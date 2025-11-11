from __future__ import annotations

import io
from dataclasses import dataclass
import re
from pathlib import Path
from typing import Iterable

import pandas as pd
import pdfplumber
import pytesseract
import unicodedata

from pdf2image import convert_from_bytes
from PIL import Image
from pytesseract import Output, TesseractNotFoundError

from app.utils.image_ops import detect_table_column_centers, load_image


@dataclass
class ExtractionResult:
    dataframe: pd.DataFrame
    notes: list[str]


class DocumentProcessor:
    """
    Convert PDFs or screenshots into structured CSV-friendly data frames.
    """

    HEADER_ALIASES = {
        "fecha": "Fecha",
        "numerodetransaccion": "Numero de Transaccion",
        "numerodetransaccionoficina": "Numero de Transaccion",
        "oficina": "Oficina",
        "descripcion": "Descripcion",
        "egresos": "Egresos",
        "ingresos": "Ingresos",
        "saldo": "Saldo",
    }

    def __init__(
        self,
        tesseract_config: str = "--psm 6 --oem 3 -c preserve_interword_spaces=1",
        tesseract_lang: str = "eng+spa",
    ):
        self.tesseract_config = tesseract_config
        self.tesseract_lang = tesseract_lang

    def process(self, filename: str, content: bytes) -> ExtractionResult:
        notes: list[str] = []
        suffix = Path(filename).suffix.lower()
        try:
            if suffix == ".pdf" or content.startswith(b"%PDF"):
                frames, pdf_notes = self._process_pdf(content)
                notes.extend(pdf_notes)
            else:
                frames = [self._ocr_dataframe(load_image(content))]
        except TesseractNotFoundError as exc:
            notes.append(
                "Tesseract OCR engine is not installed or not on PATH. "
                "Install it and try again."
            )
            return ExtractionResult(dataframe=pd.DataFrame(), notes=notes + [str(exc)])
        frames = [df for df in frames if not df.empty]
        if not frames:
            empty = pd.DataFrame()
            return ExtractionResult(dataframe=empty, notes=notes + ["No text detected."])
        dataframe = pd.concat(frames, ignore_index=True)
        return ExtractionResult(dataframe=dataframe, notes=notes)

    def _process_pdf(self, content: bytes) -> tuple[list[pd.DataFrame], list[str]]:
        notes: list[str] = []
        frames: list[pd.DataFrame] = []
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        cleaned = self._clean_table_rows(table)
                        if cleaned:
                            frames.append(
                                self._rows_to_frame(
                                    cleaned,
                                    normalize_headers=False,
                                    drop_noise_rows=False,
                                )
                            )
                if frames:
                    notes.append("Structured data extracted directly from PDF tables.")
                    return frames, notes
        except Exception as exc:  # pragma: no cover - defensive
            notes.append(f"pdfplumber failed, falling back to OCR ({exc}).")

        try:
            pil_images = convert_from_bytes(content, dpi=300)
        except Exception as exc:  # pragma: no cover
            notes.append(
                "Failed to rasterize PDF for OCR. Install Poppler (provides pdftoppm) "
                f"and retry. Details: {exc}"
            )
            return frames, notes

        for idx, image in enumerate(pil_images, start=1):
            notes.append(f"OCR applied to PDF page {idx}.")
            frames.append(self._ocr_dataframe(image))
        return frames, notes

    def _ocr_dataframe(self, image: Image.Image) -> pd.DataFrame:
        working_image = image
        width, height = working_image.size
        if width < 2000:
            scale = 2000 / width
            new_size = (int(width * scale), int(height * scale))
            working_image = working_image.resize(new_size, Image.BICUBIC)

        ocr_df = pytesseract.image_to_data(
            working_image,
            lang=self.tesseract_lang,
            config=self.tesseract_config,
            output_type=Output.DATAFRAME,
        )
        if ocr_df.empty:
            return pd.DataFrame()

        ocr_df = ocr_df.dropna(subset=["text"])
        ocr_df = ocr_df[ocr_df["text"].str.strip() != ""]
        if ocr_df.empty:
            return pd.DataFrame()

        ocr_df["conf"] = pd.to_numeric(ocr_df["conf"], errors="coerce")
        ocr_df = ocr_df[ocr_df["conf"] > 40]
        if ocr_df.empty:
            return pd.DataFrame()

        column_centers = detect_table_column_centers(working_image)
        if not column_centers:
            column_centers = self._infer_column_centers(ocr_df)

        rows = self._rows_from_tokens(ocr_df, column_centers)
        if not rows:
            return pd.DataFrame()
        return self._rows_to_frame(rows)

    @staticmethod
    def _clean_table_rows(table: Iterable[Iterable[str]]) -> list[list[str]]:
        cleaned_rows: list[list[str]] = []
        for row in table:
            cleaned_row = [cell.strip() if isinstance(cell, str) else "" for cell in row]
            if any(cell for cell in cleaned_row):
                cleaned_rows.append(cleaned_row)
        return cleaned_rows

    @staticmethod
    def _rows_to_frame(
        rows: list[list[str]],
        *,
        normalize_headers: bool = True,
        drop_noise_rows: bool = True,
    ) -> pd.DataFrame:
        max_len = max(len(row) for row in rows)
        normalized = [row + [""] * (max_len - len(row)) for row in rows]
        df = pd.DataFrame(normalized, columns=[f"Column {idx+1}" for idx in range(max_len)])

        if drop_noise_rows:
            df = df[
                df.apply(lambda row: DocumentProcessor._is_meaningful_row(row), axis=1)
            ].reset_index(drop=True)
            if df.empty:
                return df

        if normalize_headers and not df.empty:
            header_row = df.iloc[0]
            alpha_cells = 0
            for cell in header_row:
                letters = sum(ch.isalpha() for ch in cell)
                digits = sum(ch.isdigit() for ch in cell)
                if letters >= digits and letters >= 3:
                    alpha_cells += 1
            if alpha_cells >= max(2, df.shape[1] // 2):
                new_columns = []
                for idx, cell in enumerate(header_row):
                    cleaned = DocumentProcessor._clean_header(cell)
                    new_columns.append(cleaned or f"Column {idx+1}")
                df = df.iloc[1:].reset_index(drop=True)
                df.columns = new_columns
        return df

    @staticmethod
    def _is_meaningful_row(row: pd.Series) -> bool:
        texts = [cell.strip() for cell in row if isinstance(cell, str) and cell.strip()]
        if not texts:
            return False
        if len(texts) >= 2:
            return True
        cell = texts[0]
        return any(ch.isdigit() for ch in cell)

    @staticmethod
    def _clean_header(cell: str) -> str:
        normalized = unicodedata.normalize("NFKD", cell).encode("ascii", "ignore").decode()
        normalized = re.sub(r"[^A-Za-z]+", " ", normalized).strip()
        if not normalized:
            return ""
        compact = normalized.replace(" ", "").lower()
        for alias, canonical in DocumentProcessor.HEADER_ALIASES.items():
            if alias in compact:
                return canonical

        tokens = normalized.lower().split()
        if "fecha" in tokens:
            return "Fecha"
        if "transacci" in compact or "transaccion" in tokens:
            return "Numero de Transaccion"
        if "descripcion" in tokens or "descripcien" in tokens:
            return "Descripcion"
        return normalized.title()

    @staticmethod
    def _infer_column_centers(ocr_df: pd.DataFrame) -> list[float]:
        """
        Fallback heuristic when we cannot detect table lines.
        We analyze the first chunk of lines and cluster words by their left edge.
        """
        if ocr_df.empty:
            return []

        header_threshold = ocr_df["top"].quantile(0.2)
        header_df = ocr_df[ocr_df["top"] <= header_threshold]
        candidate_df = header_df if not header_df.empty else ocr_df
        x_values = sorted(candidate_df["left"].tolist())
        if not x_values:
            return []

        width_median = candidate_df["width"].median()
        if pd.isna(width_median) or width_median <= 0:
            width_median = 40.0

        merge_threshold = max(20.0, float(width_median))
        anchors: list[float] = []
        for value in x_values:
            if not anchors or value - anchors[-1] > merge_threshold:
                anchors.append(value)

        if len(anchors) < 2:
            min_left = float(ocr_df["left"].min())
            max_right = float((ocr_df["left"] + ocr_df["width"]).max())
            anchors = [min_left, (min_left + max_right) / 2, max_right]

        # Convert anchor (left edges) to centers by adding an estimated cell width.
        estimated_width = max(30.0, float(width_median))
        return [anchor + estimated_width / 2 for anchor in anchors]

    @staticmethod
    def _rows_from_tokens(ocr_df: pd.DataFrame, column_centers: list[float]) -> list[list[str]]:
        column_centers = sorted(column_centers)
        column_count = len(column_centers)
        if column_count == 0:
            return []

        rows: list[list[str]] = []
        group_cols = ["block_num", "par_num", "line_num"]
        for _, line_df in ocr_df.groupby(group_cols):
            sorted_line = line_df.sort_values(by="left")
            row_cells = [""] * column_count
            for _, token in sorted_line.iterrows():
                col_idx = DocumentProcessor._nearest_column(token, column_centers)
                if col_idx is None:
                    continue
                text = token["text"].strip()
                if not text:
                    continue
                if row_cells[col_idx]:
                    row_cells[col_idx] = f"{row_cells[col_idx]} {text}"
                else:
                    row_cells[col_idx] = text
            if any(row_cells):
                rows.append(row_cells)
        return rows

    @staticmethod
    def _nearest_column(token: pd.Series, column_centers: list[float]) -> int | None:
        token_center = float(token["left"]) + float(token["width"]) / 2
        distances = [abs(token_center - center) for center in column_centers]
        if not distances:
            return None
        col_idx = distances.index(min(distances))
        return col_idx
