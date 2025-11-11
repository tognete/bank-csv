import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import "./App.css";

type ExtractionResponse = {
  filename: string;
  columns: string[];
  rows: string[][];
  csv: string;
  row_count: number;
  notes: string[];
};

const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000/api";

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ExtractionResponse | null>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files?.length) {
      setFile(event.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const droppedFile = event.dataTransfer.files?.[0];
    if (droppedFile) {
      setFile(droppedFile);
      setResult(null);
      setError(null);
    }
  };

  const submit = async () => {
    if (!file) {
      setError("Select a PDF or image first.");
      return;
    }
    setIsSubmitting(true);
    setError(null);
    setResult(null);
    const body = new FormData();
    body.append("file", file);

    try {
      const response = await fetch(`${API_BASE}/extract`, {
        method: "POST",
        body,
      });
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Extraction failed");
      }
      const data: ExtractionResponse = await response.json();
      if (!data.rows.length) {
        setError("No structured rows detected. Try another file.");
      }
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const csvBlobUrl = useMemo(() => {
    if (!result?.csv) return null;
    return URL.createObjectURL(
      new Blob([result.csv], { type: "text/csv;charset=utf-8" })
    );
  }, [result]);

  return (
    <div className="app">
      <header>
        <div>
          <h1>Bank CSV Extractor</h1>
          <p>Upload PDFs or screenshots and turn them into CSVs instantly.</p>
        </div>
        <div className="status">
          <span className="pill">Backend: {API_BASE}</span>
        </div>
      </header>

      <section
        className={`dropzone ${isDragging ? "dragging" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setIsDragging(false);
        }}
      >
        <label onDrop={handleDrop}>
          <input
            type="file"
            accept=".pdf,image/*"
            onChange={handleFileChange}
          />
          <div>
            <p>Drag & drop a bank statement PDF or screenshot</p>
            <p className="muted">or click to browse files</p>
            {file && <p className="selected">{file.name}</p>}
          </div>
        </label>
        <button disabled={!file || isSubmitting} onClick={submit}>
          {isSubmitting ? "Processing…" : "Convert to CSV"}
        </button>
      </section>

      {error && <p className="error">{error}</p>}

      {result && (
        <section className="results">
          <div className="result-header">
            <div>
              <h2>{result.filename}</h2>
              <p>
                {result.row_count} rows · {result.columns.length} columns
              </p>
            </div>
            <div className="actions">
              {csvBlobUrl && (
                <a download={`${result.filename}.csv`} href={csvBlobUrl}>
                  Download CSV
                </a>
              )}
            </div>
          </div>

          {!!result.notes.length && (
            <ul className="notes">
              {result.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          )}

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  {result.columns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.rows.map((row, idx) => (
                  <tr key={idx}>
                    {row.map((value, colIdx) => (
                      <td key={`${idx}-${colIdx}`}>{value}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}

export default App;
