import { Link } from "@tanstack/react-router";
import { Activity } from "lucide-react";

export function SiteNav() {
  return (
    <header className="sticky top-0 z-40 backdrop-blur-xl bg-background/70 border-b border-border">
      <div className="mx-auto max-w-7xl px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Activity className="h-4 w-4" />
          </span>
          <span>MediAI</span>
          <span className="ml-2 hidden md:inline text-[10px] uppercase tracking-[0.18em] text-muted-foreground border border-border rounded px-1.5 py-0.5">
            Clinical&nbsp;Preview
          </span>
        </Link>
        <nav className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
          <Link to="/" className="hover:text-foreground transition">Home</Link>
          <a href="#features" className="hover:text-foreground transition">Features</a>
          <a href="#solutions" className="hover:text-foreground transition">Solutions</a>
          <Link to="/app/dashboard" className="hover:text-foreground transition">Dashboard</Link>
        </nav>
        <div className="flex items-center gap-2">
          <Link to="/login" className="text-sm px-3 py-1.5 rounded-md hover:bg-muted transition">Log in</Link>
          <Link
            to="/register"
            className="text-sm px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition"
          >
            Get started
          </Link>
        </div>
      </div>
    </header>
  );
}