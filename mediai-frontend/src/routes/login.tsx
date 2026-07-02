import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { AuthShell, Field } from "@/components/auth-shell";
import { useAuth } from "@/lib/auth";
import { extractError } from "@/lib/api";

export const Route = createFileRoute("/login")({
  head: () => ({ meta: [{ title: "Log in · MediAI" }, { name: "description", content: "Sign in to your MediAI clinical workspace." }] }),
  component: LoginPage,
});

function LoginPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to your MediAI workspace."
      footer={<>Don't have an account? <Link to="/register" className="text-secondary font-medium hover:underline">Create one</Link></>}
    >
      <form
        className="space-y-4"
        onSubmit={async (e) => {
          e.preventDefault();
          setError(null);
          setLoading(true);
          try {
            await signIn(email, password);
            navigate({ to: "/app/dashboard" });
          } catch (err) {
            setError(extractError(err, "Invalid email or password"));
          } finally {
            setLoading(false);
          }
        }}
      >
        <Field label="Email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@clinic.com" />
        <Field label="Password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
        {error && <div className="text-sm text-destructive">{error}</div>}
        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 text-muted-foreground"><input type="checkbox" className="rounded border-border" /> Remember me</label>
          <Link to="/forgot-password" className="text-secondary hover:underline">Forgot password?</Link>
        </div>
        <button type="submit" disabled={loading} className="w-full h-11 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition disabled:opacity-60">{loading ? "Signing in…" : "Sign in"}</button>
      </form>
    </AuthShell>
  );
}