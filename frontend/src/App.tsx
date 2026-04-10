import { FormEvent, startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Batch, getResults, processBatch, uploadReference, uploadStudents } from "./api";

const DRAWING_TYPES = ["orthographic", "isometric", "sectional"];

type Phase = "idle" | "uploading" | "processing" | "ready";

export default function App() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [drawingType, setDrawingType] = useState("orthographic");
  const [referenceName, setReferenceName] = useState("Machine Bracket Reference");
  const [referenceFile, setReferenceFile] = useState<File | null>(null);
  const [studentFiles, setStudentFiles] = useState<FileList | null>(null);
  const [referenceId, setReferenceId] = useState<number | null>(null);
  const [activeBatchId, setActiveBatchId] = useState<number | null>(null);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [message, setMessage] = useState("Upload a reference sheet and a student batch to begin evaluation.");
  const deferredBatches = useDeferredValue(batches);

  useEffect(() => {
    let mounted = true;
    const poll = async () => {
      const data = await getResults();
      if (!mounted) {
        return;
      }
      startTransition(() => {
        setBatches(data.batches);
        const current = activeBatchId ? data.batches.find((batch) => batch.id === activeBatchId) : data.batches[0];
        if (current && current.status === "completed") {
          setPhase("ready");
          setMessage(`Batch ${current.id} completed. ${current.processed_files}/${current.total_files} drawings evaluated.`);
        }
      });
    };
    poll().catch(() => undefined);
    const timer = window.setInterval(() => {
      poll().catch(() => undefined);
    }, 4000);
    return () => {
      mounted = false;
      window.clearInterval(timer);
    };
  }, [activeBatchId]);

  const currentBatch = useMemo(
    () => deferredBatches.find((batch) => batch.id === activeBatchId) ?? deferredBatches[0],
    [activeBatchId, deferredBatches]
  );

  const chartData = useMemo(
    () =>
      (currentBatch?.submissions ?? [])
        .filter((submission) => submission.score !== null)
        .map((submission) => ({ name: submission.student_id, score: submission.score ?? 0 })),
    [currentBatch]
  );

  async function handleUploadReference(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!referenceFile) {
      setMessage("Choose a reference drawing first.");
      return;
    }
    setPhase("uploading");
    const formData = new FormData();
    formData.append("file", referenceFile);
    formData.append("name", referenceName);
    formData.append("drawing_type", drawingType);
    const response = await uploadReference(formData);
    setReferenceId(response.id);
    setPhase("idle");
    setMessage(`Reference drawing saved as ID ${response.id}.`);
  }

  async function handleUploadStudents(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!referenceId || !studentFiles?.length) {
      setMessage("Upload a reference and choose at least one student file.");
      return;
    }
    setPhase("uploading");
    const formData = new FormData();
    formData.append("reference_id", String(referenceId));
    formData.append("drawing_type", drawingType);
    Array.from(studentFiles).forEach((file) => formData.append("files", file));
    const batch = await uploadStudents(formData);
    setActiveBatchId(batch.id);
    setPhase("idle");
    setMessage(`Batch ${batch.id} uploaded with ${batch.total_files} student drawings.`);
  }

  async function handleProcess() {
    if (!activeBatchId) {
      setMessage("Upload a student batch first.");
      return;
    }
    setPhase("processing");
    await processBatch(activeBatchId);
    setMessage(`Batch ${activeBatchId} is being processed. Progress updates will refresh automatically.`);
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">AI Engineering Drawing Evaluation System</p>
          <h1>Evaluate large engineering drawing batches with geometric rigor.</h1>
          <p className="hero-text">
            Upload a reference answer sheet, ingest 100 to 1000 student drawings, score them using line and shape
            analysis, then review rich feedback and exports from a single professor dashboard.
          </p>
          <div className="hero-status">
            <span>{message}</span>
            <strong className={`phase phase-${phase}`}>{phase}</strong>
          </div>
        </div>
        <div className="hero-grid" aria-hidden="true">
          <div className="grid-line" />
          <div className="grid-line" />
          <div className="grid-line" />
          <div className="grid-diagonal" />
        </div>
      </header>

      <main className="workspace">
        <section className="control-panel">
          <div>
            <p className="section-label">Setup</p>
            <h2>Reference and batch intake</h2>
          </div>
          <div className="controls">
            <label>
              Drawing type
              <select value={drawingType} onChange={(event) => setDrawingType(event.target.value)}>
                {DRAWING_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </label>

            <form className="upload-form" onSubmit={(event) => void handleUploadReference(event)}>
              <label>
                Reference title
                <input value={referenceName} onChange={(event) => setReferenceName(event.target.value)} />
              </label>
              <label>
                Reference file
                <input type="file" accept=".png,.jpg,.jpeg,.pdf" onChange={(event) => setReferenceFile(event.target.files?.[0] ?? null)} />
              </label>
              <button type="submit">Upload Reference</button>
            </form>

            <form className="upload-form" onSubmit={(event) => void handleUploadStudents(event)}>
              <label>
                Student drawings
                <input type="file" multiple accept=".png,.jpg,.jpeg,.pdf" onChange={(event) => setStudentFiles(event.target.files)} />
              </label>
              <button type="submit">Upload Student Batch</button>
            </form>

            <button className="accent-button" onClick={() => void handleProcess()}>
              Start Evaluation
            </button>
          </div>
        </section>

        <section className="results-grid">
          <article className="metric-panel">
            <p className="section-label">Progress</p>
            <h3>Batch status</h3>
            <div className="metric-row">
              <span>Processed</span>
              <strong>
                {currentBatch?.processed_files ?? 0}/{currentBatch?.total_files ?? 0}
              </strong>
            </div>
            <div className="metric-row">
              <span>Status</span>
              <strong>{currentBatch?.status ?? "waiting"}</strong>
            </div>
            <div className="metric-row">
              <span>Average</span>
              <strong>{currentBatch?.summary_json?.average_score ?? "-"}</strong>
            </div>
            <div className="metric-row">
              <span>Failed</span>
              <strong>{currentBatch?.summary_json?.failed ?? 0}</strong>
            </div>
            {currentBatch?.summary_json?.export_path ? (
              <a className="export-link" href={String(currentBatch.summary_json.export_path)} target="_blank" rel="noreferrer">
                Download Excel Export
              </a>
            ) : null}
            {currentBatch?.summary_json?.csv_export_path ? (
              <a className="export-link" href={String(currentBatch.summary_json.csv_export_path)} target="_blank" rel="noreferrer">
                Download CSV Export
              </a>
            ) : null}
          </article>

          <article className="chart-panel">
            <p className="section-label">Score distribution</p>
            <h3>Student marks</h3>
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="2 8" vertical={false} stroke="rgba(255,255,255,0.12)" />
                  <XAxis dataKey="name" stroke="#d6d2c4" tick={{ fontSize: 12 }} />
                  <YAxis stroke="#d6d2c4" />
                  <Tooltip />
                  <Bar dataKey="score" fill="#f3b33d" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </article>
        </section>

        <section className="table-panel">
          <div>
            <p className="section-label">Evaluated submissions</p>
            <h2>Detailed feedback</h2>
          </div>
          <div className="submission-list">
            {(currentBatch?.submissions ?? []).map((submission) => (
              <article className="submission-card" key={submission.id}>
                <div className="submission-head">
                  <div>
                    <h3>{submission.student_id}</h3>
                    <p>{submission.original_filename}</p>
                  </div>
                  <strong>{submission.score ?? "-"}</strong>
                </div>
                <p className="submission-status">{submission.status}</p>
                {submission.result_json?.comparison?.component_scores ? (
                  <p className="component-line">
                    Angles {submission.result_json.comparison.component_scores.angles?.toFixed(1)} | Proportions{" "}
                    {submission.result_json.comparison.component_scores.proportions?.toFixed(1)} | Alignment{" "}
                    {submission.result_json.comparison.component_scores.alignment?.toFixed(1)} | Completeness{" "}
                    {submission.result_json.comparison.component_scores.completeness?.toFixed(1)}
                  </p>
                ) : null}
                <pre>{submission.feedback_text ?? "Awaiting evaluation..."}</pre>
                {submission.preview_path ? <img src={submission.preview_path} alt={`${submission.student_id} feedback`} /> : null}
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
