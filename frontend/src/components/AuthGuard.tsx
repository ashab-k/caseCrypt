"use client";

import { useEffect, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated, subscribeAuth } from "@/lib/api";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const ready = useSyncExternalStore(subscribeAuth, isAuthenticated, () => false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
  }, [router, ready]);

  if (!ready) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted text-sm">
        Loading…
      </div>
    );
  }

  return <>{children}</>;
}
