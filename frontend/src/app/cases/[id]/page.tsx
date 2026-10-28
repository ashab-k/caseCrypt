"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { Nav } from "@/components/Nav";
import { AuthGuard } from "@/components/AuthGuard";
import { EntitiesPanel } from "@/components/extraction/EntitiesPanel";
import { KnowledgeGraph } from "@/components/timeline/KnowledgeGraph";
import { TimelineView } from "@/components/timeline/TimelineView";
import { ApiError, api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type {
  Case,
  CaseDocument,
  CaseEntities,
  KnowledgeGraph as KnowledgeGraphData,
  Timeline,
} from "@/types";

const LATER_MODULES = [
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
  const [docs, setDocs] = useState<CaseDocument[]>([]);
  const [entities, setEntities] = useState<CaseEntities | null>(null);
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [graph, setGraph] = useState<KnowledgeGraphData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [extractNote, setExtractNote] = useState<string | null>(null);

  const loadIntelligence = useCallback(async (id: string) => {
    const [ents, tl, kg] = await Promise.all([
      api.getEntities(id),
      api.getTimeline(id),
      api.getKnowledgeGraph(id),
    ]);
    setEntities(ents);
    setTimeline(tl);
    setGraph(kg);
  }, []);

  useEffect(() => {
    if (!caseId) return;
    Promise.all([api.getCase(caseId), api.listDocuments(caseId)])
      .then(async ([c, d]) => {
        setCaseData(c);
        setDocs(d);
        await loadIntelligence(caseId);
      })
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load case"),
      );
  }, [caseId, loadIntelligence]);

  async function runExtraction(force = false) {
    if (!caseId) return;
    setExtracting(true);
    setError(null);
    setExtractNote(null);
    try {
      const result = await api.extractCase(caseId, force);
      setExtractNote(
        `Processed ${result.processed}, skipped ${result.skipped} already extracted.`,
      );
      const refreshed = await api.listDocuments(caseId);
      setDocs(refreshed);
      await loadIntelligence(caseId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Extraction failed");
    } finally {
      setExtracting(false);
    }
  }

  const unextracted = docs.filter((d) => !d.extracted).length;

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
                <h1 className="font-[family-name:var(--font-display)] text-4xl text-ink [overflow-wrap:anywhere]">
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
              <div className="flex flex-wrap gap-2">
                <Link
                  href={`/cases/${caseId}/upload`}
                  className="rounded-md border border-line bg-white px-4 py-2 text-sm font-semibold text-ink hover:border-accent"
                >
                  Upload documents
                </Link>
                <button
                  type="button"
                  disabled={extracting || docs.length === 0}
                  onClick={() => runExtraction(false)}
                  className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-hover disabled:opacity-50"
                >
                  {extracting ? "Extracting…" : "Run extraction"}
                </button>
              </div>
            </div>

            {extractNote && (
              <p className="mt-4 text-sm text-accent">{extractNote}</p>
            )}

            <section className="mt-8 border border-line bg-white p-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-ink">Documents</h2>
                  <p className="mt-1 text-sm text-muted">
                    {docs.length === 0
                      ? "No files yet. Upload PDFs, DOCX, or images to start building this case."
                      : `${docs.length} file${docs.length === 1 ? "" : "s"} · ${unextracted} pending extraction`}
                  </p>
                </div>
                {docs.some((d) => d.extracted) && (
                  <button
                    type="button"
                    disabled={extracting}
                    onClick={() => runExtraction(true)}
                    className="text-sm text-muted underline-offset-2 hover:text-accent hover:underline disabled:opacity-50"
                  >
                    Re-run all
                  </button>
                )}
              </div>
              {docs.length > 0 && (
                <ul className="mt-4 divide-y divide-line border border-line">
                  {docs.map((doc) => (
                    <li
                      key={doc.id}
                      className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-sm"
                    >
                      <span className="min-w-0 [overflow-wrap:anywhere] text-ink">{doc.original_name}</span>
                      <span
                        className={
                          doc.extracted
                            ? "text-xs font-medium text-accent"
                            : "text-xs font-medium text-muted"
                        }
                      >
                        {doc.extracted ? "Extracted" : "Pending"}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="mt-10 space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-ink">Document intelligence</h2>
                <p className="mt-1 text-sm text-muted">
                  OCR, parties, timeline, and entity graph for this case.
                </p>
              </div>
              <div className="grid items-start gap-6 lg:grid-cols-2">
                <div className="min-w-0 space-y-6">
                  <EntitiesPanel entities={entities} />
                  <KnowledgeGraph graph={graph} />
                </div>
                <TimelineView timeline={timeline} />
              </div>
            </section>

            <section className="mt-10">
              <h2 className="text-lg font-semibold text-ink">Upcoming modules</h2>
              <ul className="mt-6 grid gap-4 sm:grid-cols-3">
                {LATER_MODULES.map((m) => (
                  <li
                    key={m.title}
                    className="border border-dashed border-line bg-white/70 p-5"
                  >
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-ink">{m.title}</h3>
                      <span className="text-xs text-muted">{m.phase}</span>
                    </div>
                    <p className="mt-2 text-sm text-slate">{m.blurb}</p>
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
