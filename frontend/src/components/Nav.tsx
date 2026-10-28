"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearAuth, getStoredUser, getAuthSnapshot, subscribeAuth } from "@/lib/api";
import { useSyncExternalStore } from "react";

export function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const snapshot = useSyncExternalStore(subscribeAuth, getAuthSnapshot, () => null);
  const authed = snapshot !== null;
  const name = authed ? getStoredUser()?.name : null;

  function logout() {
    clearAuth();
    router.push("/login");
  }

  return (
    <header className="border-b border-line/80 bg-paper/80 backdrop-blur-sm sticky top-0 z-40">
      <div className="mx-auto flex min-h-14 flex-wrap gap-2 py-2 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link
          href={authed ? "/dashboard" : "/"}
          className="font-[family-name:var(--font-display)] text-xl tracking-tight text-ink"
        >
          CaseCrypt
        </Link>
        <nav className="flex flex-wrap items-center gap-1 text-sm sm:gap-3">
          {authed ? (
            <>
              <span className="hidden text-muted sm:inline">{name}</span>
              <Link
                href="/dashboard"
                className="rounded-md px-3 py-1.5 text-slate hover:bg-paper-deep hover:text-ink"
              >
                Dashboard
              </Link>
              <Link href="/research" aria-current={pathname === "/research" ? "page" : undefined}
                className="rounded-md px-3 py-1.5 text-slate hover:bg-paper-deep hover:text-ink">
                Research
              </Link>
              <button
                type="button"
                onClick={logout}
                className="rounded-md border border-line px-3 py-1.5 text-slate hover:border-ink/30 hover:text-ink"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="rounded-md px-3 py-1.5 text-slate hover:text-ink">
                Log in
              </Link>
              <Link
                href="/register"
                className="rounded-md bg-accent px-3 py-1.5 font-medium text-white hover:bg-accent-hover"
              >
                Get started
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
