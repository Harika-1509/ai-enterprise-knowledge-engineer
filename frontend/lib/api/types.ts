// Mirrors backend/app/schemas/search.py (Step 17)
export interface SearchResult {
  document_id: string;
  filename: string;
  content: string;
  score: number;
  chunk_index: number;
  page_number: number | null;
  slide_number: number | null;
  sheet_name: string | null;
  paragraph_index: number | null;
  table_index: number | null;
  row_index: number | null;
}

// Mirrors backend/app/schemas/answer.py (Step 23)
export interface Citation {
  source_number: number;
  document_id: string;
  filename: string;
  location: string | null;
  snippet: string;
}

// Mirrors backend/app/schemas/answer.py (Step 27)
export type ConfidenceLevel = "high" | "medium" | "low";

export interface Confidence {
  level: ConfidenceLevel;
  retrieval_score: number;
  self_verified: boolean | null;
  reasoning: string;
}

// Mirrors backend/app/schemas/answer.py (Step 22/23/27 combined)
export interface AskResponse {
  query: string;
  answer: string;
  citations: Citation[];
  sources: SearchResult[];
  confidence: Confidence;
  validation_warning: string | null;
}

// Mirrors backend/app/schemas/agent.py (Step 28)
export interface AgentResponse {
  query: string;
  intent: string;
  result: AskResponse | null;
  error: string | null;
}

// Mirrors backend/app/schemas/user.py (Step 5)
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "member";
  is_active: boolean;
}

// Mirrors backend/app/schemas/document.py (Step 7)
export interface DocumentResponse {
  id: string;
  filename: string;
  file_type: string;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
}