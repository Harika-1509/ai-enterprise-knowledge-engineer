export interface StreamEvent {
  type: "token" | "citations" | "done";
  content?: string;
  citations?: unknown[];
}

export async function streamAsk(
  query: string,
  limit: number,
  onEvent: (event: StreamEvent) => void
): Promise<void> {
  const API_URL = process.env.NEXT_PUBLIC_API_URL;
  const token = localStorage.getItem("ake_token");

  const response = await fetch(`${API_URL}/api/v1/ask/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ query, limit }),
  });

  if (!response.ok || !response.body) {
    throw new Error(`Stream request failed: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // SSE events are separated by \n\n - split and process complete
    // events, keeping any trailing partial event in the buffer for
    // the next chunk (a single fetch "chunk" doesn't always align
    // neatly with a complete SSE event boundary).
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      const jsonStr = line.slice("data:".length).trim();
      try {
        const event: StreamEvent = JSON.parse(jsonStr);
        onEvent(event);
      } catch {
        // Malformed/partial JSON - skip rather than crash the stream
      }
    }
  }
}