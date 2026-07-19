"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api/client";
import type { DocumentResponse } from "@/lib/api/types";

const STATUS_STYLES: Record<string, string> = {
  completed: "bg-green-500/20 text-green-300",
  processing: "bg-yellow-500/20 text-yellow-300",
  pending: "bg-slate-500/20 text-slate-300",
  failed: "bg-red-500/20 text-red-300",
};

interface DocumentTableProps {
  documents: DocumentResponse[];
  onDeleted: (id: string) => void;
}

export function DocumentTable({ documents, onDeleted }: DocumentTableProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleDelete(id: string) {
    if (!confirm("Delete this document? This cannot be undone.")) return;
    setDeletingId(id);
    try {
      await apiClient.del(`/api/v1/documents/${id}`);// see note below
      onDeleted(id);
    } catch (err) {
      alert("Failed to delete document.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <table className="w-full text-left text-sm text-slate-300">
      <thead className="border-b border-slate-700 text-slate-400">
        <tr>
          <th className="py-2">Filename</th>
          <th className="py-2">Type</th>
          <th className="py-2">Status</th>
          <th className="py-2">Uploaded</th>
          <th className="py-2"></th>
        </tr>
      </thead>
      <tbody>
        {documents.map((doc) => (
          <tr key={doc.id} className="border-b border-slate-800">
            <td className="py-2">{doc.filename}</td>
            <td className="py-2 uppercase text-xs text-slate-500">{doc.file_type}</td>
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
                disabled={deletingId === doc.id}
                className="text-red-400 hover:text-red-300 disabled:opacity-50"
              >
                {deletingId === doc.id ? "Deleting..." : "Delete"}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}