import { AuthGuard } from "@/components/auth-guard";
import { AppShell } from "@/components/app-shell";
import { getHealthStatus } from "@/lib/api";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const health = await getHealthStatus();

  return (
    <AuthGuard>
      <AppShell health={health}>{children}</AppShell>
    </AuthGuard>
  );
}
