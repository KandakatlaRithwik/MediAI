import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AppShell, SectionCard } from "@/components/app-shell";
import { ServerCog, Database, Brain, ScanLine } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { api, extractError } from "@/lib/api";

export const Route = createFileRoute("/app/admin")({
  head: () => ({ meta: [{ title: "System · MediAI" }] }),
  component: AdminPage,
});

type Component = {
  status: string;
  detail?: string;
  latency_ms?: number;
  documents_indexed?: number;
  model?: string;
};
type Health = {
  overall: string;
  version: string;
  database: Component;
  chromadb: Component;
  gemini: Component;
  ocr: Component;
};

function statusTone(s: string) {
  if (s === "healthy") return "success";
  if (s === "disabled") return "muted-foreground";
  return "destructive";
}

function AdminPage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Health>("/system/health")
      .then((r) => setHealth(r.data))
      .catch((e) => setError(extractError(e, "Could not reach system health endpoint")))
      .finally(() => setLoading(false));
  }, []);

  const rows = [
    { l: "Database", k: "database" as const, i: Database },
    { l: "Vector store", k: "chromadb" as const, i: ServerCog },
    { l: "Gemini LLM", k: "gemini" as const, i: Brain },
    { l: "OCR pipeline", k: "ocr" as const, i: ScanLine },
  ];

  return (
    <AppShell title="System Health" subtitle="Live status of platform components">
      {error && <div className="mb-4 text-sm text-destructive">{error}</div>}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {rows.map((row) => {
          const comp = health?.[row.k];
          return (
            <div key={row.l} className="surface-card p-5">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-xs uppercase tracking-wider text-muted-foreground">{row.l}</div>
                  {loading ? (
                    <Skeleton className="h-6 w-24 mt-2" />
                  ) : (
                    <div className="mt-2 text-lg font-semibold capitalize" style={{ color: `var(--${statusTone(comp?.status ?? "unhealthy")})` }}>
                      {comp?.status ?? "unknown"}
                    </div>
                  )}
                  {comp?.latency_ms != null && <div className="text-xs text-muted-foreground mt-1 font-mono">{comp.latency_ms.toFixed(1)} ms</div>}
                  {comp?.documents_indexed != null && <div className="text-xs text-muted-foreground mt-1 font-mono">{comp.documents_indexed} docs</div>}
                  {comp?.model && <div className="text-xs text-muted-foreground mt-1 font-mono truncate">{comp.model}</div>}
                </div>
                <span className="h-9 w-9 rounded-lg bg-muted flex items-center justify-center"><row.i className="h-4 w-4" /></span>
              </div>
              {comp?.detail && <div className="mt-3 text-xs text-destructive">{comp.detail}</div>}
            </div>
          );
        })}
      </div>

      <SectionCard title="Platform" className="mt-6">
        {loading ? (
          <Skeleton className="h-12 w-full" />
        ) : (
          <ul className="text-sm divide-y divide-border">
            <li className="py-2.5 flex justify-between"><span className="text-muted-foreground">Overall</span><span className="capitalize" style={{ color: `var(--${health?.overall === "healthy" ? "success" : "warning"})` }}>{health?.overall ?? "—"}</span></li>
            <li className="py-2.5 flex justify-between"><span className="text-muted-foreground">Version</span><span className="font-mono">{health?.version ?? "—"}</span></li>
          </ul>
        )}
      </SectionCard>
    </AppShell>
  );
}
