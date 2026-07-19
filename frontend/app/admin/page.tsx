"use client";

import { useEffect, useState } from "react";
import { AdminGuard } from "@/components/admin/AdminGuard";
import { DocumentTable } from "@/components/admin/DocumentTable";
import { apiClient } from "@/lib/api/client";
import type { DocumentResponse, User } from "@/lib/api/types";

function AdminDashboard() {
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  useEffect(() => {
    Promise.all([
      apiClient.get<DocumentResponse[]>("/api/v1/admin/documents"),
      apiClient.get<User[]>("/api/v1/admin/users"),
    ])
      .then(([docs, allUsers]) => {
        setDocuments(docs);
        setUsers(allUsers);
      })
      .finally(() => setLoadingData(false));
  }, []);

  function handleDeleted(id: string) {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  }

  if (loadingData) return <p className="p-8 text-slate-400">Loading...</p>;

  return (
    <main className="min-h-screen bg-slate-950 p-8">
      <h1 className="mb-6 text-xl font-semibold text-white">Admin Dashboard</h1>

      <section className="mb-8">
        <h2 className="mb-3 text-sm font-medium uppercase text-slate-500">
          Users ({users.length})
        </h2>
        <ul className="text-sm text-slate-300">
          {users.map((u) => (
            <li key={u.id} className="border-b border-slate-800 py-1.5">
              {u.email} — <span className="text-slate-500">{u.role}</span>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase text-slate-500">
          All Documents ({documents.length})
        </h2>
        <DocumentTable documents={documents} onDeleted={handleDeleted} />
      </section>
    </main>
  );
}

export default function AdminPage() {
  return (
    <AdminGuard>
      <AdminDashboard />
    </AdminGuard>
  );
}