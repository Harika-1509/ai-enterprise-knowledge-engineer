import type { Citation } from "@/lib/api/types";
import { CitationBadge } from "./CitationBadge";

interface CitationRendererProps {
  text: string;
  citations: Citation[];
}

// Mirrors the pattern family used in backend/app/services/generation/
// citation_parser.py (Step 23) - handles [Source 1], [Source 1, 2],
// [Sources 1 and 2] etc. Kept in sync deliberately with the backend's
// regex, since both need to recognize the exact same marker formats
// the LLM was instructed to produce (Step 22's prompt).
const CITATION_PATTERN = /\[Sources?\s+([\d,\s]+(?:and\s*\d+)?)\]/gi;

export function CitationRenderer({ text, citations }: CitationRendererProps) {
  const citationByNumber = new Map(citations.map((c) => [c.source_number, c]));

  const parts: (string | { numbers: number[] })[] = [];
  let lastIndex = 0;

  for (const match of text.matchAll(CITATION_PATTERN)) {
    const [fullMatch, rawNumbers] = match;
    const index = match.index ?? 0;

    if (index > lastIndex) {
      parts.push(text.slice(lastIndex, index));
    }

    const numbers = rawNumbers
      .replace(/and/gi, ",")
      .split(",")
      .map((s) => parseInt(s.trim(), 10))
      .filter((n) => !isNaN(n));

    parts.push({ numbers });
    lastIndex = index + fullMatch.length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return (
    <span className="whitespace-pre-wrap">
      {parts.map((part, i) =>
        typeof part === "string" ? (
          <span key={i}>{part}</span>
        ) : (
          <span key={i}>
            {part.numbers.map((n) => (
              <CitationBadge key={n} number={n} citation={citationByNumber.get(n)} />
            ))}
          </span>
        )
      )}
    </span>
  );
}