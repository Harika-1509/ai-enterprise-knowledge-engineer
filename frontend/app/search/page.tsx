"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { apiClient } from "@/lib/api/client";
import type { SearchResponse, SearchResult } from "@/lib/api/types";

export default function SearchPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    try {
      const response = await apiClient.post<SearchResponse>("/api/v1/search/", {
        query,
        limit: 10,
      });
      setResults(response.results);
    } catch (err) {
      alert("Search failed.");
    } finally {
      setSearching(false);
    }
  }

  if (loading || !user) return null;

  return (
    <main className="min-h-screen bg-slate-950 p-8">
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-white">Search Documents</h1>
          <a href="/chat" className="text-sm text-slate-400 hover:text-white">← Back to chat</a>
        </div>

        <form onSubmit={handleSearch} className="mb-6 flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search your knowledge base..."
            className="flex-1 rounded border border-slate-700 bg-slate-800 p-3 text-white"
          />
          <button
            type="submit"
            disabled={searching}
            className="rounded bg-blue-600 px-6 font-medium text-white disabled:opacity-50"
          >
            {searching ? "Searching..." : "Search"}
          </button>
        </form>

        <div className="space-y-3">
          {results.map((r, i) => (
            <div key={i} className="rounded-lg border border-slate-800 bg-slate-900 p-4">
              <div className="mb-1 flex items-center justify-between">
                <span className="font-medium text-white">{r.filename}</span>
                <span className="text-xs text-slate-500">score: {r.score.toFixed(3)}</span>
              </div>
              {r.page_number && <p className="text-xs text-slate-500">Page {r.page_number}</p>}
              <p className="mt-2 text-sm text-slate-300">{r.content}</p>
            </div>
          ))}
          {results.length === 0 && !searching && (
            <p className="text-slate-500">No results yet — try a search above.</p>
          )}
        </div>
      </div>
    </main>
  );
}