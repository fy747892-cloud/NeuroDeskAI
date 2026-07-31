import type { Metadata } from "next";
import { DealsView } from "@/components/deals/deals-view";

export const metadata: Metadata = { title: "Fırsatlar" };

export default function DealsPage() {
  return <DealsView />;
}
