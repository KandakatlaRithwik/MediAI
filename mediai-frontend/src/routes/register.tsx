import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AuthShell, Field, SelectField } from "@/components/auth-shell";
import { useAuth } from "@/lib/auth";
import { api, extractError, DEFAULT_SECURITY_QUESTIONS } from "@/lib/api";

export const Route = createFileRoute("/register")({
  head: () => ({ meta: [{ title: "Create account · MediAI" }, { name: "description", content: "Create your MediAI clinical workspace." }] }),
  component: RegisterPage,
});

function RegisterPage() {
  const { signUp } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [questions, setQuestions] = useState<string[]>(DEFAULT_SECURITY_QUESTIONS);
  const [securityQuestion, setSecurityQuestion] = useState<string>(DEFAULT_SECURITY_QUESTIONS[0]);
  const [securityAnswer, setSecurityAnswer] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api.get<{ questions: string[] }>("/auth/security-questions").then(({ data }) => {
      if (cancelled || !Array.isArray(data.questions) || data.questions.length === 0) return;
      setQuestions(data.questions);
      setSecurityQuestion(data.questions[0]);
    }).catch(() => { /* keep defaults */ });
    return () => { cancelled = true; };
  }, []);

  return (
    <AuthShell
      title="Create your account"
      subtitle="Two minutes to your first consultation."
      footer={<>Already have an account? <Link to="/login" className="text-secondary font-medium hover:underline">Sign in</Link></>}
    >
      <form
        className="space-y-4"
        onSubmit={async (e) => {
          e.preventDefault();
          setError(null);
          setLoading(true);
          try {
            await signUp(name, email, password, securityQuestion, securityAnswer);
            navigate({ to: "/app/dashboard" });
          } catch (err) {
            setError(extractError(err, "Unable to create account"));
          } finally {
            setLoading(false);
          }
        }}
      >
        <Field label="Full name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Dr. Jane Doe" />
        <Field label="Email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@clinic.com" />
        <Field label="Password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 8 characters" />
        <SelectField
          label="Security question"
          value={securityQuestion}
          onChange={(e) => setSecurityQuestion(e.target.value)}
          options={questions.map((q) => ({ value: q, label: q }))}
        />
        <Field
          label="Security answer"
          required
          value={securityAnswer}
          onChange={(e) => setSecurityAnswer(e.target.value)}
          placeholder="Case-insensitive · used to recover your password"
        />
        {error && <div className="text-sm text-destructive">{error}</div>}
        <p className="text-xs text-muted-foreground">
          Your security answer is stored hashed (bcrypt) — never in plaintext — and is only used to
          verify identity during password recovery. MediAI is not a substitute for professional
          medical advice.
        </p>
        <button type="submit" disabled={loading} className="w-full h-11 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition disabled:opacity-60">{loading ? "Creating…" : "Create account"}</button>
      </form>
    </AuthShell>
  );
}