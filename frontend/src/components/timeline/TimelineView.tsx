"use client";

import { useState } from "react";
import type { Timeline, TimelineEvent } from "@/types";

const TYPE_STYLES: Record<string, string> = {
  filing: "bg-accent text-white",
  hearing: "bg-ink-soft text-white",
  judgment: "bg-danger text-white",
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
        className="w-full border border-line bg-white p-4 text-left transition hover:border-accent"
      >
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-[family-name:var(--font-display)] text-sm font-semibold text-ink">
            {event.date || "Undated"}
          </span>
          <span className={`px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${badge}`}>
            {event.type}
          </span>
        </div>
        <p className="mt-2 text-sm text-slate line-clamp-2">{event.description}</p>
        {open && (
          <div className="mt-3 border-t border-line pt-3 text-xs text-muted space-y-1">
            <p>
              Source: <span className="text-ink">{event.source_document}</span>
            </p>
            <p>
              Type: <span className="text-ink">{event.document_type}</span>
              {event.page_number != null ? ` · Page ${event.page_number}` : ""}
            </p>
            <p className="text-sm text-slate leading-relaxed">{event.description}</p>
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

  return (
    <div className="border border-line bg-white p-5 animate-fade-up">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold text-ink">Timeline</h2>
        <p className="text-xs text-muted">
          {timeline.events.length} event{timeline.events.length === 1 ? "" : "s"}
          {timeline.last_updated
            ? ` · Updated ${new Date(timeline.last_updated).toLocaleString("en-IN")}`
            : ""}
        </p>
      </div>
      <ol className="relative mt-6 space-y-4 before:absolute before:left-[12px] before:top-1 before:bottom-1 before:w-px before:bg-line">
        {timeline.events.map((event, idx) => (
          <EventCard
            key={`${event.date}-${event.source_document}-${idx}`}
            event={event}
          />
        ))}
      </ol>
    </div>
  );
}
