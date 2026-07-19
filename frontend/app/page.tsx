"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api/client";

export default function HomePage() {
  const [status, setStatus] = useState<string>("Checking backend connection...");

  useEffect(() => {
    apiClient
      .get<{ message: string }>("/")
      .then((data) => setStatus(`✅ Connected: ${data.message}`))
      .catch((err) => setStatus(`❌ Connection failed: ${err.message}`));
  }, []);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
      <div className="w-full max-w-2xl text-center px-6">
        <h1 className="mb-4 text-4xl font-bold">
          AI Enterprise Knowledge Engineer
        </h1>

        <p className="mb-6 text-lg text-slate-400">
          An AI-powered enterprise knowledge platform for document search,
          question answering, and intelligent information retrieval.
        </p>

        <p className="mb-8 text-sm text-slate-500">
          {status}
        </p>

        <div className="flex justify-center gap-4">
          <Link
            href="/login"
            className="rounded-lg bg-blue-600 px-6 py-3 font-medium text-white transition hover:bg-blue-700"
          >
            Login
          </Link>

          <Link
            href="/register"
            className="rounded-lg border border-slate-600 px-6 py-3 font-medium text-white transition hover:bg-slate-800"
          >
            Register
          </Link>
        </div>
      </div>
    </main>
  );
}