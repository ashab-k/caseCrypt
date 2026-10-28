"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Nav } from "@/components/Nav";
import { ApiError, api, setAuth } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.register(name, email, password);
      setAuth(res.access_token, res.user);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Nav />
      <main className="flex flex-1 items-center justify-center px-4 py-16">
        <form
          onSubmit={onSubmit}
          className="animate-fade-up w-full max-w-md border border-line bg-white p-8 shadow-sm"
        >
          <h1 className="font-[family-name:var(--font-display)] text-3xl text-ink">
            Create account
          </h1>
          <p className="mt-2 text-sm text-muted">Start managing cases with CaseCrypt.</p>

          {error && (
            <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-danger">{error}</p>
          )}

          <label className="mt-6 block text-sm font-medium text-ink-soft">
            Full name
            <input
              type="text"
              required
              minLength={2}
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1.5 w-full rounded-md border border-line bg-paper px-3 py-2 text-ink outline-none focus:border-accent"
            />
          </label>

          <label className="mt-4 block text-sm font-medium text-ink-soft">
            Email
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1.5 w-full rounded-md border border-line bg-paper px-3 py-2 text-ink outline-none focus:border-accent"
            />
          </label>

          <label className="mt-4 block text-sm font-medium text-ink-soft">
            Password
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1.5 w-full rounded-md border border-line bg-paper px-3 py-2 text-ink outline-none focus:border-accent"
            />
          </label>

          <button
            type="submit"
            disabled={loading}
            className="mt-6 w-full rounded-md bg-accent py-2.5 text-sm font-semibold text-white hover:bg-accent-hover disabled:opacity-60"
          >
            {loading ? "Creating…" : "Register"}
          </button>

          <p className="mt-4 text-center text-sm text-muted">
            Already registered?{" "}
            <Link href="/login" className="font-medium text-accent hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </main>
    </>
  );
}
