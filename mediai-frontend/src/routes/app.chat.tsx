import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Send, Sparkles, BookOpen, ShieldAlert, Plus, MessageSquare } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { api, extractError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { StructuredAnswer } from "@/components/structured-answer";

export const Route = createFileRoute("/app/chat")({
  head: () => ({ meta: [{ title: "AI Medical Chat · MediAI" }] }),
  component: ChatPage,
});

type Msg = { role: "user" | "ai"; text: string; sources?: string[] };

const greeting: Msg = {
  role: "ai",
  text: "Hi — I'm your MediAI assistant. Describe what you're experiencing, share a report, or ask a clinical question. I'll cite sources where relevant.",
};

const suggestions = [
  "Explain my recent lipid panel results",
  "What could cause persistent fatigue with elevated TSH?",
  "Drug interactions between metformin and lisinopril",
  "Triage chest pain in a 54-year-old male",
];

type ChatHistoryEntry = { id: number; question: string; response: string; created_at: string };

function ChatPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Msg[]>([greeting]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<ChatHistoryEntry[]>([]);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming]);

  useEffect(() => {
    api
      .get<ChatHistoryEntry[]>("/history/chat")
      .then((r) => setHistory(r.data.slice(0, 12)))
      .catch(() => setHistory([]));
  }, []);

  async function send(text?: string) {
    const q = (text ?? input).trim();
    if (!q) return;
    setError(null);
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setStreaming(true);
    try {
      const { data } = await api.post("/ask", { question: q });
      setMessages((m) => [...m, { role: "ai", text: data.answer, sources: data.sources ?? [] }]);
    } catch (err) {
      setError(extractError(err, "The assistant is unavailable. Please try again."));
    } finally {
      setStreaming(false);
    }
  }

  const initials = (user?.full_name || "U").slice(0, 2).toUpperCase();

  return (
    <AppShell title="AI Medical Chat" subtitle="Conversational guidance with cited clinical sources">
      <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr_300px] gap-4 h-[calc(100vh-10rem)]">
        <aside className="surface-card p-3 flex flex-col">
          <button
            onClick={() => setMessages([greeting])}
            className="flex items-center justify-center gap-2 h-10 rounded-md border border-dashed border-border text-sm hover:bg-muted transition"
          >
            <Plus className="h-4 w-4" /> New consultation
          </button>
          <div className="mt-4 px-1 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Recent</div>
          <div className="mt-2 space-y-1 overflow-y-auto">
            {history.length === 0 && (
              <div className="text-xs text-muted-foreground px-3 py-2">No previous chats yet.</div>
            )}
            {history.map((h) => (
              <button
                key={h.id}
                onClick={() => setMessages([greeting, { role: "user", text: h.question }, { role: "ai", text: h.response }])}
                className="w-full text-left rounded-md px-3 py-2 hover:bg-muted text-sm"
              >
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="truncate">{h.question}</span>
                </div>
                <div className="text-xs text-muted-foreground mt-0.5">
                  {new Date(h.created_at).toLocaleString()}
                </div>
              </button>
            ))}
          </div>
        </aside>

        <section className="surface-card flex flex-col min-h-0">
          <div className="flex-1 overflow-y-auto p-6 space-y-5">
            {messages.map((m, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
                {m.role === "ai" && <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium shrink-0">AI</div>}
                <div className={`max-w-2xl rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${m.role === "user" ? "bg-secondary text-secondary-foreground rounded-tr-md" : "bg-card border border-border rounded-tl-md"}`}>
                  {m.role === "ai" ? (
                    <div className="not-prose"><StructuredAnswer text={m.text} /></div>
                  ) : (
                    <p>{m.text}</p>
                  )}
                  {m.sources && m.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border space-y-1">
                      <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground flex items-center gap-1.5"><BookOpen className="h-3 w-3" /> Sources</div>
                      {m.sources.map((s, idx) => <div key={idx} className="text-xs text-muted-foreground">· {s}</div>)}
                    </div>
                  )}
                </div>
                {m.role === "user" && <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-xs font-medium shrink-0">{initials}</div>}
              </motion.div>
            ))}
            {streaming && (
              <div className="flex gap-3">
                <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium">AI</div>
                <div className="rounded-2xl rounded-tl-md bg-card border border-border px-4 py-3 text-sm">
                  <span className="inline-flex gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce" />
                    <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:120ms]" />
                    <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:240ms]" />
                  </span>
                </div>
              </div>
            )}
            {error && <div className="text-sm text-destructive">{error}</div>}
            <div ref={endRef} />
          </div>

          <div className="border-t border-border p-4">
            {messages.length <= 1 && (
              <div className="mb-3 flex gap-2 flex-wrap">
                {suggestions.map((s) => (
                  <button key={s} onClick={() => send(s)} className="chip hover:bg-muted transition">
                    <Sparkles className="h-3 w-3 text-accent" /> {s}
                  </button>
                ))}
              </div>
            )}
            <form onSubmit={(e) => { e.preventDefault(); send(); }} className="flex items-end gap-2 rounded-xl border border-border bg-card focus-within:border-secondary focus-within:ring-2 focus-within:ring-secondary/20 transition px-3 py-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                placeholder="Describe symptoms, ask a clinical question, or paste a report excerpt…"
                rows={2}
                className="flex-1 resize-none bg-transparent outline-none text-sm py-1"
              />
              <button type="submit" className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm font-medium inline-flex items-center gap-1.5 hover:bg-primary/90 transition disabled:opacity-50" disabled={!input.trim() || streaming}>
                <Send className="h-4 w-4" /> Send
              </button>
            </form>
          </div>
        </section>

        <aside className="surface-card p-4 space-y-4 overflow-y-auto">
          <div className="flex items-start gap-2 rounded-lg bg-warning/10 border border-warning/30 p-3 text-xs">
            <ShieldAlert className="h-4 w-4 text-warning shrink-0 mt-0.5" />
            <p className="text-foreground/80">MediAI provides educational guidance. It is not a substitute for professional medical advice, diagnosis or treatment.</p>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Signed in as</div>
            <div className="mt-2 space-y-1.5 text-sm">
              <div className="flex justify-between"><span className="text-muted-foreground">Name</span><span className="truncate ml-2">{user?.full_name ?? "—"}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Email</span><span className="truncate ml-2 text-xs">{user?.email ?? "—"}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">Role</span><span>{user?.role ?? "—"}</span></div>
            </div>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
