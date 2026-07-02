import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { AuthShell, Field } from "@/components/auth-shell";
import { api, extractError } from "@/lib/api";

export const Route = createFileRoute("/forgot-password")({
  head: () => ({
    meta: [
      { title: "Recover password · MediAI" },
      { name: "description", content: "Reset your MediAI password using your security question." },
    ],
  }),
  component: ForgotPasswordPage,
});

type Step = "email" | "answer" | "done";

function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [question, setQuestion] = useState<string>("");
  const [answer, setAnswer] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function lookupQuestion(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.post<{ security_question: string }>(
        "/auth/security-question",
        { email },
      );
      setQuestion(data.security_question);
      setStep("answer");
    } catch (err) {
      setError(extractError(err, "No security question is available for that account."));
    } finally {
      setLoading(false);
    }
  }

  async function submitReset(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await api.post("/auth/reset-password", {
        email,
        security_answer: answer,
        new_password: newPassword,
      });
      setStep("done");
    } catch (err) {
      setError(extractError(err, "Security answer is incorrect."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell
      title="Recover your password"
      subtitle="Answer your security question — no email required."
      footer={<>Remembered it? <Link to="/login" className="text-secondary font-medium hover:underline">Back to sign in</Link></>}
    >
      {step === "email" && (
        <form className="space-y-4" onSubmit={lookupQuestion}>
          <Field
            label="Email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@clinic.com"
          />
          {error && <div className="text-sm text-destructive">{error}</div>}
          <button
            type="submit"
            disabled={loading}
            className="w-full h-11 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition disabled:opacity-60"
          >
            {loading ? "Looking up…" : "Continue"}
          </button>
        </form>
      )}

      {step === "answer" && (
        <form className="space-y-4" onSubmit={submitReset}>
          <div className="rounded-md border border-border bg-muted/40 p-3">
            <div className="text-xs uppercase tracking-wider text-muted-foreground">Your security question</div>
            <div className="mt-1 text-sm font-medium">{question}</div>
          </div>
          <Field
            label="Answer"
            required
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Case-insensitive"
          />
          <Field
            label="New password"
            type="password"
            required
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="At least 8 characters"
          />
          <Field
            label="Confirm new password"
            type="password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Re-enter new password"
          />
          {error && <div className="text-sm text-destructive">{error}</div>}
          <button
            type="submit"
            disabled={loading}
            className="w-full h-11 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition disabled:opacity-60"
          >
            {loading ? "Resetting…" : "Reset password"}
          </button>
          <button
            type="button"
            onClick={() => { setStep("email"); setError(null); }}
            className="w-full text-xs text-muted-foreground hover:text-foreground"
          >
            ← Use a different email
          </button>
        </form>
      )}

      {step === "done" && (
        <div className="space-y-4">
          <div className="rounded-md border border-success/30 bg-success/10 p-4 text-sm">
            <div className="font-medium text-success">Password reset successfully.</div>
            <p className="mt-1 text-muted-foreground">You can now sign in with your new password.</p>
          </div>
          <button
            onClick={() => navigate({ to: "/login" })}
            className="w-full h-11 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition"
          >
            Go to sign in
          </button>
        </div>
      )}
    </AuthShell>
  );
}