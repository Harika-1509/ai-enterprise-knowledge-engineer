"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api/client";

export default function HomePage() {
  const [status, setStatus] = useState<string>("Checking backend connection...");

  useEffect(() => {
    apiClient
      .get<{ message: string }>("/")
      .then((data) => setStatus(`Connected: ${data.message}`))
      .catch((err) => setStatus(`Connection failed: ${err.message}`));
  }, []);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
      <div className="text-center">
        <h1 className="text-2xl font-semibold mb-2">AI Enterprise Knowledge Engineer</h1>
        <p className="text-slate-400">{status}</p>
      </div>
    </main>
  );
}