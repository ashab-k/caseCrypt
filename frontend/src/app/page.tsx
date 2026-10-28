import Link from "next/link";
import { Nav } from "@/components/Nav";

export default function Home() {
  return (
    <>
      <Nav />
      <main className="relative flex flex-1 flex-col overflow-hidden">
        <section className="hero-grid relative flex min-h-[calc(100vh-3.5rem)] flex-col justify-center px-4 sm:px-6">
          <div className="mx-auto w-full max-w-6xl">
            <p className="animate-fade-up font-[family-name:var(--font-display)] text-5xl tracking-tight text-ink sm:text-7xl md:text-8xl">
              CaseCrypt
            </p>
            <h1
              className="animate-fade-up mt-6 max-w-xl text-2xl font-medium leading-snug text-ink-soft sm:text-3xl"
              style={{ animationDelay: "80ms" }}
            >
              Smart legal case intelligence with verifiable evidence integrity.
            </h1>
            <p
              className="animate-fade-up mt-4 max-w-lg text-base leading-relaxed text-slate sm:text-lg"
              style={{ animationDelay: "160ms" }}
            >
              Extract facts, build timelines, research Indian statutes, and prove
              evidence has not been altered — built for lawyers who need citations,
              not black boxes.
            </p>
            <div
              className="animate-fade-up mt-10 flex flex-wrap gap-3"
              style={{ animationDelay: "240ms" }}
            >
              <Link
                href="/register"
                className="rounded-md bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-hover"
              >
                Create account
              </Link>
              <Link
                href="/login"
                className="rounded-md border border-line bg-white/60 px-5 py-2.5 text-sm font-medium text-ink hover:border-ink/25"
              >
                Sign in
              </Link>
            </div>
          </div>
        </section>
      </main>
    </>
  );
}
