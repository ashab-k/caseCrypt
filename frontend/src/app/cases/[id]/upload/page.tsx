"use client";

import Link from "next/link";
import { DragEvent, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Nav } from "@/components/Nav";
import { AuthGuard } from "@/components/AuthGuard";
import { ApiError, api } from "@/lib/api";
import { formatBytes, formatDate } from "@/lib/utils";
import type { Case, CaseDocument } from "@/types";

const ACCEPT = ".pdf,.docx,.jpg,.jpeg,.png";

export default function UploadPage() {
  return (
    <AuthGuard>
      <UploadInner />
    </AuthGuard>
  );
}

function UploadInner() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;
  const uploadInProgress = useRef(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [docs, setDocs] = useState<CaseDocument[]>([]);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([api.getCase(caseId), api.listDocuments(caseId)])
      .then(([c, d]) => {
        if (!active) return;
        setCaseData(c);
        setDocs(d);
      })
      .catch((err) => {
        if (active) setError(err instanceof ApiError ? err.message : "Failed to load");
      });
    return () => {
      active = false;
    };
  }, [caseId]);

  async function handleFiles(files: FileList | File[]) {
    const list = Array.from(files);
    if (!list.length || !caseId || uploadInProgress.current) return;
    if (list.some((file) => !/\.(pdf|docx|jpe?g|png)$/i.test(file.name))) {
      setError("Choose PDF, DOCX, JPG, or PNG files.");
      if (inputRef.current) inputRef.current.value = "";
      return;
    }
    uploadInProgress.current = true;
    setUploading(true);
    setError(null);
    try {
      const uploaded = await api.uploadDocuments(caseId, list);
      setDocs((prev) => [...uploaded, ...prev]);
      setCaseData((prev) =>
        prev
          ? { ...prev, document_count: prev.document_count + uploaded.length }
          : prev,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      uploadInProgress.current = false;
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files?.length) handleFiles(e.dataTransfer.files);
  }

  async function onDelete(docId: string) {
    if (!caseId || !confirm("Delete this document?")) return;
    try {
      await api.deleteDocument(caseId, docId);
      setDocs((prev) => prev.filter((d) => d.id !== docId));
      setCaseData((prev) =>
        prev
          ? { ...prev, document_count: Math.max(0, prev.document_count - 1) }
          : prev,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Delete failed");
    }
  }

  return (
    <>
      <Nav />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6">
        <Link
          href={`/cases/${caseId}`}
          className="text-sm text-muted hover:text-accent"
        >
          ← Back to case
        </Link>

        <h1 className="mt-4 font-[family-name:var(--font-display)] text-4xl text-ink">
          Upload documents
        </h1>
        <p className="mt-1 text-sm text-muted">
          {caseData ? caseData.title : "…"} — PDF, DOCX, JPG, PNG
        </p>

        {error && (
          <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-danger">{error}</p>
        )}

        <div
          onDragOver={(e) => {
            e.preventDefault();
            if (!uploading) setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          role="button"
          tabIndex={uploading ? -1 : 0}
          aria-label="Choose documents to upload"
          aria-disabled={uploading}
          aria-busy={uploading}
          onClick={() => { if (!uploading) inputRef.current?.click(); }}
          onKeyDown={(e) => {
            if (e.target !== e.currentTarget) return;
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              if (!uploading) inputRef.current?.click();
            }
          }}
          className={`mt-8 cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 border-2 border-dashed px-6 py-16 text-center transition ${
            dragging
              ? "border-accent bg-accent-soft/40"
              : "border-line bg-white hover:border-accent/50"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            disabled={uploading}
            accept={ACCEPT}
            className="hidden"
            onChange={(e) => e.target.files && handleFiles(e.target.files)}
          />
          <p className="text-base font-medium text-ink">
            {uploading ? "Uploading…" : "Drop files here or click to browse"}
          </p>
          <p className="mt-2 text-sm text-muted">
            Files are stored per case and SHA-256 hashed on upload.
          </p>
        </div>

        {docs.length > 0 && (
          <p className="mt-6 text-sm text-slate">
            Next:{" "}
            <Link href={`/cases/${caseId}`} className="font-semibold text-accent hover:underline">
              open the case
            </Link>{" "}
            and run extraction to build the timeline and entity graph.
          </p>
        )}

        <section className="mt-10">
          <h2 className="text-lg font-semibold text-ink">
            Documents ({docs.length})
          </h2>
          {docs.length === 0 ? (
            <p className="mt-3 text-sm text-muted">No documents uploaded yet.</p>
          ) : (
            <ul className="mt-4 divide-y divide-line border border-line bg-white">
              {docs.map((d) => (
                <li
                  key={d.id}
                  className="flex flex-wrap items-center justify-between gap-3 px-4 py-3"
                >
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-ink [overflow-wrap:anywhere]">{d.original_name}</p>
                    <p className="text-xs text-muted">
                      {d.file_type.toUpperCase()} · {formatBytes(d.file_size)} ·{" "}
                      {formatDate(d.uploaded_at)}
                      {" · "}
                      <span className={d.extracted ? "text-accent" : ""}>
                        {d.extracted ? "Extracted" : "Pending extraction"}
                      </span>
                    </p>
                    <p className="mt-0.5 font-mono text-[10px] text-muted break-all">
                      sha256:{d.sha256.slice(0, 16)}…
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => onDelete(d.id)}
                    className="text-xs text-muted hover:text-danger"
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </>
  );
}
