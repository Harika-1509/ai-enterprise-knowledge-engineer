"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/auth-context";
import { apiClient } from "@/lib/api/client";
import type { DocumentResponse } from "@/lib/api/types";

const STATUS_STYLES: Record<string, string> = {
  completed: "bg-green-500/20 text-green-300",
  processing: "bg-yellow-500/20 text-yellow-300",
  pending: "bg-slate-500/20 text-slate-300",
  failed: "bg-red-500/20 text-red-300",
};

export default function DocumentsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (user) fetchDocuments();
  }, [user]);

  async function fetchDocuments() {
    setLoadingDocs(true);
    try {
      const docs = await apiClient.get<DocumentResponse[]>("/api/v1/documents/");
      setDocuments(docs);
    } catch (err) {
      setError("Failed to load documents.");
    } finally {
      setLoadingDocs(false);
    }
  }

  async function handleUpload(file: File) {
    setUploading(true);
    setError(null);
    const token = localStorage.getItem("ake_token");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL;
      const response = await fetch(`${API_URL}/api/v1/documents/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!response.ok) throw new Error("Upload failed.");
      await fetchDocuments();
      pollUntilComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function pollUntilComplete() {
    // Ingestion (Step 8-16) runs as a background task - poll briefly so
    // the status badge updates from "pending" to "completed" without
    // requiring a manual page refresh.
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      await fetchDocuments();
      if (attempts >= 8) clearInterval(interval); // stop after ~16s
    }, 2000);
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this document? This cannot be undone.")) return;
    try {
      await apiClient.del(`/api/v1/documents/${id}`);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      alert("Failed to delete document.");
    }
  }

  if (loading || !user) return null;

  return (
    <main className="min-h-screen bg-slate-950 p-8">
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-white">My Documents</h1>
          <a href="/chat" className="text-sm text-slate-400 hover:text-white">
            ← Back to chat
          </a>
        </div>

        <div className="mb-6 rounded-lg border border-dashed border-slate-700 p-6 text-center">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.pptx,.xlsx,.txt"
            onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
            disabled={uploading}
            className="text-sm text-slate-400"
          />
          {uploading && <p className="mt-2 text-sm text-blue-400">Uploading...</p>}
          {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
        </div>

        {loadingDocs ? (
          <p className="text-slate-400">Loading documents...</p>
        ) : documents.length === 0 ? (
          <p className="text-slate-500">No documents uploaded yet.</p>
        ) : (
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="border-b border-slate-700 text-slate-500">
              <tr>
                <th className="py-2">Filename</th>
                <th className="py-2">Status</th>
                <th className="py-2">Uploaded</th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-b border-slate-800">
                  <td className="py-2">{doc.filename}</td>
                  <td className="py-2">
                    <span className={`rounded px-2 py-0.5 text-xs ${STATUS_STYLES[doc.status]}`}>
                      {doc.status}
                    </span>
                  </td>
                  <td className="py-2 text-slate-500">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-2">
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="text-red-400 hover:text-red-300"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}