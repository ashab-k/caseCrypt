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
  const inputRef = useRef<HTMLInputElement>(null);
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [docs, setDocs] = useState<CaseDocument[]>([]);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    if (!caseId) return;
    const [c, d] = await Promise.all([
      api.getCase(caseId),
      api.listDocuments(caseId),
    ]);
    setCaseData(c);
    setDocs(d);
  }

  useEffect(() => {
    refresh().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Failed to load"),
    );
  }, [caseId]);

  async function handleFiles(files: FileList | File[]) {
    const list = Array.from(files);
    if (!list.length || !caseId) return;
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
      setUploading(false);
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
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`mt-8 cursor-pointer border-2 border-dashed px-6 py-16 text-center transition ${
            dragging
              ? "border-accent bg-accent-soft/40"
              : "border-line bg-white hover:border-accent/50"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            multiple
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
                  <div>
                    <p className="font-medium text-ink">{d.original_name}</p>
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
