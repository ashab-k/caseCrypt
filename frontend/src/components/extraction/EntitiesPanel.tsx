"use client";

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
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">
        {title}
      </h3>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-muted">{empty}</p>
      ) : (
        <ul className="mt-2 flex flex-wrap gap-2">
          {items.map((item) => (
            <li
              key={`${title}-${item}`}
              className="border border-line bg-accent-soft/60 px-2.5 py-1 text-sm text-ink"
            >
              {item}
            </li>
          ))}
        </ul>
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
    `${p.act} §${p.section}`.trim(),
  );

  const dateTags = entities.dates.map((d) =>
    d.event ? `${d.date} — ${d.event.slice(0, 60)}` : d.date,
  );

  return (
    <div className="border border-line bg-white p-5 animate-fade-in">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">Entities</h2>
        <p className="text-xs text-muted">
          From {entities.document_count_extracted} extracted document
          {entities.document_count_extracted === 1 ? "" : "s"}
        </p>
      </div>
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
