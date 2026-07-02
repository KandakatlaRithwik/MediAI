import { createFileRoute } from "@tanstack/react-router";
import { AppShell, SectionCard } from "@/components/app-shell";
import { Field } from "@/components/auth-shell";
import { useAuth } from "@/lib/auth";
import { Skeleton } from "@/components/ui/skeleton";

export const Route = createFileRoute("/app/profile")({
  head: () => ({ meta: [{ title: "Profile · MediAI" }] }),
  component: ProfilePage,
});

function ProfilePage() {
  const { user, loading } = useAuth();

  return (
    <AppShell title="Profile" subtitle="Patient information and account">
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <SectionCard title="Patient information" className="xl:col-span-2">
          {loading || !user ? (
            <div className="space-y-4">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : (
            <>
              <div className="flex items-center gap-4 mb-6">
                <div className="h-16 w-16 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xl font-medium">
                  {(user.full_name || "U").slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <div className="text-lg font-medium">{user.full_name}</div>
                  <div className="text-sm text-muted-foreground">{user.email}</div>
                  <div className="mt-1 chip">{user.role}</div>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Field label="Full name" defaultValue={user.full_name} readOnly />
                <Field label="Email" defaultValue={user.email} readOnly />
                <Field label="Phone" defaultValue={user.phone ?? ""} readOnly />
                <Field label="Role" defaultValue={user.role} readOnly />
              </div>
            </>
          )}
        </SectionCard>

        <div className="space-y-4">
          <SectionCard title="Account">
            <ul className="text-sm divide-y divide-border">
              <li className="py-2.5 flex justify-between"><span className="text-muted-foreground">Status</span><span className="font-medium">{user?.is_active ? "Active" : "Inactive"}</span></li>
              <li className="py-2.5 flex justify-between"><span className="text-muted-foreground">Member since</span><span className="font-mono text-xs">{user?.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}</span></li>
              <li className="py-2.5 flex justify-between"><span className="text-muted-foreground">User ID</span><span className="font-mono text-xs truncate max-w-[140px]">{user?.uuid ?? "—"}</span></li>
            </ul>
          </SectionCard>
        </div>
      </div>
    </AppShell>
  );
}
