"use client";

import Link from 'next/link';
import { FormEvent, useEffect, useRef, useState } from 'react';
import { AuthGuard } from '@/components/AuthGuard';
import { Nav } from '@/components/Nav';
import { ApiError, api } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import type { CorpusStatus, ResearchAct, ResearchAnswer } from '@/types';

const ACTS: ResearchAct[] = ['IPC', 'CrPC', 'Constitution', 'Evidence Act', 'IT Act'];
const EXAMPLES = ['What is Section 302 IPC?', 'What does Article 21 of the Constitution protect?', 'What is Section 65B of the Evidence Act?'];
type Entry = {question: string; act?: ResearchAct; result: ResearchAnswer};

export default function ResearchPage() {
  return <AuthGuard><ResearchWorkspace /></AuthGuard>;
}

function ResearchWorkspace() {
  const [status, setStatus] = useState<CorpusStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [question, setQuestion] = useState('');
  const [act, setAct] = useState<ResearchAct | ''>('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [active, setActive] = useState(0);
  const [submitted, setSubmitted] = useState<string | null>(null);
  const busy = useRef(false);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    api.corpusStatus().then((value) => {if (mounted.current) setStatus(value);})
      .catch((err) => {if (mounted.current) setStatusError(err instanceof ApiError ? err.message : 'Could not check corpus availability.');});
    return () => { mounted.current = false; };
  }, []);

  async function ask(e: FormEvent) {
    e.preventDefault();
    const text = question.trim();
    if (busy.current || text.length < 3) return;
    busy.current = true;
    setPending(true); setError(null); setSubmitted(text);
    try {
      const result = await api.research(text, act || undefined);
      if (!mounted.current) return;
      setEntries((previous) => [{question: text, act: act || undefined, result}, ...previous].slice(0, 10));
      setActive(0);
    } catch (err) {
      if (mounted.current) setError(err instanceof ApiError ? err.message : 'Research failed. Check the API connection and try again.');
    } finally {
      busy.current = false;
      if (mounted.current) setPending(false);
    }
  }

  const entry = entries[active];
  return <>
    <Nav />
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 sm:py-10">
      <Link href="/dashboard" className="text-sm text-muted hover:text-accent">← Back to cases</Link>
      <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
        <div><p className="text-xs font-semibold uppercase tracking-widest text-accent">Public statute library</p>
          <h1 className="mt-1 font-[family-name:var(--font-display)] text-4xl text-ink">Legal research</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate">Ask a question, inspect the cited passages, and open the official source. Research searches the public corpus only.</p>
        </div>
        <span className="border border-line bg-white px-3 py-1.5 text-xs text-slate">
          {status ? `${status.total_chunks.toLocaleString('en-IN')} indexed passages` : statusError ? 'Corpus status unavailable' : 'Checking corpus…'}
        </span>
      </div>
      <p className="mt-5 border-l-2 border-accent bg-accent-soft/50 px-4 py-3 text-xs leading-relaxed text-slate">
        Static statute snapshots for lawyer review. IPC, CrPC, and the Evidence Act are historical texts; replacement criminal laws effective from July 2024 are outside this library. Verify applicability and amendments in the official source.
      </p>
      {statusError && <p role="alert" className="mt-4 text-sm text-danger">{statusError}</p>}
      {status && !status.seeded && <div className="mt-4 border border-line bg-white p-4 text-sm text-slate">
        <p className="font-semibold text-ink">The statute library has not been indexed yet.</p>
        <p className="mt-1">Research will be available once the corpus is seeded. Your case documents are unaffected.</p>
      </div>}
      {status?.seeded && !status.complete && <p className="mt-4 text-sm text-slate">Partial library: some acts have no indexed passages. Check coverage below before relying on a search.</p>}
      <div className="mt-6 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_16rem]">
        <div className="min-w-0">
          <form onSubmit={ask} className="border border-line bg-white p-5 sm:p-6" aria-busy={pending}>
            <label htmlFor="research-question" className="text-sm font-semibold text-ink">Your question</label>
            <textarea id="research-question" value={question} onChange={(e) => setQuestion(e.target.value)}
              required minLength={3} maxLength={2000} rows={3} placeholder="For example, what is Section 302 IPC?"
              className="mt-2 w-full resize-y rounded-md border border-line bg-paper px-3 py-2 text-sm outline-none focus:border-accent" />
            <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
              <label className="flex flex-col gap-1.5 text-xs font-medium text-slate">Limit to an act
                <select value={act} onChange={(e) => setAct(e.target.value as ResearchAct | '')}
                  className="rounded-md border border-line bg-white px-3 py-2 text-sm text-ink">
                  <option value="">All indexed acts</option>{ACTS.map((name) => <option key={name}>{name}</option>)}
                </select>
              </label>
              <button type="submit" disabled={pending || question.trim().length < 3 || status?.seeded === false}
                className="rounded-md bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50">
                {pending ? 'Researching…' : 'Find cited answer'}
              </button>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-muted">
              {status?.generation_available ? 'AI synthesis is enabled: your question and public statute excerpts are sent to OpenAI. Do not paste confidential case material.' : 'Source excerpts mode. Enter a public-law question; case documents are not searched.'}
            </p>
          </form>
          {!entry && !pending && <div className="mt-4 flex flex-wrap gap-2">{EXAMPLES.map((example) =>
            <button key={example} type="button" onClick={() => {setQuestion(example); setAct('');}}
              className="max-w-full rounded-md border border-line px-3 py-2 text-left text-xs text-slate hover:border-accent hover:text-accent">{example}</button>)}
          </div>}
          {pending && <p role="status" className="mt-5 text-sm text-muted">Finding statute passages for “{submitted}”…</p>}
          {error && <p role="alert" className="mt-5 rounded-md bg-red-50 p-4 text-sm text-danger">{error}</p>}
          {entry && !pending && <section className="mt-6 min-w-0 space-y-4" aria-label="Research result">
            <h2 className="font-[family-name:var(--font-display)] text-xl [overflow-wrap:anywhere]">{entry.question}</h2>
            <div className="border border-line bg-white p-5 sm:p-6">
              <div className="flex flex-wrap gap-2 text-xs text-muted">
                <span className="rounded bg-paper px-2 py-1">{entry.result.generation_mode === 'openai' ? 'AI synthesis' : entry.result.generation_mode === 'extractive' ? 'Source excerpts' : 'Insufficient support'}</span>
                <span className="rounded bg-paper px-2 py-1">{entry.result.retrieval_mode}</span>
                <span className="rounded bg-paper px-2 py-1">Retrieval match: {entry.result.confidence}</span>
              </div>
              <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate [overflow-wrap:anywhere]">{entry.result.answer}</p>
              <p className="mt-5 border-t border-line pt-3 text-xs leading-relaxed text-muted">{entry.result.notice}</p>
            </div>
            {entry.result.sources.length > 0 && <div><h3 className="text-sm font-semibold">Sources ({entry.result.sources.length})</h3>
              <div className="mt-3 space-y-3">{entry.result.sources.map((source) => <details key={source.id} className="border border-line bg-white p-4">
                <summary className="cursor-pointer text-sm font-medium text-ink [overflow-wrap:anywhere]">[{source.id}] {source.act} · {source.act === 'Constitution' ? 'Article' : 'Section'} {source.section} — {source.title}
                  {source.historical && <span className="ml-2 text-xs font-normal text-muted">Historical text</span>}
                </summary>
                <blockquote className="mt-4 whitespace-pre-wrap border-l-2 border-accent pl-3 text-sm leading-relaxed text-slate [overflow-wrap:anywhere]">{source.text}</blockquote>
                <a href={source.url} target="_blank" rel="noopener noreferrer" className="mt-4 inline-block text-xs font-semibold text-accent hover:underline">Open official source · PDF page {source.page} ↗</a>
              </details>)}</div>
            </div>}
          </section>}
        </div>
        <aside className="space-y-5">
          <section className="border border-line bg-white p-5"><h2 className="text-sm font-semibold">Corpus coverage</h2>
            {status ? <><ul className="mt-3 divide-y divide-line">{status.acts.map((item) => <li key={item.act} className="flex items-center justify-between gap-2 py-2 text-xs">
              <span>{item.act}<span className="block text-[10px] text-muted">{item.historical ? 'Historical statute' : 'Static snapshot'}</span></span>
              <span className="text-right text-muted">{item.sections} provisions<br/>{item.chunks} passages</span>
            </li>)}</ul>{status.seeded_at && <p className="mt-3 text-xs text-muted">Indexed {formatDate(status.seeded_at)}</p>}</>
              : <p className="mt-3 text-xs text-muted">{statusError || 'Checking library…'}</p>}
          </section>
          <section className="border border-line bg-white p-5"><div className="flex items-center justify-between gap-2"><h2 className="text-sm font-semibold">Session history</h2>
            {entries.length > 0 && <button type="button" disabled={pending} onClick={() => {setEntries([]); setActive(0);}} className="text-xs text-muted hover:text-danger disabled:opacity-50">Clear</button>}</div>
            {entries.length === 0 ? <p className="mt-3 text-xs leading-relaxed text-muted">Your last 10 questions appear here during this visit.</p> : <ol className="mt-3 space-y-2">{entries.map((item, index) =>
              <li key={index}><button type="button" disabled={pending} aria-pressed={active === index} onClick={() => {setActive(index); setQuestion(item.question); setAct(item.act || ''); setError(null);}}
                className={`w-full rounded p-2 text-left text-xs leading-relaxed [overflow-wrap:anywhere] disabled:opacity-50 ${active === index ? 'bg-accent-soft text-accent' : 'text-slate hover:bg-paper'}`}>{item.question}</button></li>)}</ol>}
          </section>
        </aside>
      </div>
    </main>
  </>;
}
