import { DashboardView } from "@/components/dashboard-view";
import { getHealthStatus } from "@/lib/api";

export default async function DashboardPage() {
  const health = await getHealthStatus();

  return <DashboardView health={health} />;
}
