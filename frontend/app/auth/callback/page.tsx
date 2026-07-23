"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get("token");
    if (token) {
      localStorage.setItem("ake_token", token);
      router.push("/chat");
    } else {
      router.push("/login?error=missing_token");
    }
  }, [searchParams, router]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950">
      <p className="text-slate-400">Signing you in...</p>
    </main>
  );
}