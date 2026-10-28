"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Nav } from "@/components/Nav";
import { AuthGuard } from "@/components/AuthGuard";
import { ApiError, api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { Case, CaseType } from "@/types";

const CASE_TYPES: CaseType[] = ["criminal", "civil", "contract", "other"];

export default function DashboardPage() {
  return (
    <AuthGuard>
      <DashboardInner />
    </AuthGuard>
  );
}

function DashboardInner() {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [caseType, setCaseType] = useState<CaseType>("other");
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setCases(await api.listCases());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load cases");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await api.createCase({
        title,
        description,
        case_type: caseType,
      });
      setCases((prev) => [created, ...prev]);
      setShowCreate(false);
      setTitle("");
      setDescription("");
      setCaseType("other");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create case");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(id: string) {
    if (!confirm("Delete this case and all of its documents?")) return;
    try {
      await api.deleteCase(id);
      setCases((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Delete failed");
    }
  }

  return (
    <>
      <Nav />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="font-[family-name:var(--font-display)] text-4xl text-ink">
              Your cases
            </h1>
            <p className="mt-1 text-sm text-muted">
              Create a matter, upload files, and open module workspaces.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowCreate(true)}
            className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-hover"
          >
            New case
          </button>
        </div>

        {error && (
          <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-danger">{error}</p>
        )}

        {showCreate && (
          <form
            onSubmit={onCreate}
            className="animate-fade-in mt-8 border border-line bg-white p-6"
          >
            <h2 className="text-lg font-semibold text-ink">Create case</h2>
            <label className="mt-4 block text-sm font-medium">
              Title
              <input
                required
                minLength={3}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="mt-1.5 w-full rounded-md border border-line bg-paper px-3 py-2 outline-none focus:border-accent"
              />
            </label>
            <label className="mt-3 block text-sm font-medium">
              Description
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="mt-1.5 w-full rounded-md border border-line bg-paper px-3 py-2 outline-none focus:border-accent"
              />
            </label>
            <label className="mt-3 block text-sm font-medium">
              Type
              <select
                value={caseType}
                onChange={(e) => setCaseType(e.target.value as CaseType)}
                className="mt-1.5 w-full rounded-md border border-line bg-paper px-3 py-2 outline-none focus:border-accent"
              >
                {CASE_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </option>
                ))}
              </select>
            </label>
            <div className="mt-4 flex gap-2">
              <button
                type="submit"
                disabled={saving}
                className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-hover disabled:opacity-60"
              >
                {saving ? "Saving…" : "Create"}
              </button>
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="rounded-md border border-line px-4 py-2 text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {loading ? (
          <p className="mt-10 text-sm text-muted">Loading cases…</p>
        ) : cases.length === 0 ? (
          <p className="mt-10 text-sm text-muted">
            No cases yet. Create one to get started.
          </p>
        ) : (
          <ul className="mt-8 grid gap-4 sm:grid-cols-2">
            {cases.map((c) => (
              <li
                key={c.id}
                className="animate-fade-up group relative border border-line bg-white transition hover:border-accent/50 hover:bg-accent-soft/20"
              >
                <Link
                  href={`/cases/${c.id}`}
                  className="block p-5 outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset sm:pr-28"
                  aria-label={`Open case ${c.title}`}
                >
                  <p className="text-xs font-medium uppercase tracking-wide text-accent">
                    {c.case_type}
                  </p>
                  <h2 className="mt-1 font-[family-name:var(--font-display)] text-xl text-ink [overflow-wrap:anywhere] group-hover:text-accent">
                    {c.title}
                  </h2>
                  <p className="mt-2 line-clamp-2 text-sm text-slate [overflow-wrap:anywhere]">
                    {c.description || "No description"}
                  </p>
                  <p className="mt-4 text-xs text-muted">
                    {c.document_count} document{c.document_count === 1 ? "" : "s"} ·{" "}
                    {formatDate(c.created_at)}
                  </p>
                </Link>

                <div className="flex gap-2 border-t border-line px-5 py-3 sm:absolute sm:right-3 sm:top-3 sm:z-10 sm:flex-col sm:items-stretch sm:border-0 sm:p-0">
                  <Link
                    href={`/cases/${c.id}/upload`}
                    className="flex-1 rounded-md bg-accent px-3 py-2 text-center text-xs font-semibold text-white hover:bg-accent-hover sm:flex-none sm:py-1.5"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Upload
                  </Link>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      onDelete(c.id);
                    }}
                    className="flex-1 rounded-md px-3 py-2 text-xs text-muted hover:bg-red-50 hover:text-danger sm:flex-none sm:py-1.5"
                  >
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </main>
    </>
  );
}
