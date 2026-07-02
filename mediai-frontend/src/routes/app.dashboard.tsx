import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FileText, Stethoscope, AlertTriangle, CalendarClock } from "lucide-react";
import { AppShell, SectionCard } from "@/components/app-shell";
import { Skeleton } from "@/components/ui/skeleton";
import { api, extractError } from "@/lib/api";

export const Route = createFileRoute("/app/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard · MediAI" }] }),
  component: Dashboard,
});

type Summary = {
  total_reports: number;
  total_symptom_checks: number;
  high_risk_reports: number;
  last_report_date?: string | null;
};

type ReportEntry = { id: number; report_type: string; report_summary: string; risk_assessment: { severity: string }[]; created_at: string };
type ChatEntry = { id: number; question: string; created_at: string };
type SymptomEntry = { id: number; severity: string; emergency_status: boolean; created_at: string };

function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [reports, setReports] = useState<ReportEntry[]>([]);
  const [chats, setChats] = useState<ChatEntry[]>([]);
  const [symptoms, setSymptoms] = useState<SymptomEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.allSettled([
      api.get<Summary>("/dashboard/summary"),
      api.get<ReportEntry[]>("/history/reports"),
      api.get<ChatEntry[]>("/history/chat"),
      api.get<SymptomEntry[]>("/history/symptoms"),
    ])
      .then(([s, r, c, sym]) => {
        if (s.status === "fulfilled") setSummary(s.value.data);
        else setError(extractError(s.reason, "Failed to load dashboard"));
        if (r.status === "fulfilled") setReports(r.value.data);
        if (c.status === "fulfilled") setChats(c.value.data);
        if (sym.status === "fulfilled") setSymptoms(sym.value.data);
      })
      .finally(() => setLoading(false));
  }, []);

  const stats = [
    { label: "Total Reports", value: summary?.total_reports ?? 0, icon: FileText },
    { label: "Symptom Checks", value: summary?.total_symptom_checks ?? 0, icon: Stethoscope },
    { label: "High-risk Reports", value: summary?.high_risk_reports ?? 0, icon: AlertTriangle },
    {
      label: "Last Report",
      value: summary?.last_report_date ? new Date(summary.last_report_date).toLocaleDateString() : "—",
      icon: CalendarClock,
    },
  ];

  return (
    <AppShell title="Dashboard" subtitle="Your medical activity at a glance">
      {error && <div className="mb-4 text-sm text-destructive">{error}</div>}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {stats.map((s, i) => (
          <motion.div key={s.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }} className="surface-card p-5">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-xs uppercase tracking-wider text-muted-foreground">{s.label}</div>
                {loading ? (
                  <Skeleton className="h-8 w-20 mt-2" />
                ) : (
                  <div className="mt-2 text-3xl font-semibold tracking-tight font-mono">{s.value}</div>
                )}
              </div>
              <span className="h-9 w-9 rounded-lg bg-muted flex items-center justify-center text-muted-foreground"><s.icon className="h-4 w-4" /></span>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="mt-6 grid grid-cols-1 xl:grid-cols-2 gap-4">
        <SectionCard title="Recent reports">
          {loading ? (
            <Skeleton className="h-40 w-full" />
          ) : reports.length === 0 ? (
            <div className="text-sm text-muted-foreground">No reports analyzed yet.</div>
          ) : (
            <ul className="divide-y divide-border text-sm">
              {reports.slice(0, 6).map((r) => {
                const sev = r.risk_assessment.find((x) => x.severity === "High")?.severity
                  ?? r.risk_assessment.find((x) => x.severity === "Moderate")?.severity
                  ?? "Low";
                const tone = sev === "High" ? "destructive" : sev === "Moderate" ? "warning" : "success";
                return (
                  <li key={r.id} className="py-3 flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="font-medium truncate">{r.report_type}</div>
                      <div className="text-xs text-muted-foreground truncate">{r.report_summary}</div>
                    </div>
                    <span className="chip" style={{ color: `var(--${tone})`, borderColor: `color-mix(in oklab, var(--${tone}) 35%, transparent)` }}>{sev}</span>
                  </li>
                );
              })}
            </ul>
          )}
        </SectionCard>

        <SectionCard title="Recent activity">
          {loading ? (
            <Skeleton className="h-40 w-full" />
          ) : (
            <ul className="divide-y divide-border text-sm">
              {[...chats.slice(0, 3).map((c) => ({ t: "Chat", title: c.question, at: c.created_at })),
                ...symptoms.slice(0, 3).map((s) => ({ t: "Symptoms", title: `Severity: ${s.severity}${s.emergency_status ? " · Emergency" : ""}`, at: s.created_at })),
              ]
                .sort((a, b) => +new Date(b.at) - +new Date(a.at))
                .slice(0, 6)
                .map((row, i) => (
                  <li key={i} className="py-3 flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-xs uppercase tracking-wider text-muted-foreground">{row.t}</div>
                      <div className="text-sm truncate">{row.title}</div>
                    </div>
                    <span className="text-xs text-muted-foreground font-mono">{new Date(row.at).toLocaleDateString()}</span>
                  </li>
                ))}
              {chats.length === 0 && symptoms.length === 0 && (
                <li className="py-3 text-sm text-muted-foreground">No activity yet — start a chat or symptom check.</li>
              )}
            </ul>
          )}
        </SectionCard>
      </div>
    </AppShell>
  );
}
