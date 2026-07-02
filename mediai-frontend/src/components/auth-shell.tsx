import { Link } from "@tanstack/react-router";
import {
  Activity, ShieldCheck, Lock, Stethoscope, Brain, HeartPulse, KeyRound,
} from "lucide-react";
import type { ReactNode, SelectHTMLAttributes } from "react";

export function AuthShell({ title, subtitle, children, footer }: { title: string; subtitle: string; children: ReactNode; footer: ReactNode }) {
  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-background">
      {/* LEFT — brand panel with layered clinical visual */}
      <div className="hidden lg:flex relative flex-col justify-between p-12 bg-primary text-primary-foreground overflow-hidden">
        <div className="absolute inset-0 grid-clinical opacity-10" />
        <div className="absolute -top-32 -right-24 h-80 w-80 rounded-full bg-secondary/25 blur-3xl" />
        <div className="absolute bottom-0 -left-24 h-72 w-72 rounded-full bg-accent/15 blur-3xl" />

        <Link to="/" className="relative flex items-center gap-2 font-semibold">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary-foreground/10 border border-primary-foreground/20">
            <Activity className="h-4 w-4" />
          </span>
          MediAI
        </Link>

        <div className="relative space-y-8 max-w-md">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-primary-foreground/20 bg-primary-foreground/5 px-2.5 py-1 text-[11px] uppercase tracking-wider text-primary-foreground/70">
              <span className="h-1.5 w-1.5 rounded-full bg-success" /> Clinical preview
            </span>
            <h2 className="mt-5 text-3xl font-semibold tracking-tight leading-tight">
              The clinical co-pilot trusted by modern care teams.
            </h2>
            <p className="mt-3 text-sm text-primary-foreground/70 leading-relaxed">
              Symptom triage, report analysis and evidence-grounded answers — from one secure workspace.
            </p>
          </div>

          {/* Mini clinical vignette card */}
          <div className="relative rounded-xl border border-primary-foreground/15 bg-primary-foreground/5 backdrop-blur p-5 space-y-4">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-primary-foreground/70">
                <Stethoscope className="h-3.5 w-3.5" /> Vitals snapshot
              </div>
              <span className="font-mono text-primary-foreground/50">#A-2941</span>
            </div>
            <div className="grid grid-cols-3 gap-3 text-center">
              {[
                { l: "HbA1c", v: "6.1%", ok: true },
                { l: "LDL",   v: "142",  ok: false },
                { l: "BP",    v: "128/82", ok: true },
              ].map((m) => (
                <div key={m.l} className="rounded-lg border border-primary-foreground/10 bg-primary-foreground/[0.03] p-2">
                  <div className="text-[10px] uppercase tracking-wider text-primary-foreground/50">{m.l}</div>
                  <div className="mt-1 font-mono text-sm">{m.v}</div>
                  <div className={`mt-0.5 text-[10px] ${m.ok ? "text-success" : "text-warning"}`}>{m.ok ? "in range" : "high"}</div>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-2 rounded-md bg-primary-foreground/5 border border-primary-foreground/10 px-3 py-2 text-xs text-primary-foreground/70">
              <HeartPulse className="h-3.5 w-3.5" /> Glycemic control on target · LDL trending up.
            </div>
          </div>

          <div className="space-y-2.5 text-sm text-primary-foreground/70">
            <Row icon={<Brain className="h-4 w-4" />} label="RAG · retrieval-grounded answers" />
            <Row icon={<ShieldCheck className="h-4 w-4" />} label="Emergency detection & red-flag alerts" />
            <Row icon={<KeyRound className="h-4 w-4" />} label="Security-question account recovery" />
            <Row icon={<Lock className="h-4 w-4" />} label="JWT + bcrypt, role-based access" />
          </div>
        </div>

        <div className="relative text-xs text-primary-foreground/50 font-mono">v1.0 · clinical preview</div>
      </div>

      {/* RIGHT — form area (unchanged design) */}
      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <Link to="/" className="lg:hidden flex items-center gap-2 font-semibold mb-8">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground"><Activity className="h-4 w-4" /></span>
            MediAI
          </Link>
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">{subtitle}</p>
          <div className="mt-8 space-y-4">{children}</div>
          <div className="mt-8 text-sm text-muted-foreground">{footer}</div>
        </div>
      </div>
    </div>
  );
}

function Row({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="inline-flex h-6 w-6 items-center justify-center rounded-md bg-primary-foreground/10">{icon}</span>
      {label}
    </div>
  );
}

export function Field({ label, ...props }: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{label}</span>
      <input
        {...props}
        className="mt-1.5 w-full h-11 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-secondary focus:ring-2 focus:ring-secondary/20 transition"
      />
    </label>
  );
}

export function SelectField({
  label, options, ...props
}: { label: string; options: { value: string; label: string }[] } & SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{label}</span>
      <select
        {...props}
        className="mt-1.5 w-full h-11 rounded-md border border-border bg-card px-3 text-sm outline-none focus:border-secondary focus:ring-2 focus:ring-secondary/20 transition"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  );
}