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
                className="animate-fade-up border border-line bg-white p-5 transition hover:border-accent/40"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-accent">
                      {c.case_type}
                    </p>
                    <Link
                      href={`/cases/${c.id}`}
                      className="mt-1 block font-[family-name:var(--font-display)] text-xl text-ink hover:text-accent"
                    >
                      {c.title}
                    </Link>
                    <p className="mt-2 line-clamp-2 text-sm text-slate">
                      {c.description || "No description"}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => onDelete(c.id)}
                    className="text-xs text-muted hover:text-danger"
                  >
                    Delete
                  </button>
                </div>
                <div className="mt-4 flex items-center justify-between text-xs text-muted">
                  <span>{c.document_count} document{c.document_count === 1 ? "" : "s"}</span>
                  <span>{formatDate(c.created_at)}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </main>
    </>
  );
}
