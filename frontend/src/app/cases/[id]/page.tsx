"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Nav } from "@/components/Nav";
import { AuthGuard } from "@/components/AuthGuard";
import { ApiError, api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { Case } from "@/types";

const MODULES = [
  {
    title: "Timeline",
    blurb: "Chronological events extracted across documents.",
    phase: "Phase 2",
  },
  {
    title: "Legal research",
    blurb: "Cited answers from Indian statutes (IPC, CrPC, and more).",
    phase: "Phase 3",
  },
  {
    title: "Contradiction detection",
    blurb: "Cross-document inconsistency flags for lawyer review.",
    phase: "Phase 4",
  },
  {
    title: "Evidence integrity",
    blurb: "SHA-256 chain-of-custody and tamper verification.",
    phase: "Phase 5",
  },
];

export default function CaseDetailPage() {
  return (
    <AuthGuard>
      <CaseDetailInner />
    </AuthGuard>
  );
}

function CaseDetailInner() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!caseId) return;
    api
      .getCase(caseId)
      .then(setCaseData)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load case"),
      );
  }, [caseId]);

  return (
    <>
      <Nav />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6">
        <Link href="/dashboard" className="text-sm text-muted hover:text-accent">
          ← Back to cases
        </Link>

        {error && (
          <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-danger">{error}</p>
        )}

        {!caseData && !error && (
          <p className="mt-8 text-sm text-muted">Loading case…</p>
        )}

        {caseData && (
          <>
            <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-accent">
                  {caseData.case_type}
                </p>
                <h1 className="font-[family-name:var(--font-display)] text-4xl text-ink">
                  {caseData.title}
                </h1>
                <p className="mt-2 max-w-2xl text-sm text-slate">
                  {caseData.description || "No description"}
                </p>
                <p className="mt-2 text-xs text-muted">
                  {caseData.document_count} documents · Opened{" "}
                  {formatDate(caseData.created_at)}
                </p>
              </div>
              <Link
                href={`/cases/${caseId}/upload`}
                className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-hover"
              >
                Upload documents
              </Link>
            </div>

            <section className="mt-8 border border-line bg-white p-6">
              <h2 className="text-lg font-semibold text-ink">Documents</h2>
              <p className="mt-1 text-sm text-muted">
                {caseData.document_count === 0
                  ? "No files yet. Upload PDFs, DOCX, or images to start building this case."
                  : `${caseData.document_count} file${caseData.document_count === 1 ? "" : "s"} attached to this case.`}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Link
                  href={`/cases/${caseId}/upload`}
                  className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-hover"
                >
                  {caseData.document_count === 0 ? "Upload files" : "Manage uploads"}
                </Link>
              </div>
            </section>

            <section className="mt-10">
              <h2 className="text-lg font-semibold text-ink">Intelligence modules</h2>
              <p className="mt-1 text-sm text-muted">
                Placeholders for upcoming phases — upload documents to prepare the case.
              </p>
              <ul className="mt-6 grid gap-4 sm:grid-cols-2">
                {MODULES.map((m) => (
                  <li
                    key={m.title}
                    className="border border-dashed border-line bg-white/70 p-5"
                  >
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-ink">{m.title}</h3>
                      <span className="text-xs text-muted">{m.phase}</span>
                    </div>
                    <p className="mt-2 text-sm text-slate">{m.blurb}</p>
                    <p className="mt-4 text-xs font-medium text-muted">Coming soon</p>
                  </li>
                ))}
              </ul>
            </section>
          </>
        )}
      </main>
    </>
  );
}
