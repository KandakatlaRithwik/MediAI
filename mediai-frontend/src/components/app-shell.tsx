import { Link, useRouterState } from "@tanstack/react-router";
import { Activity, LayoutDashboard, MessagesSquare, Stethoscope, FileText, History, User, Shield, Bell, Search, LogOut } from "lucide-react";
import type { ReactNode } from "react";
import { useAuth } from "@/lib/auth";

const nav = [
  { to: "/app/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/app/chat", label: "AI Chat", icon: MessagesSquare },
  { to: "/app/symptoms", label: "Symptom Checker", icon: Stethoscope },
  { to: "/app/reports", label: "Report Analyzer", icon: FileText },
  { to: "/app/history", label: "History", icon: History },
  { to: "/app/profile", label: "Profile", icon: User },
  { to: "/app/admin", label: "Admin", icon: Shield },
] as const;

export function AppShell({ title, subtitle, actions, children }: { title: string; subtitle?: string; actions?: ReactNode; children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { user, signOut } = useAuth();

  return (
    <div className="min-h-screen bg-background text-foreground flex">
      {/* Sidebar */}
      <aside className="hidden lg:flex w-64 shrink-0 flex-col bg-sidebar text-sidebar-foreground border-r border-sidebar-border">
        <Link to="/" className="h-16 px-5 flex items-center gap-2 font-semibold border-b border-sidebar-border">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground"><Activity className="h-4 w-4" /></span>
          MediAI
        </Link>
        <nav className="flex-1 p-3 space-y-0.5">
          <div className="px-2 pt-2 pb-1 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Workspace</div>
          {nav.map((n) => {
            const active = pathname === n.to;
            return (
              <Link
                key={n.to}
                to={n.to}
                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition ${
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground"
                }`}
              >
                <n.icon className="h-4 w-4" />
                {n.label}
                {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-accent" />}
              </Link>
            );
          })}
        </nav>
        <div className="p-3 border-t border-sidebar-border">
          <div className="flex items-center gap-3 rounded-md p-2 hover:bg-sidebar-accent/60 transition">
            <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium">
              {(user?.full_name || "G").slice(0, 2).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm truncate">{user?.full_name || "Guest"}</div>
              <div className="text-xs text-muted-foreground truncate">{user?.email || "not signed in"}</div>
            </div>
            <button onClick={signOut} className="text-muted-foreground hover:text-foreground" aria-label="Sign out">
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="h-16 border-b border-border bg-background/80 backdrop-blur sticky top-0 z-30">
          <div className="h-full px-6 flex items-center gap-4">
            <div>
              <h1 className="text-lg font-semibold tracking-tight">{title}</h1>
              {subtitle && <p className="text-xs text-muted-foreground -mt-0.5">{subtitle}</p>}
            </div>
            <div className="ml-auto flex items-center gap-2">
              <div className="hidden md:flex items-center gap-2 h-9 px-3 rounded-md border border-border bg-card text-sm text-muted-foreground w-72">
                <Search className="h-4 w-4" />
                <input placeholder="Search patients, reports, drugs…" className="bg-transparent outline-none flex-1 text-foreground placeholder:text-muted-foreground" />
                <kbd className="font-mono text-[10px] border border-border rounded px-1.5 py-0.5">⌘K</kbd>
              </div>
              <button className="h-9 w-9 rounded-md border border-border bg-card flex items-center justify-center hover:bg-muted transition relative" aria-label="Notifications">
                <Bell className="h-4 w-4" />
                <span className="absolute top-2 right-2 h-1.5 w-1.5 rounded-full bg-destructive" />
              </button>
              {actions}
            </div>
          </div>
        </header>
        <main className="flex-1 p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}

export function SectionCard({ title, hint, children, className = "" }: { title?: string; hint?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`surface-card p-5 ${className}`}>
      {(title || hint) && (
        <div className="flex items-center justify-between mb-4">
          {title && <h3 className="text-sm font-semibold tracking-tight">{title}</h3>}
          {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
        </div>
      )}
      {children}
    </section>
  );
}