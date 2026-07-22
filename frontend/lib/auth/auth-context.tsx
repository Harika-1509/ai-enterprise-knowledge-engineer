"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { apiClient } from "@/lib/api/client";
import type { User } from "@/lib/api/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("ake_token");
    if (!token) {
      setLoading(false);
      return;
    }
    apiClient
      .get<User>("/api/v1/auth/me")
      .then(setUser)
      .catch(() => localStorage.removeItem("ake_token"))
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    // Backend's /auth/login (Step 5) expects OAuth2PasswordRequestForm
    // (form-encoded, field name "username"), not JSON - a deliberate
    // FastAPI/Swagger convention from Step 5, so we build the request
    // body differently here than our normal JSON apiClient calls.
    const API_URL = process.env.NEXT_PUBLIC_API_URL;
    const formBody = new URLSearchParams();
    formBody.append("username", email);
    formBody.append("password", password);

    const response = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formBody,
    });

    if (!response.ok) throw new Error("Login failed. Check your credentials.");

    const { access_token } = await response.json();
    localStorage.setItem("ake_token", access_token);

    const me = await apiClient.get<User>("/api/v1/auth/me");
    setUser(me);
  }

  function logout() {
    localStorage.removeItem("ake_token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}