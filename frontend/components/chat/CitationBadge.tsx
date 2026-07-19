"use client";

import { useState } from "react";
import type { Citation } from "@/lib/api/types";

interface CitationBadgeProps {
  number: number;
  citation: Citation | undefined;
}

export function CitationBadge({ number, citation }: CitationBadgeProps) {
  const [open, setOpen] = useState(false);

  if (!citation) {
    // Model cited a source number that didn't map to real data (Step
    // 23's out-of-range guard already prevents this from reaching
    // `citations`, but the raw [Source N] marker in the TEXT itself
    // could still reference a number that got filtered out server-side -
    // render it as plain, non-interactive text rather than a broken badge.
    return <span className="text-slate-500">[{number}]</span>;
  }

  return (
    <span className="relative inline-block">
      <button
        onClick={() => setOpen((v) => !v)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        className="mx-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-blue-500/20 px-1 text-[10px] font-medium text-blue-300 hover:bg-blue-500/40"
      >
        {number}
      </button>

      {open && (
        <div className="absolute bottom-full left-0 z-10 mb-2 w-72 rounded-lg border border-slate-700 bg-slate-800 p-3 text-xs shadow-lg">
          <p className="mb-1 font-medium text-white">{citation.filename}</p>
          {citation.location && (
            <p className="mb-2 text-slate-400">{citation.location}</p>
          )}
          <p className="text-slate-300 leading-relaxed">{citation.snippet}</p>
        </div>
      )}
    </span>
  );
}