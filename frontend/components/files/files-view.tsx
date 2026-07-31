"use client";

import { ChangeEvent, DragEvent, FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  analyzeFile,
  deleteFile,
  FileRecord,
  getFileAnalysis,
  getFileDownloadUrl,
  getFileText,
  listFiles,
  updateFile,
  uploadFile,
} from "@/lib/api";
import { Language, useLanguage } from "@/lib/i18n/context";
import { useSession } from "@/lib/session";
import { useToast } from "@/lib/toast";
import { SkeletonList } from "@/components/shell/skeleton";
import { formatDateTime } from "@/lib/format";
import { deferredExecute, UNDO_WINDOW_MS } from "@/lib/undo";
import { EmptyState } from "@/components/shell/empty-state";

type DialogState = {
  title: string;
  status: string;
  content: string;
} | null;

const maxUploadSizeBytes = 25 * 1024 * 1024;
const acceptedExtensions = ".pdf,.docx,.xlsx,.txt,.mp3,.wav,.m4a,.eml";

export function FilesView() {
  const { tokens } = useSession();
  const { t, language } = useLanguage();
  const { showToast } = useToast();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [isLoading, setLoading] = useState(true);
  const [activeFileId, setActiveFileId] = useState<string | null>(null);
  const [isUploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dialog, setDialog] = useState<DialogState>(null);
  const [editingFileId, setEditingFileId] = useState<string | null>(null);
  const [editingFilename, setEditingFilename] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState<"newest" | "oldest" | "name" | "size">("newest");
  const [searchQuery, setSearchQuery] = useState("");
  const [isDragActive, setDragActive] = useState(false);
  const dragCounter = useRef(0);

  const readyCount = useMemo(() => files.filter((file) => file.status === "ready").length, [files]);
  const totalBytes = useMemo(() => files.reduce((sum, file) => sum + file.size_bytes, 0), [files]);

  const availableStatuses = useMemo(
    () => Array.from(new Set(files.map((file) => file.status))).sort(),
    [files],
  );

  const visibleFiles = useMemo(() => {
    let next = files;
    if (statusFilter !== "all") {
      next = next.filter((file) => file.status === statusFilter);
    }
    if (searchQuery.trim()) {
      const query = searchQuery.trim().toLocaleLowerCase(language === "tr" ? "tr-TR" : "en-US");
      next = next.filter((file) => file.filename.toLocaleLowerCase().includes(query));
    }
    const sorted = [...next];
    switch (sortBy) {
      case "oldest":
        sorted.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
        break;
      case "name":
        sorted.sort((a, b) => a.filename.localeCompare(b.filename));
        break;
      case "size":
        sorted.sort((a, b) => b.size_bytes - a.size_bytes);
        break;
      default:
        sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    }
    return sorted;
  }, [files, statusFilter, searchQuery, sortBy, language]);

  const loadFiles = useCallback(async () => {
    if (!tokens?.accessToken) return;
    setLoading(true);
    try {
      const nextFiles = await listFiles(tokens.accessToken);
      setFiles(nextFiles);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : t("files.loadError"));
    } finally {
      setLoading(false);
    }
  }, [tokens?.accessToken, t]);

  useEffect(() => {
    loadFiles();
  }, [loadFiles]);

  async function uploadSelectedFile(selected: File) {
    if (!tokens?.accessToken) return;

    if (selected.size > maxUploadSizeBytes) {
      showToast(t("files.tooLarge", { size: formatBytes(maxUploadSizeBytes) }), "error");
      return;
    }

    setUploading(true);
    setError(null);
    try {
      const uploaded = await uploadFile(tokens.accessToken, selected);
      setFiles((current) => [uploaded, ...current.filter((file) => file.id !== uploaded.id)]);
      showToast(t("files.uploaded", { filename: uploaded.filename }), "success");
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : t("files.uploadError"));
    } finally {
      setUploading(false);
    }
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0];
    event.target.value = "";
    if (!selected) return;
    await uploadSelectedFile(selected);
  }

  function handleDragEnter(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (!event.dataTransfer.types.includes("Files")) return;
    dragCounter.current += 1;
    setDragActive(true);
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    dragCounter.current = Math.max(0, dragCounter.current - 1);
    if (dragCounter.current === 0) {
      setDragActive(false);
    }
  }

  async function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    dragCounter.current = 0;
    setDragActive(false);
    const dropped = event.dataTransfer.files?.[0];
    if (!dropped) return;
    await uploadSelectedFile(dropped);
  }

  async function handleAnalyze(file: FileRecord) {
    if (!tokens?.accessToken) return;
    setActiveFileId(file.id);
    setError(null);
    try {
      const analysis = await analyzeFile(tokens.accessToken, file.id);
      setDialog({
        title: t("files.summaryTitle", { filename: file.filename }),
        status: analysis.status,
        content: analysis.summary ?? t("files.noSummary"),
      });
      showToast(t("files.analysisCompleted", { status: statusLabel(analysis.status, t) }), "success");
      await loadFiles();
    } catch (analyzeError) {
      setError(analyzeError instanceof Error ? analyzeError.message : t("files.analysisError"));
    } finally {
      setActiveFileId(null);
    }
  }

  async function handleShowText(file: FileRecord) {
    if (!tokens?.accessToken) return;
    setActiveFileId(file.id);
    setError(null);
    try {
      const text = await getFileText(tokens.accessToken, file.id);
      setDialog({
        title: t("files.textTitle", { filename: file.filename }),
        status: text.status,
        content: text.extracted_text ?? t("files.noText"),
      });
    } catch (textError) {
      setError(textError instanceof Error ? textError.message : t("files.textError"));
    } finally {
      setActiveFileId(null);
    }
  }

  async function handleShowAnalysis(file: FileRecord) {
    if (!tokens?.accessToken) return;
    setActiveFileId(file.id);
    setError(null);
    try {
      const analysis = await getFileAnalysis(tokens.accessToken, file.id);
      setDialog({
        title: t("files.summaryTitle", { filename: file.filename }),
        status: analysis.status,
        content: analysis.summary ?? t("files.noSummary"),
      });
    } catch (analysisError) {
      setError(analysisError instanceof Error ? analysisError.message : t("files.summaryError"));
    } finally {
      setActiveFileId(null);
    }
  }

  async function handleDownload(file: FileRecord) {
    if (!tokens?.accessToken) return;
    setActiveFileId(file.id);
    setError(null);
    try {
      const url = await getFileDownloadUrl(tokens.accessToken, file.id);
      window.open(url, "_blank", "noopener,noreferrer");
    } catch (downloadError) {
      setError(downloadError instanceof Error ? downloadError.message : t("files.downloadError"));
    } finally {
      setActiveFileId(null);
    }
  }

  function handleDelete(file: FileRecord) {
    if (!tokens?.accessToken) return;
    const accessToken = tokens.accessToken;
    const previousFiles = files;
    setError(null);

    setFiles((current) => current.filter((item) => item.id !== file.id));

    const pending = deferredExecute(async () => {
      try {
        await deleteFile(accessToken, file.id);
      } catch (deleteError) {
        setFiles(previousFiles);
        setError(deleteError instanceof Error ? deleteError.message : t("files.deleteError"));
      }
    });

    showToast(t("files.deleted", { filename: file.filename }), "success", {
      duration: UNDO_WINDOW_MS,
      action: {
        label: t("common.undo"),
        onClick: () => {
          pending.cancel();
          setFiles(previousFiles);
        },
      },
    });
  }

  function startEditing(file: FileRecord) {
    setEditingFileId(file.id);
    setEditingFilename(file.filename);
    setError(null);
  }

  async function handleRenameFile(event: FormEvent<HTMLFormElement>, file: FileRecord) {
    event.preventDefault();
    const filename = editingFilename.trim();
    if (!tokens?.accessToken || !filename) return;

    setActiveFileId(file.id);
    setError(null);
    try {
      const updated = await updateFile(tokens.accessToken, file.id, { filename });
      setFiles((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setEditingFileId(null);
      setEditingFilename("");
      showToast(t("files.renamed"), "success");
    } catch (renameError) {
      setError(renameError instanceof Error ? renameError.message : t("files.renameError"));
    } finally {
      setActiveFileId(null);
    }
  }

  return (
    <div className="p-xl space-y-xl">
      <header className="flex items-start justify-between gap-lg flex-wrap">
        <div>
          <h2 className="font-headline-lg text-headline-lg text-on-surface">{t("files.pageTitle")}</h2>
          <p className="text-body-md text-on-surface-variant mt-1">{t("files.pageSubtitle")}</p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept={acceptedExtensions}
          className="hidden"
          onChange={handleFileChange}
        />
        <button
          type="button"
          disabled={isUploading}
          onClick={() => inputRef.current?.click()}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary rounded-lg font-label-md disabled:opacity-60"
        >
          <span className="material-symbols-outlined text-[18px]">{isUploading ? "hourglass_top" : "upload_file"}</span>
          {isUploading ? t("files.uploading") : t("files.upload")}
        </button>
      </header>

      {error ? <p className="text-error text-body-sm">{error}</p> : null}

      <section className="grid grid-cols-1 md:grid-cols-3 gap-lg">
        <Metric icon="folder" label={t("files.metrics.files")} value={files.length.toString()} />
        <Metric icon="verified" label={t("files.metrics.ready")} value={readyCount.toString()} />
        <Metric icon="database" label={t("files.metrics.size")} value={formatBytes(totalBytes)} />
      </section>

      {files.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[200px]">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[18px]">
              search
            </span>
            <input
              className="w-full bg-surface-container-low border-none rounded-full pl-10 pr-4 py-2 text-body-sm"
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t("files.searchPlaceholder")}
              value={searchQuery}
            />
          </div>
          <select
            className="bg-surface-container-low border-none rounded-lg px-3 py-2 text-body-sm"
            onChange={(e) => setStatusFilter(e.target.value)}
            value={statusFilter}
          >
            <option value="all">{t("files.filterAllStatuses")}</option>
            {availableStatuses.map((status) => (
              <option key={status} value={status}>
                {statusLabel(status, t)}
              </option>
            ))}
          </select>
          <select
            className="bg-surface-container-low border-none rounded-lg px-3 py-2 text-body-sm"
            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            value={sortBy}
          >
            <option value="newest">{t("files.sortNewest")}</option>
            <option value="oldest">{t("files.sortOldest")}</option>
            <option value="name">{t("files.sortName")}</option>
            <option value="size">{t("files.sortSize")}</option>
          </select>
        </div>
      ) : null}

      <section
        className={
          "space-y-md rounded-xl transition-colors " +
          (isDragActive ? "ring-2 ring-primary ring-offset-2 ring-offset-background" : "")
        }
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {isDragActive ? (
          <div className="glass-card p-xl rounded-xl border-2 border-dashed border-primary text-center text-body-md text-primary">
            {t("files.dropHint")}
          </div>
        ) : null}
        {isLoading ? <SkeletonList count={3} /> : null}
        {!isLoading && files.length === 0 ? (
          <div className="glass-card rounded-xl">
            <EmptyState icon="upload_file" size="lg" title={t("files.emptyWithDropHint")} />
          </div>
        ) : null}
        {!isLoading && files.length > 0 && visibleFiles.length === 0 ? (
          <div className="glass-card rounded-xl">
            <EmptyState icon="search_off" title={t("files.noMatches")} />
          </div>
        ) : null}
        {visibleFiles.map((file) => (
          <FileCard
            key={file.id}
            file={file}
            language={language}
            isActive={activeFileId === file.id}
            onAnalyze={() => handleAnalyze(file)}
            onCancelEdit={() => {
              setEditingFileId(null);
              setEditingFilename("");
            }}
            onDelete={() => handleDelete(file)}
            onDownload={() => handleDownload(file)}
            onEdit={() => startEditing(file)}
            onEditingFilenameChange={setEditingFilename}
            onRename={(event) => handleRenameFile(event, file)}
            onShowAnalysis={() => handleShowAnalysis(file)}
            onShowText={() => handleShowText(file)}
            editingFilename={editingFileId === file.id ? editingFilename : null}
          />
        ))}
      </section>

      {dialog ? <TextDialog dialog={dialog} onClose={() => setDialog(null)} /> : null}
    </div>
  );
}

function FileCard({
  file,
  language,
  isActive,
  onAnalyze,
  onCancelEdit,
  onDelete,
  onDownload,
  onEdit,
  onEditingFilenameChange,
  onRename,
  onShowAnalysis,
  onShowText,
  editingFilename,
}: {
  file: FileRecord;
  language: Language;
  isActive: boolean;
  onAnalyze: () => void;
  onCancelEdit: () => void;
  onDelete: () => void;
  onDownload: () => void;
  onEdit: () => void;
  onEditingFilenameChange: (value: string) => void;
  onRename: (event: FormEvent<HTMLFormElement>) => void;
  onShowAnalysis: () => void;
  onShowText: () => void;
  editingFilename: string | null;
}) {
  const { t } = useLanguage();
  return (
    <article className="glass-card p-lg rounded-xl">
      <div className="flex items-start gap-md">
        <div className="w-11 h-11 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
          <span className="material-symbols-outlined">description</span>
        </div>
        <div className="min-w-0 flex-1">
          {editingFilename !== null ? (
            <form onSubmit={onRename} className="flex items-center gap-2">
              <input
                autoFocus
                className="min-w-0 flex-1 bg-surface-container-lowest border border-outline-variant/40 rounded-lg px-3 py-2 text-body-sm"
                onChange={(event) => onEditingFilenameChange(event.target.value)}
                placeholder={t("files.renamePlaceholder")}
                value={editingFilename}
              />
              <button
                type="submit"
                disabled={isActive || !editingFilename.trim()}
                className="w-9 h-9 rounded-lg bg-primary text-on-primary flex items-center justify-center disabled:opacity-60"
                aria-label={t("common.save")}
              >
                <span className="material-symbols-outlined text-[18px]">{isActive ? "hourglass_top" : "check"}</span>
              </button>
              <button
                type="button"
                disabled={isActive}
                onClick={onCancelEdit}
                className="w-9 h-9 rounded-lg border border-outline-variant/40 text-on-surface-variant bg-surface-container-lowest flex items-center justify-center disabled:opacity-60"
                aria-label={t("common.cancel")}
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </form>
          ) : (
            <div className="flex items-center justify-between gap-md">
              <h3 className="font-label-md text-label-md text-on-surface truncate">{file.filename}</h3>
              <span className="px-2 py-0.5 rounded-full bg-surface-container-high text-[11px] font-bold text-on-surface-variant shrink-0">
                {statusLabel(file.status, t)}
              </span>
            </div>
          )}
          <p className="text-body-sm text-on-surface-variant truncate mt-1">{file.mime_type}</p>
          <div className="flex items-center gap-lg mt-3 text-body-sm text-on-surface-variant flex-wrap">
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[16px]">storage</span>
              {formatBytes(file.size_bytes)}
            </span>
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[16px]">schedule</span>
              {formatDateTime(file.created_at, language)}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-lg flex flex-wrap gap-2">
        <ActionButton disabled={isActive} icon="auto_awesome" label={t("files.actions.analyze")} onClick={onAnalyze} primary />
        <ActionButton disabled={isActive} icon="article" label={t("files.actions.text")} onClick={onShowText} />
        <ActionButton disabled={isActive} icon="summarize" label={t("files.actions.summary")} onClick={onShowAnalysis} />
        <ActionButton disabled={isActive} icon="edit" label={t("common.edit")} onClick={onEdit} />
        <ActionButton disabled={isActive} icon="open_in_new" label={t("files.actions.open")} onClick={onDownload} />
        <ActionButton disabled={isActive} icon="delete" label={t("common.delete")} onClick={onDelete} danger />
      </div>
    </article>
  );
}

function ActionButton({
  danger = false,
  disabled,
  icon,
  label,
  onClick,
  primary = false,
}: {
  danger?: boolean;
  disabled: boolean;
  icon: string;
  label: string;
  onClick: () => void;
  primary?: boolean;
}) {
  const className = primary
    ? "bg-primary text-on-primary"
    : danger
      ? "border border-error/30 text-error bg-surface-container-lowest"
      : "border border-outline-variant/40 text-on-surface-variant bg-surface-container-lowest";
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-label-sm font-bold disabled:opacity-60 ${className}`}
    >
      <span className="material-symbols-outlined text-[17px]">{disabled ? "hourglass_top" : icon}</span>
      {label}
    </button>
  );
}

function Metric({ icon, label, value }: { icon: string; label: string; value: string }) {
  return (
    <div className="bg-inverse-surface text-inverse-on-surface rounded-xl p-lg">
      <span className="material-symbols-outlined text-primary-fixed-dim">{icon}</span>
      <p className="text-headline-md font-bold mt-md">{value}</p>
      <p className="text-body-sm text-outline-variant">{label}</p>
    </div>
  );
}

function TextDialog({ dialog, onClose }: { dialog: NonNullable<DialogState>; onClose: () => void }) {
  const { t } = useLanguage();
  return (
    <div className="fixed inset-0 z-[80] bg-black/40 flex items-center justify-center p-xl" role="dialog" aria-modal="true">
      <div className="bg-surface rounded-xl shadow-2xl max-w-3xl w-full max-h-[80vh] flex flex-col">
        <header className="p-lg border-b border-outline-variant/30 flex items-start justify-between gap-md">
          <div>
            <h3 className="font-headline-md text-headline-md">{dialog.title}</h3>
            <span className="inline-flex mt-2 px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[11px] font-bold">
              {statusLabel(dialog.status, t)}
            </span>
          </div>
          <button type="button" onClick={onClose} className="text-on-surface-variant hover:text-on-surface">
            <span className="material-symbols-outlined">close</span>
          </button>
        </header>
        <pre className="p-lg overflow-auto whitespace-pre-wrap text-body-sm text-on-surface leading-relaxed">
          {dialog.content}
        </pre>
      </div>
    </div>
  );
}

function statusLabel(status: string, t: (path: string) => string): string {
  switch (status) {
    case "ready":
      return t("files.status.ready");
    case "processing":
      return t("files.status.processing");
    case "failed":
      return t("files.status.failed");
    case "uploaded":
      return t("files.status.uploaded");
    case "extracted":
      return t("files.status.extracted");
    case "unsupported":
      return t("files.status.unsupported");
    case "completed":
      return t("files.status.completed");
    default:
      return t("files.status.unknown");
  }
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
