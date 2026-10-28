"use client";

import { useState } from "react";
import { formatDate } from "@/lib/utils";
import type { Timeline, TimelineEvent } from "@/types";

const TYPE_STYLES: Record<string, string> = {
  filing: "bg-accent text-white",
  hearing: "bg-ink-soft text-white",
  judgment: "bg-danger text-white",
  order: "bg-ink-soft text-white",
  incident: "bg-slate text-white",
  other: "bg-line text-ink",
};

function EventCard({ event }: { event: TimelineEvent }) {
  const [open, setOpen] = useState(false);
  const badge = TYPE_STYLES[event.type] || TYPE_STYLES.other;

  return (
    <li className="relative pl-8">
      <span className="absolute left-[7px] top-2 h-3 w-3 rounded-full border-2 border-accent bg-white" />
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="w-full [overflow-wrap:anywhere] border border-line bg-white p-4 text-left transition hover:border-accent"
      >
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-[family-name:var(--font-display)] text-sm font-semibold text-ink">
            {event.date ? formatDate(event.date) : "Date not stated"}
          </span>
          <span className={`px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${badge}`}>
            {event.type}
          </span>
        </div>
        <p className={`mt-2 text-sm leading-relaxed text-slate ${open ? "" : "line-clamp-3"}`}>{event.description}</p>
        <p className="mt-2 text-xs text-muted">
          {event.source_document}{event.document_type !== "docx" && event.page_number != null ? ` · Page ${event.page_number}` : ""}
        </p>
        <span className="mt-2 inline-block text-xs font-medium text-accent">{open ? "Hide details" : "View details"}</span>
        {open && (
          <div className="mt-3 border-t border-line pt-3 text-xs text-muted space-y-1">
            <p>
              Source: <span className="text-ink">{event.source_document}</span>
            </p>
            <p>
              Type: <span className="text-ink">{event.document_type}</span>
              {event.document_type !== "docx" && event.page_number != null ? ` · Page ${event.page_number}` : ""}
            </p>

          </div>
        )}
      </button>
    </li>
  );
}

export function TimelineView({ timeline }: { timeline: Timeline | null }) {
  if (!timeline || timeline.events.length === 0) {
    return (
      <div className="border border-dashed border-line bg-white/70 p-5">
        <h2 className="text-lg font-semibold text-ink">Timeline</h2>
        <p className="mt-2 text-sm text-muted">
          Chronological events appear here after documents are extracted.
        </p>
      </div>
    );
  }

  const dated = timeline.events.filter((event) => event.date);
  const undated = timeline.events.filter((event) => !event.date);

  return (
    <div className="min-w-0 border border-line bg-white p-5 animate-fade-up">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold text-ink">Timeline</h2>
        <p className="text-xs text-muted">
          {timeline.events.length} event{timeline.events.length === 1 ? "" : "s"}
          {timeline.last_updated
            ? ` · Updated ${new Date(timeline.last_updated).toLocaleString("en-IN")}`
            : ""}
        </p>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-muted">
        {dated.length} dated event{dated.length === 1 ? "" : "s"} · Select an event to review its source.
      </p>
      <div className="mt-5 max-h-[44rem] overflow-y-auto overscroll-contain pr-2" tabIndex={0} role="region" aria-label="Case timeline events">
        {dated.length > 0 ? (
          <ol className="relative space-y-4 before:absolute before:left-[12px] before:top-1 before:bottom-1 before:w-px before:bg-line">
            {dated.map((event, idx) => (
              <EventCard key={`${event.date}-${event.document_id}-${idx}`} event={event} />
            ))}
          </ol>
        ) : (
          <p className="text-sm text-muted">No reliable dates were found. Review the source documents or re-run extraction.</p>
        )}
        {undated.length > 0 && (
          <details className="mt-5 border-t border-line pt-4">
            <summary className="cursor-pointer text-sm font-medium text-slate">
              Dates need review ({undated.length})
            </summary>
            <p className="mt-2 text-xs text-muted">These mentions have no reliable date and are excluded from the chronology.</p>
            <ol className="mt-4 space-y-4">
              {undated.map((event, idx) => (
                <EventCard key={`undated-${event.document_id}-${idx}`} event={event} />
              ))}
            </ol>
          </details>
        )}
      </div>
    </div>
  );
}
