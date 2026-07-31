import type { Metadata } from "next";
import { FilesView } from "@/components/files/files-view";

export const metadata: Metadata = { title: "Dosyalar" };

export default function FilesPage() {
  return <FilesView />;
}
