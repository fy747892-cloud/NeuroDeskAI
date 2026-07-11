import { ModulePlaceholder } from "@/components/module-placeholder";

export default function ApprovalCenterPage() {
  return (
    <ModulePlaceholder
      description="AI tarafindan uretilen aksiyonlar insan onayi icin burada kuyruklanacak."
      items={[
        { label: "Backend module", value: "ai" },
        { label: "Primary data", value: "Approvals" },
        { label: "Sprint focus", value: "Human review" },
      ]}
    />
  );
}
