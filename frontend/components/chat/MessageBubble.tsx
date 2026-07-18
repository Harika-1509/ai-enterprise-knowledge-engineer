interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

export function MessageBubble({ role, content, isStreaming }: MessageBubbleProps) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-2xl rounded-lg px-4 py-3 ${
          isUser ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-100"
        }`}
      >
        <p className="whitespace-pre-wrap">
          {content}
          {isStreaming && <span className="animate-pulse">▋</span>}
        </p>
      </div>
    </div>
  );
}