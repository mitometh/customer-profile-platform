export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  tool_calls?: ToolCall[];
}

export interface ChatResponse {
  session_id: string;
  message: {
    role: "assistant";
    content: string;
  };
  sources?: Source[];
  tool_calls?: ToolCall[];
}

export interface Source {
  table: string;
  record_id: string;
  fields_used: Record<string, unknown>;
}

export interface ToolCall {
  tool: string;
  input: Record<string, unknown>;
  result_count: number;
}

export interface SessionSummary {
  id: string;
  title: string | null;
  message_count: number;
  last_message_at: string | null;
  created_at: string;
}

export interface SessionMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  tool_calls?: ToolCall[];
  created_at: string;
}

export interface SessionDetail {
  id: string;
  title: string | null;
  message_count: number;
  last_message_at: string | null;
  created_at: string;
  messages: SessionMessage[];
}
