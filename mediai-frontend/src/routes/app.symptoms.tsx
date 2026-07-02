import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, Stethoscope, Brain } from "lucide-react";
import { AppShell, SectionCard } from "@/components/app-shell";
import { api, extractError } from "@/lib/api";

export const Route = createFileRoute("/app/symptoms")({
  head: () => ({ meta: [{ title: "Symptom Checker · MediAI" }] }),
  component: SymptomsPage,
});

type PossibleDisease = {
  disease: string;
  confidence: number;
  level: string;
  category?: string;
  specialist: string;
  severity?: string;
  matched_symptoms?: string[];
};

type SymptomResponse = {
  symptoms: string[];
  possible_diseases: PossibleDisease[];
  severity: string;
  emergency: boolean;
  recommended_specialist: string;
  reasoning: string[];
  disclaimer: string;
};

function levelTone(level: string) {
  const l = level.toLowerCase();
  if (l.includes("high") || l.includes("emergency") || l.includes("severe")) return "destructive";
  if (l.includes("moderate") || l.includes("medium")) return "warning";
  return "success";
}

function SymptomsPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<SymptomResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function analyze() {
    if (text.trim().length < 3) {
      setError("Please describe your symptoms in at least a short sentence.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const { data } = await api.post<SymptomResponse>("/symptom-checker", { text });
      setResult(data);
    } catch (err) {
      setError(extractError(err, "Failed to analyze symptoms"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell title="Symptom Checker" subtitle="Structured triage with differential reasoning">
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-4">
        <div className="space-y-4">
          <SectionCard title="Describe your symptoms" hint="Free text — fever, cough, body aches…">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={5}
              placeholder="e.g. For the last 3 days I have a high fever, dry cough, and body pain."
              className="w-full rounded-md border border-border bg-card p-3 text-sm outline-none focus:border-secondary focus:ring-2 focus:ring-secondary/20 transition resize-none"
            />
            {error && <div className="mt-2 text-sm text-destructive">{error}</div>}
            <button
              onClick={analyze}
              disabled={loading || text.trim().length < 3}
              className="mt-5 w-full h-11 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition disabled:opacity-50 inline-flex items-center justify-center gap-2"
            >
              <Stethoscope className="h-4 w-4" /> {loading ? "Analyzing…" : "Analyze symptoms"}
            </button>
          </SectionCard>

          {result && result.emergency && (
            <div className="surface-card border-destructive/40 bg-destructive/5 p-4 flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-destructive mt-0.5" />
              <div>
                <div className="font-medium text-destructive">Possible emergency detected</div>
                <p className="text-sm text-muted-foreground mt-1">Seek immediate medical attention or call your local emergency number.</p>
              </div>
            </div>
          )}

          {result && (
            <SectionCard title="Differential" hint={`Severity: ${result.severity} · See ${result.recommended_specialist}`}>
              {result.possible_diseases.length === 0 ? (
                <div className="text-sm text-muted-foreground">No matching conditions identified.</div>
              ) : (
                <div className="space-y-3">
                  {result.possible_diseases.map((r, i) => {
                    const tone = levelTone(r.level);
                    return (
                      <motion.div key={`${r.disease}-${i}`} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }} className="rounded-lg border border-border p-4 hover:bg-muted/30 transition">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium">{r.disease}</div>
                            <div className="text-xs text-muted-foreground mt-0.5">See {r.specialist}</div>
                          </div>
                          <div className="text-right">
                            <div className="font-mono text-lg">{Math.round(r.confidence)}%</div>
                            <span className="chip" style={{ color: `var(--${tone})`, borderColor: `color-mix(in oklab, var(--${tone}) 35%, transparent)` }}>{r.level}</span>
                          </div>
                        </div>
                        <div className="mt-3 h-1.5 rounded-full bg-muted overflow-hidden">
                          <motion.div initial={{ width: 0 }} animate={{ width: `${r.confidence}%` }} transition={{ duration: 0.6, delay: 0.1 + i * 0.06 }} className="h-full" style={{ background: `var(--${tone})` }} />
                        </div>
                        {r.matched_symptoms && r.matched_symptoms.length > 0 && (
                          <div className="mt-3 flex items-start gap-2 text-sm text-muted-foreground">
                            <Brain className="h-4 w-4 text-accent shrink-0 mt-0.5" /> Matched: {r.matched_symptoms.join(", ")}
                          </div>
                        )}
                      </motion.div>
                    );
                  })}
                </div>
              )}
              {result.reasoning.length > 0 && (
                <ul className="mt-4 space-y-1 text-xs text-muted-foreground">
                  {result.reasoning.map((r, i) => <li key={i}>· {r}</li>)}
                </ul>
              )}
              <p className="mt-4 text-xs text-muted-foreground italic">{result.disclaimer}</p>
            </SectionCard>
          )}
        </div>

        <div className="space-y-4">
          <div className="surface-card p-4">
            <div className="flex items-start gap-2 text-sm">
              <AlertTriangle className="h-4 w-4 text-warning shrink-0 mt-0.5" />
              <div>
                <div className="font-medium">Emergency signals</div>
                <p className="text-muted-foreground mt-1 text-xs leading-relaxed">If you experience chest pain radiating to the arm, sudden weakness on one side, severe shortness of breath, or loss of consciousness — call emergency services immediately.</p>
              </div>
            </div>
          </div>
          <SectionCard title="Detected symptoms">
            {!result || result.symptoms.length === 0 ? (
              <div className="text-xs text-muted-foreground">No symptoms detected yet. Run an analysis to see extracted terms.</div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {result.symptoms.map((s) => <span key={s} className="chip bg-secondary/10 border-secondary/30 text-secondary">{s}</span>)}
              </div>
            )}
          </SectionCard>
        </div>
      </div>
    </AppShell>
  );
}
