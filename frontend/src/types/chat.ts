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
