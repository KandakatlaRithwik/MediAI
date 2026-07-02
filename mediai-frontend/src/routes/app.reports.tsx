import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { motion } from "framer-motion";
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, X, ScanLine } from "lucide-react";
import { AppShell, SectionCard } from "@/components/app-shell";
import { api, extractError } from "@/lib/api";

export const Route = createFileRoute("/app/reports")({
  head: () => ({ meta: [{ title: "Report Analyzer · MediAI" }] }),
  component: ReportsPage,
});

type ReportParameter = {
  name: string;
  value: number;
  unit?: string | null;
  status: "LOW" | "NORMAL" | "HIGH";
  reference_min?: number | null;
  reference_max?: number | null;
};
type RiskAssessment = { risk: string; severity: string; based_on: string[] };
type AnalysisResponse = {
  report_type: string;
  parameters: ReportParameter[];
  abnormal_parameters: string[];
  risk_assessment: RiskAssessment[];
  ai_summary: string;
  disclaimer: string;
  ocr_text?: string;
  ocr_confidence?: number;
};

function tone(s: ReportParameter["status"]) {
  return s === "NORMAL" ? "success" : s === "HIGH" ? "destructive" : "warning";
}

const IMAGE_EXT = [".jpg", ".jpeg", ".png"];

function isImage(name: string) {
  const lower = name.toLowerCase();
  return IMAGE_EXT.some((e) => lower.endsWith(e));
}

function ReportsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  function handleFile(f: File | null) {
    setFile(f);
    setResult(null);
    setError(null);
    setProgress(0);
  }

  async function analyze() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setProgress(0);
    const useOcr = isImage(file.name);
    const endpoint = useOcr ? "/analyze-image-report" : "/analyze-report";
    const form = new FormData();
    form.append("file", file);
    try {
      const { data } = await api.post<AnalysisResponse>(endpoint, form, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (e.total) setProgress(Math.round((e.loaded / e.total) * 100));
        },
      });
      setResult(data);
    } catch (err) {
      setError(extractError(err, "Failed to analyze report"));
    } finally {
      setLoading(false);
    }
  }

  const highestSeverity = result?.risk_assessment.reduce((acc, r) => {
    const order = { Low: 1, Moderate: 2, High: 3 } as Record<string, number>;
    return (order[r.severity] ?? 0) > (order[acc] ?? 0) ? r.severity : acc;
  }, "Low" as string);

  return (
    <AppShell title="Medical Report Analyzer" subtitle="Drag-and-drop interpretation of labs, imaging summaries and clinical notes">
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-4">
        <div className="space-y-4">
          <SectionCard>
            <label
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files?.[0] ?? null); }}
              className={`flex flex-col items-center justify-center text-center rounded-xl border-2 border-dashed transition cursor-pointer py-14 px-6 ${dragging ? "border-secondary bg-secondary/5" : "border-border hover:border-muted-foreground/40"}`}
            >
              <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center"><UploadCloud className="h-5 w-5" /></div>
              <div className="mt-4 text-base font-medium">Drop a report to begin</div>
              <p className="mt-1 text-sm text-muted-foreground">PDF, TXT, PNG or JPG · up to 10MB</p>
              <span className="mt-4 chip">Browse files</span>
              <input type="file" accept=".pdf,.txt,image/*" className="hidden" onChange={(e) => handleFile(e.target.files?.[0] ?? null)} />
            </label>
            {file && (
              <div className="mt-4 rounded-lg border border-border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-md bg-muted flex items-center justify-center">
                      {isImage(file.name) ? <ScanLine className="h-4 w-4" /> : <FileText className="h-4 w-4" />}
                    </div>
                    <div>
                      <div className="text-sm font-medium">{file.name}</div>
                      <div className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB {isImage(file.name) && "· OCR pipeline"}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => handleFile(null)} className="h-9 w-9 rounded-md border border-border hover:bg-muted transition" aria-label="Remove"><X className="h-4 w-4 mx-auto" /></button>
                    <button onClick={analyze} disabled={loading} className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition disabled:opacity-60">{loading ? "Analyzing…" : "Analyze report"}</button>
                  </div>
                </div>
                {loading && (
                  <div className="mt-3 h-1.5 rounded-full bg-muted overflow-hidden">
                    <div className="h-full bg-secondary transition-all" style={{ width: `${progress}%` }} />
                  </div>
                )}
                {error && <div className="mt-3 text-sm text-destructive">{error}</div>}
              </div>
            )}
          </SectionCard>

          {result && (
            <SectionCard title="Detected parameters" hint={result.report_type}>
              {result.parameters.length === 0 ? (
                <div className="text-sm text-muted-foreground">No lab parameters detected in this report.</div>
              ) : (
                <div className="overflow-x-auto -mx-5">
                  <table className="w-full text-sm">
                    <thead className="text-xs text-muted-foreground uppercase tracking-wider">
                      <tr className="border-b border-border">
                        <th className="text-left font-medium px-5 py-2">Parameter</th>
                        <th className="text-left font-medium py-2">Value</th>
                        <th className="text-left font-medium py-2">Reference</th>
                        <th className="text-right font-medium px-5 py-2">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.parameters.map((p, i) => (
                        <motion.tr key={`${p.name}-${i}`} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }} className="border-b border-border last:border-0 hover:bg-muted/30 transition">
                          <td className="px-5 py-3">{p.name}</td>
                          <td className="py-3 font-mono">{p.value} <span className="text-muted-foreground text-xs">{p.unit ?? ""}</span></td>
                          <td className="py-3 text-muted-foreground font-mono text-xs">{p.reference_min ?? "—"}–{p.reference_max ?? "—"}</td>
                          <td className="px-5 py-3 text-right">
                            <span className="chip" style={{ color: `var(--${tone(p.status)})`, borderColor: `color-mix(in oklab, var(--${tone(p.status)}) 35%, transparent)` }}>
                              {p.status === "NORMAL" ? <><CheckCircle2 className="h-3 w-3" /> Normal</> : <><AlertTriangle className="h-3 w-3" /> {p.status === "HIGH" ? "Elevated" : "Low"}</>}
                            </span>
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </SectionCard>
          )}

          {result?.ocr_text && (
            <SectionCard title="OCR text" hint={result.ocr_confidence != null ? `${Math.round(result.ocr_confidence * 100)}% confidence` : undefined}>
              <pre className="text-xs whitespace-pre-wrap font-mono text-muted-foreground max-h-60 overflow-y-auto">{result.ocr_text}</pre>
            </SectionCard>
          )}
        </div>

        <div className="space-y-4">
          {result ? (
            <>
              <SectionCard title="Risk assessment">
                <div className="text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Overall</span>
                    <span className="chip" style={{ color: `var(--${highestSeverity === "High" ? "destructive" : highestSeverity === "Moderate" ? "warning" : "success"})`, borderColor: `color-mix(in oklab, var(--${highestSeverity === "High" ? "destructive" : highestSeverity === "Moderate" ? "warning" : "success"}) 35%, transparent)` }}>{highestSeverity ?? "Low"}</span>
                  </div>
                  <ul className="mt-4 space-y-2 text-xs text-muted-foreground">
                    {result.risk_assessment.length === 0 && <li>· No notable risks identified.</li>}
                    {result.risk_assessment.map((r, i) => (
                      <li key={i}>· {r.risk} ({r.severity}) — {r.based_on.join(", ")}</li>
                    ))}
                  </ul>
                </div>
              </SectionCard>
              <SectionCard title="AI summary">
                <p className="text-sm text-foreground/80 leading-relaxed whitespace-pre-wrap">{result.ai_summary}</p>
                <p className="mt-3 text-[11px] text-muted-foreground italic">{result.disclaimer}</p>
              </SectionCard>
            </>
          ) : (
            <SectionCard title="How it works">
              <ol className="text-sm text-muted-foreground space-y-2 list-decimal pl-4">
                <li>Upload a PDF, TXT, or image of a lab report.</li>
                <li>Images and scans run through the OCR pipeline.</li>
                <li>Parameters are matched against reference ranges.</li>
                <li>Risk is assessed and a plain-English summary is generated.</li>
              </ol>
            </SectionCard>
          )}
        </div>
      </div>
    </AppShell>
  );
}
