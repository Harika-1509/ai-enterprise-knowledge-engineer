"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/auth-context";
import { streamAsk } from "@/lib/api/stream";
import { MessageBubble } from "@/components/chat/MessageBubble";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    if (!input.trim() || streaming) return;

    const query = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    setStreaming(true);

    try {
      await streamAsk(query, 5, (event) => {
        if (event.type === "token" && event.content) {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: updated[updated.length - 1].content + event.content,
            };
            return updated;
          });
        }
      });
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Sorry, something went wrong generating a response.",
        };
        return updated;
      });
    } finally {
      setStreaming(false);
    }
  }

  if (loading || !user) return null;

  return (
    <main className="flex h-screen flex-col bg-slate-950">
      <header className="flex items-center justify-between border-b border-slate-800 p-4">
        <h1 className="text-white font-medium">AI Enterprise Knowledge Engineer</h1>
        <button onClick={logout} className="text-sm text-slate-400 hover:text-white">
          Sign out
        </button>
      </header>

      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((m, i) => (
          <MessageBubble
            key={i}
            role={m.role}
            content={m.content}
            isStreaming={streaming && i === messages.length - 1 && m.role === "assistant"}
          />
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-slate-800 p-4">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask a question about your documents..."
            className="flex-1 rounded border border-slate-700 bg-slate-800 p-3 text-white"
          />
          <button
            onClick={handleSend}
            disabled={streaming}
            className="rounded bg-blue-600 px-6 font-medium text-white disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </main>
  );
}