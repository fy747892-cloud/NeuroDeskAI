"use client";

import { useEffect, useMemo, useState } from "react";
import { analyzeFile, deleteFile, FileRecord, listFiles } from "@/lib/api";
import { useSession } from "@/lib/session";

export function FilesView() {
  const { tokens } = useSession();
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);
  const [activeId, setActiveId] = useState<string | null>(null);

  async function loadFiles() {
    if (!tokens?.accessToken) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setFiles(await listFiles(tokens.accessToken));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Dosyalar alinamadi.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadFiles();
  }, [tokens?.accessToken]);

  const summary = useMemo(() => {
    const totalBytes = files.reduce((total, file) => total + file.size_bytes, 0);
    return {
      total: files.length,
      ready: files.filter((file) => file.status === "ready").length,
      processing: files.filter((file) => file.status !== "ready").length,
      storage: formatBytes(totalBytes),
    };
  }, [files]);

  async function handleAnalyze(file: FileRecord) {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveId(file.id);
    setError(null);
    setNotice(null);
    try {
      const analysis = await analyzeFile(tokens.accessToken, file.id);
      setNotice(`${file.filename} analiz durumu: ${analysis.status}`);
    } catch (analysisError) {
      setError(analysisError instanceof Error ? analysisError.message : "Dosya analiz edilemedi.");
    } finally {
      setActiveId(null);
    }
  }

  async function handleDelete(file: FileRecord) {
    if (!tokens?.accessToken) {
      return;
    }

    setActiveId(file.id);
    setError(null);
    setNotice(null);
    try {
      await deleteFile(tokens.accessToken, file.id);
      setFiles((currentFiles) => currentFiles.filter((currentFile) => currentFile.id !== file.id));
      setNotice(`${file.filename} silindi.`);
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Dosya silinemedi.");
    } finally {
      setActiveId(null);
    }
  }

  return (
    <section className="moduleSurface">
      {error ? <p className="notice">{error}</p> : null}
      {notice ? <p className="notice success">{notice}</p> : null}

      <div className="moduleGrid">
        <SummaryCard label="Dosya" value={summary.total} />
        <SummaryCard label="Hazir" value={summary.ready} />
        <SummaryCard label="Islemde" value={summary.processing} />
        <SummaryCard label="Boyut" value={summary.storage} />
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>Dosya listesi</h2>
          <button disabled={isLoading} onClick={loadFiles} type="button">
            {isLoading ? "Yukleniyor" : "Yenile"}
          </button>
        </div>
        <div className="dataList">
          {isLoading ? <p className="emptyState">Dosyalar yukleniyor.</p> : null}
          {!isLoading && files.length === 0 ? <p className="emptyState">Dosya bulunmuyor.</p> : null}
          {files.map((file) => (
            <article className="dataRow" key={file.id}>
              <div>
                <div className="rowTitle">
                  <h3>{file.filename}</h3>
                  <span>{file.mime_type}</span>
                </div>
                <p>{formatBytes(file.size_bytes)} | {formatDateTime(file.created_at)}</p>
                <small>{file.status}</small>
              </div>
              <div className="rowActions horizontal">
                <button disabled={activeId === file.id} onClick={() => handleAnalyze(file)} type="button">
                  Analiz et
                </button>
                <button disabled={activeId === file.id} onClick={() => handleDelete(file)} type="button">
                  Sil
                </button>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function SummaryCard({ label, value }: { label: string; value: number | string }) {
  return (
    <article className="moduleCard compact">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${Math.round(bytes / 1024)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
  }).format(new Date(value));
}
