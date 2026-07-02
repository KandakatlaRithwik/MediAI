import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  Activity, Brain, FileText, MessagesSquare, ShieldCheck, Stethoscope,
  ScanLine, LineChart, History, Lock, ArrowRight, CheckCircle2, HeartPulse,
} from "lucide-react";
import { SiteNav } from "@/components/site-nav";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "MediAI — AI-Powered Healthcare Assistant" },
      { name: "description", content: "Intelligent symptom analysis, medical report interpretation and clinical guidance, in one secure platform." },
      { property: "og:title", content: "MediAI — AI-Powered Healthcare Assistant" },
      { property: "og:description", content: "Intelligent symptom analysis, medical report interpretation and clinical guidance." },
    ],
  }),
  component: Landing,
});

const features = [
  { icon: MessagesSquare, title: "Medical Chat Assistant", desc: "Conversational guidance grounded in vetted clinical sources." },
  { icon: Brain, title: "RAG-Powered Knowledge", desc: "Retrieval over peer-reviewed literature with cited references." },
  { icon: Stethoscope, title: "Symptom Intelligence", desc: "Differential reasoning with severity and specialist suggestions." },
  { icon: HeartPulse, title: "Disease Prediction", desc: "Probabilistic models highlight likely conditions and red flags." },
  { icon: ShieldCheck, title: "Emergency Detection", desc: "Automatic triage signals for time-critical presentations." },
  { icon: FileText, title: "Report Analysis", desc: "Parses lab panels and flags out-of-range values clearly." },
  { icon: ScanLine, title: "OCR Processing", desc: "Reads PDFs and scanned reports with EasyOCR + Tesseract." },
  { icon: LineChart, title: "Patient Dashboard", desc: "A single view of health activity, trends and risk." },
  { icon: History, title: "Medical History", desc: "Longitudinal timeline of chats, reports and assessments." },
  { icon: Lock, title: "Secure by default", desc: "JWT auth, RBAC and audited access on every request." },
];

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: (i = 0) => ({ opacity: 1, y: 0, transition: { delay: i * 0.05, duration: 0.5, ease: [0.22, 1, 0.36, 1] as const } }),
};

function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <SiteNav />

      {/* HERO */}
      <section className="relative overflow-hidden border-b border-border">
        <div className="absolute inset-0 grid-clinical opacity-60 [mask-image:radial-gradient(ellipse_at_top,black,transparent_70%)]" />
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 h-[420px] w-[820px] rounded-full bg-secondary/10 blur-3xl" />
        <div className="relative mx-auto max-w-7xl px-6 pt-20 pb-24 lg:pt-28 lg:pb-32">
          <motion.div variants={fadeUp} initial="hidden" animate="show" className="max-w-3xl">
            <span className="chip"><span className="h-1.5 w-1.5 rounded-full bg-success" /> HIPAA-aligned · SOC 2 in progress</span>
            <h1 className="mt-6 text-5xl sm:text-6xl font-semibold tracking-[-0.03em] leading-[1.02]">
              The clinical co-pilot for{" "}
              <span className="text-secondary">modern healthcare.</span>
            </h1>
            <p className="mt-6 text-lg text-muted-foreground max-w-2xl leading-relaxed">
              MediAI combines retrieval-augmented reasoning, symptom intelligence and medical report
              analysis into one workflow — so patients get faster answers and clinicians get sharper signal.
            </p>
            <div className="mt-9 flex flex-wrap items-center gap-3">
              <Link to="/app/chat" className="group inline-flex items-center gap-2 rounded-md bg-primary text-primary-foreground px-5 py-3 text-sm font-medium hover:bg-primary/90 transition">
                Start consultation
                <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
              </Link>
              <a href="#features" className="inline-flex items-center gap-2 rounded-md border border-border bg-card px-5 py-3 text-sm font-medium hover:bg-muted transition">
                Explore features
              </a>
            </div>

            {/* Real capabilities — replaces unverified marketing metrics. */}
            <div className="mt-10 max-w-2xl">
              <div className="text-xs uppercase tracking-wider text-muted-foreground mb-3">
                Built-in capabilities
              </div>
              <div className="flex flex-wrap gap-2">
                {[
                  "RAG (Retrieval-Augmented Generation)",
                  "Gemini LLM",
                  "OCR (EasyOCR + Tesseract)",
                  "Medical NLP",
                  "JWT Authentication",
                  "Disease Knowledge Base",
                  "Report Analysis (PDF · DOCX · Image)",
                  "Emergency Detection",
                ].map((c) => (
                  <span
                    key={c}
                    className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground/80"
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-secondary" />
                    {c}
                  </span>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Floating clinical card */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="relative mt-16 mx-auto max-w-5xl"
          >
            <div className="surface-card overflow-hidden">
              <div className="flex items-center justify-between border-b border-border px-4 py-2.5 bg-muted/40">
                <div className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-destructive/70" />
                  <span className="h-2.5 w-2.5 rounded-full bg-warning/70" />
                  <span className="h-2.5 w-2.5 rounded-full bg-success/70" />
                </div>
                <div className="font-mono text-xs text-muted-foreground">mediai.app · consultation #A-2941</div>
                <span className="chip"><Activity className="h-3 w-3" /> live</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3">
                <div className="md:col-span-2 p-6 border-r border-border space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-xs font-medium">JD</div>
                    <div className="rounded-2xl rounded-tl-md bg-muted px-4 py-3 text-sm max-w-md">
                      I've had a dry cough for 5 days, mild fever yesterday, and tightness in my chest when climbing stairs.
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium">AI</div>
                    <div className="rounded-2xl rounded-tl-md bg-card border border-border px-4 py-3 text-sm max-w-md space-y-2">
                      <p>Your symptoms align with an <span className="font-medium">acute lower respiratory infection</span>. Three patterns worth considering:</p>
                      <ul className="text-muted-foreground space-y-1">
                        <li>• Viral bronchitis — <span className="font-mono text-foreground">62%</span></li>
                        <li>• Community-acquired pneumonia — <span className="font-mono text-foreground">21%</span></li>
                        <li>• Reactive airway — <span className="font-mono text-foreground">11%</span></li>
                      </ul>
                      <div className="flex items-center gap-2 text-xs text-warning"><ShieldCheck className="h-3.5 w-3.5" /> Watch for: SpO₂ &lt; 94%, chest pain, persistent fever &gt; 39°C.</div>
                    </div>
                  </div>
                </div>
                <div className="p-6 space-y-4">
                  <div>
                    <div className="text-xs uppercase tracking-wider text-muted-foreground">Severity</div>
                    <div className="mt-2 flex items-center gap-2">
                      <div className="h-2 flex-1 rounded-full bg-muted overflow-hidden">
                        <div className="h-full w-[58%] bg-warning" />
                      </div>
                      <span className="font-mono text-sm">Moderate</span>
                    </div>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-wider text-muted-foreground">Recommended</div>
                    <p className="mt-1 text-sm">See a <span className="font-medium">Pulmonologist</span> within 48 hours.</p>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-wider text-muted-foreground">Sources</div>
                    <ul className="mt-1 text-xs text-muted-foreground space-y-1">
                      <li>NEJM · Acute bronchitis review (2023)</li>
                      <li>CDC · CAP clinical guidance</li>
                      <li>UpToDate · Adult cough algorithm</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="relative border-b border-border">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="flex items-end justify-between flex-wrap gap-4 mb-12">
            <div className="max-w-2xl">
              <span className="chip">Capabilities</span>
              <h2 className="mt-4 text-3xl sm:text-4xl font-semibold tracking-tight">A complete clinical surface, in one workspace.</h2>
              <p className="mt-3 text-muted-foreground">Every module is built on the same retrieval engine, audit log and patient timeline — no glue code, no compliance gaps.</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-px bg-border rounded-xl overflow-hidden border border-border">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                custom={i}
                variants={fadeUp}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, margin: "-80px" }}
                className="bg-card p-6 hover:bg-muted/30 transition group"
              >
                <div className="h-10 w-10 rounded-lg bg-primary/5 border border-border flex items-center justify-center text-primary group-hover:bg-accent/15 group-hover:text-accent transition">
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 font-medium tracking-tight">{f.title}</h3>
                <p className="mt-1.5 text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* SOLUTIONS */}
      <section id="solutions" className="border-b border-border">
        <div className="mx-auto max-w-7xl px-6 py-24 grid lg:grid-cols-2 gap-16 items-center">
          <div>
            <span className="chip">For care teams</span>
            <h2 className="mt-4 text-3xl sm:text-4xl font-semibold tracking-tight">Built for clinicians.<br/>Trusted by patients.</h2>
            <p className="mt-4 text-muted-foreground leading-relaxed">From front-line triage to chronic care follow-up, MediAI reduces administrative load while keeping the clinician in the loop on every decision.</p>
            <ul className="mt-8 space-y-3 text-sm">
              {[
                "Inline citations from peer-reviewed sources",
                "Role-based access control with audit trails",
                "Drag-and-drop report ingestion (PDF, JPG, PNG)",
                "Patient timeline with longitudinal risk tracking",
              ].map((t) => (
                <li key={t} className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-accent shrink-0 mt-0.5" />
                  <span>{t}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="surface-card p-6">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">Patient · Sarah K.</div>
              <span className="chip"><span className="h-1.5 w-1.5 rounded-full bg-success" /> stable</span>
            </div>
            <div className="mt-5 grid grid-cols-3 gap-4">
              {[
                { l: "HbA1c", v: "6.1%", ok: true },
                { l: "LDL", v: "142 mg/dL", ok: false },
                { l: "BP", v: "128/82", ok: true },
              ].map((m) => (
                <div key={m.l} className="rounded-lg border border-border p-3">
                  <div className="text-xs text-muted-foreground">{m.l}</div>
                  <div className="font-mono mt-1">{m.v}</div>
                  <div className={`text-xs mt-1 ${m.ok ? "text-success" : "text-warning"}`}>{m.ok ? "In range" : "Elevated"}</div>
                </div>
              ))}
            </div>
            <div className="mt-5 rounded-lg bg-muted/40 border border-border p-4 text-sm">
              <div className="text-xs uppercase tracking-wider text-muted-foreground">AI Summary</div>
              <p className="mt-1.5">Glycemic control on target. LDL trending up — consider lifestyle review and re-test in 8 weeks.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-b border-border">
        <div className="mx-auto max-w-7xl px-6 py-20 text-center">
          <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight">Your intelligent medical companion.</h2>
          <p className="mt-3 text-muted-foreground max-w-xl mx-auto">Start a consultation in seconds. No card required.</p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Link to="/register" className="rounded-md bg-primary text-primary-foreground px-5 py-3 text-sm font-medium hover:bg-primary/90 transition">Create account</Link>
            <Link to="/app/dashboard" className="rounded-md border border-border bg-card px-5 py-3 text-sm font-medium hover:bg-muted transition">Open dashboard</Link>
          </div>
        </div>
      </section>

      <footer className="mx-auto max-w-7xl px-6 py-10 flex items-center justify-between text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-6 w-6 items-center justify-center rounded-md bg-primary text-primary-foreground"><Activity className="h-3 w-3" /></span>
          MediAI © {new Date().getFullYear()}
        </div>
        <div>Informational use only. Not a substitute for professional medical advice.</div>
      </footer>
    </div>
  );
}
