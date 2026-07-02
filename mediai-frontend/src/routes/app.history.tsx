import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FileText, MessagesSquare, Stethoscope } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Skeleton } from "@/components/ui/skeleton";
import { api, extractError } from "@/lib/api";

export const Route = createFileRoute("/app/history")({
  head: () => ({ meta: [{ title: "Medical History · MediAI" }] }),
  component: HistoryPage,
});

type Item = {
  date: string;
  icon: typeof FileText;
  type: string;
  title: string;
  note: string;
  tone: string;
};

function HistoryPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.allSettled([
      api.get("/history/chat"),
      api.get("/history/reports"),
      api.get("/history/symptoms"),
    ])
      .then(([c, r, s]) => {
        const out: Item[] = [];
        if (c.status === "fulfilled") {
          for (const x of c.value.data) {
            out.push({
              date: x.created_at,
              icon: MessagesSquare,
              type: "Chat",
              title: x.question,
              note: (x.response ?? "").slice(0, 140),
              tone: "secondary",
            });
          }
        }
        if (r.status === "fulfilled") {
          for (const x of r.value.data) {
            const sev = x.risk_assessment?.find((a: any) => a.severity === "High")?.severity
              ?? x.risk_assessment?.find((a: any) => a.severity === "Moderate")?.severity
              ?? "Low";
            const tone = sev === "High" ? "destructive" : sev === "Moderate" ? "warning" : "success";
            out.push({
              date: x.created_at,
              icon: FileText,
              type: "Report",
              title: x.report_type,
              note: (x.report_summary ?? "").slice(0, 140),
              tone,
            });
          }
        }
        if (s.status === "fulfilled") {
          for (const x of s.value.data) {
            out.push({
              date: x.created_at,
              icon: Stethoscope,
              type: "Symptoms",
              title: x.symptoms?.slice(0, 4).join(", ") || "Symptom check",
              note: `Severity: ${x.severity}${x.emergency_status ? " · Emergency" : ""}`,
              tone: x.emergency_status ? "destructive" : x.severity === "Severe" ? "destructive" : x.severity === "Moderate" ? "warning" : "accent",
            });
          }
        }
        const failed = [c, r, s].find((p) => p.status === "rejected") as PromiseRejectedResult | undefined;
        if (failed && out.length === 0) setError(extractError(failed.reason, "Failed to load history"));
        out.sort((a, b) => +new Date(b.date) - +new Date(a.date));
        setItems(out);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppShell title="Medical History" subtitle="Longitudinal timeline of every interaction and finding">
      <div className="surface-card p-6 max-w-4xl">
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        ) : error ? (
          <div className="text-sm text-destructive">{error}</div>
        ) : items.length === 0 ? (
          <div className="text-sm text-muted-foreground">No history yet. Your chats, reports and symptom checks will appear here.</div>
        ) : (
          <div className="relative pl-6">
            <div className="absolute left-2 top-2 bottom-2 w-px bg-border" />
            <div className="space-y-6">
              {items.map((it, i) => (
                <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }} className="relative">
                  <span className="absolute -left-[18px] top-1.5 h-3 w-3 rounded-full ring-4 ring-card" style={{ background: `var(--${it.tone})` }} />
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="font-mono">{new Date(it.date).toLocaleString()}</span>
                    <span className="chip"><it.icon className="h-3 w-3" /> {it.type}</span>
                  </div>
                  <div className="mt-1 font-medium">{it.title}</div>
                  <div className="text-sm text-muted-foreground mt-0.5">{it.note}</div>
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
