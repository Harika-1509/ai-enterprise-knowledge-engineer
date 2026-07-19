"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/auth-context";
import type { ReactNode } from "react";

export function AdminGuard({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.push("/login");
      return;
    }
    if (user.role !== "admin") {
      // UX-only redirect - the REAL enforcement is the backend's
      // require_role(UserRole.ADMIN) dependency (Step 6). This check
      // exists purely so a non-admin doesn't land on a broken/empty
      // page; it provides zero actual security on its own.
      router.push("/chat");
    }
  }, [user, loading, router]);

  if (loading || !user || user.role !== "admin") return null;

  return <>{children}</>;
}