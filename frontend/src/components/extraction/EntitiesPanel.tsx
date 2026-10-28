"use client";

import { useState } from "react";
import { formatDate } from "@/lib/utils";
import type { CaseEntities } from "@/types";

function TagGroup({
  title,
  items,
  empty,
}: {
  title: string;
  items: string[];
  empty: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const visibleItems = expanded ? items : items.slice(0, 8);
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">
        {title}
      </h3>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-muted">{empty}</p>
      ) : (
        <ul className="mt-2 flex flex-wrap gap-2">
          {visibleItems.map((item, index) => (
            <li
              key={`${title}-${item}-${index}`}
              className="border border-line max-w-full [overflow-wrap:anywhere] bg-accent-soft/60 px-2.5 py-1 text-sm text-ink"
            >
              {item}
            </li>
          ))}
        </ul>
      )}
      {items.length > 8 && (
        <button type="button" onClick={() => setExpanded((value) => !value)}
          aria-expanded={expanded}
          className="mt-2 text-xs font-medium text-accent hover:underline">
          {expanded ? "Show fewer" : `Show all ${items.length}`}
        </button>
      )}
    </div>
  );
}

export function EntitiesPanel({ entities }: { entities: CaseEntities | null }) {
  if (!entities || entities.document_count_extracted === 0) {
    return (
      <div className="border border-dashed border-line bg-white/70 p-5">
        <h2 className="text-lg font-semibold text-ink">Entities</h2>
        <p className="mt-2 text-sm text-muted">
          Run extraction to pull parties, dates, and cited provisions from case
          documents.
        </p>
      </div>
    );
  }

  const partyTags = [
    ...entities.parties.petitioner.map((n) => `Petitioner: ${n}`),
    ...entities.parties.respondent.map((n) => `Respondent: ${n}`),
    ...entities.parties.counsel.map((n) => `Counsel: ${n}`),
  ];

  const provisionTags = entities.cited_provisions.map((p) =>
    p.act === "Unknown" ? `Section ${p.section} · act not identified` : `${p.act} §${p.section}`.trim(),
  );

  const dateTags = Array.from(new Set(entities.dates.map((d) => formatDate(d.date))));

  return (
    <div className="min-w-0 border border-line bg-white p-5 animate-fade-in">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Entities</h2>
        <p className="text-xs text-muted">
          From {entities.document_count_extracted} extracted document
          {entities.document_count_extracted === 1 ? "" : "s"}
        </p>
      </div>
      {entities.extraction_methods?.includes("heuristic") && (
        <p className="mt-3 rounded-md bg-paper px-3 py-2 text-xs leading-relaxed text-slate">
          Pattern-based extraction used. Review names, dates, and provisions against the source documents.
        </p>
      )}
      <div className="mt-5 space-y-5">
        <TagGroup title="Parties" items={partyTags} empty="No parties found" />
        <TagGroup
          title="Cited provisions"
          items={provisionTags}
          empty="No statutory citations found"
        />
        <TagGroup title="Key dates" items={dateTags} empty="No dates found" />
        {entities.claims.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">
              Claims
            </h3>
            <ul className="mt-2 space-y-2">
              {entities.claims.slice(0, 6).map((claim) => (
                <li key={claim} className="text-sm text-slate leading-relaxed">
                  {claim}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
