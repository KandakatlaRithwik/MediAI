import { ReactNode } from "react";
import {
  Stethoscope,
  ListChecks,
  Home,
  Pill,
  HeartPulse,
  UserRound,
  AlertTriangle,
  Siren,
  BookOpen,
  ShieldAlert,
} from "lucide-react";

type Section = { key: string; title: string; body: string };

const SECTION_META: Record<string, { icon: ReactNode; tone: string }> = {
  Assessment: { icon: <Stethoscope className="h-4 w-4" />, tone: "text-primary" },
  "Possible Conditions": { icon: <ListChecks className="h-4 w-4" />, tone: "text-secondary" },
  "Home Care": { icon: <Home className="h-4 w-4" />, tone: "text-success" },
  "Safe OTC Medicines (educational only)": { icon: <Pill className="h-4 w-4" />, tone: "text-accent" },
  "Lifestyle Advice": { icon: <HeartPulse className="h-4 w-4" />, tone: "text-success" },
  "Recommended Specialist": { icon: <UserRound className="h-4 w-4" />, tone: "text-secondary" },
  "Warning Signs": { icon: <AlertTriangle className="h-4 w-4" />, tone: "text-warning" },
  "Emergency Advice": { icon: <Siren className="h-4 w-4" />, tone: "text-destructive" },
  References: { icon: <BookOpen className="h-4 w-4" />, tone: "text-muted-foreground" },
  Disclaimer: { icon: <ShieldAlert className="h-4 w-4" />, tone: "text-muted-foreground" },
};

function parseSections(text: string): Section[] {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const sections: Section[] = [];
  let current: Section | null = null;
  let preamble: string[] = [];
  for (const line of lines) {
    const m = line.match(/^##\s+(.+?)\s*$/);
    if (m) {
      if (current) sections.push({ ...current, body: current.body.trim() });
      current = { key: m[1], title: m[1], body: "" };
    } else if (current) {
      current.body += line + "\n";
    } else {
      preamble.push(line);
    }
  }
  if (current) sections.push({ ...current, body: current.body.trim() });
  if (sections.length === 0) {
    return [{ key: "Response", title: "Response", body: text.trim() }];
  }
  const pre = preamble.join("\n").trim();
  if (pre) sections.unshift({ key: "Summary", title: "Summary", body: pre });
  return sections;
}

function renderInline(text: string): ReactNode {
  // Bold **x** and italic *x* support
  const parts: ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = regex.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const token = m[0];
    if (token.startsWith("**")) parts.push(<strong key={i++}>{token.slice(2, -2)}</strong>);
    else parts.push(<em key={i++}>{token.slice(1, -1)}</em>);
    last = m.index + token.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

function renderBody(body: string): ReactNode {
  const lines = body.split("\n").filter((l) => l.trim().length > 0);
  const items: ReactNode[] = [];
  let bulletGroup: string[] = [];
  const flush = (key: string) => {
    if (bulletGroup.length === 0) return;
    items.push(
      <ul key={`ul-${key}`} className="list-disc pl-5 space-y-1.5 text-sm leading-relaxed">
        {bulletGroup.map((b, idx) => (
          <li key={idx}>{renderInline(b.replace(/^[-*]\s+/, ""))}</li>
        ))}
      </ul>,
    );
    bulletGroup = [];
  };
  lines.forEach((line, idx) => {
    if (/^\s*[-*]\s+/.test(line)) {
      bulletGroup.push(line);
    } else {
      flush(`g${idx}`);
      items.push(
        <p key={`p-${idx}`} className="text-sm leading-relaxed">
          {renderInline(line)}
        </p>,
      );
    }
  });
  flush("end");
  return <div className="space-y-2">{items}</div>;
}

export function StructuredAnswer({ text }: { text: string }) {
  const sections = parseSections(text);
  return (
    <div className="space-y-3">
      {sections.map((s) => {
        const meta = SECTION_META[s.title] ?? { icon: null, tone: "text-foreground" };
        const isEmergency = s.title === "Emergency Advice" && /seek emergency/i.test(s.body);
        return (
          <div
            key={s.title}
            className={`rounded-lg border p-3 ${
              isEmergency
                ? "border-destructive/40 bg-destructive/5"
                : "border-border bg-card/60"
            }`}
          >
            <div className={`flex items-center gap-2 text-xs uppercase tracking-[0.14em] font-medium ${meta.tone}`}>
              {meta.icon}
              <span>{s.title}</span>
            </div>
            <div className="mt-2 text-foreground/90">{renderBody(s.body)}</div>
          </div>
        );
      })}
    </div>
  );
}
