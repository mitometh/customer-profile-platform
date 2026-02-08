import { useReducer, useCallback, useEffect } from "preact/hooks";

import type { ChatMessage, SessionSummary } from "@/types";

import { sendMessage, getSessions, getSessionDetail } from "@/api/chat";
import { ApiError } from "@/api/client";

import { Button } from "@/components/ui/button";

import { MessageList } from "@/features/chat/message-list";
import { ChatInput } from "@/features/chat/chat-input";
import { SessionList } from "@/features/chat/session-list";

interface ChatState {
  sessionId: string | null;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sessions: SessionSummary[];
  sessionsLoading: boolean;
  showHistory: boolean;
}

type ChatAction =
  | { type: "ADD_USER_MESSAGE"; payload: string }
  | { type: "ADD_ASSISTANT_MESSAGE"; payload: ChatMessage }
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "SET_ERROR"; payload: string | null }
  | { type: "SET_SESSION_ID"; payload: string }
  | { type: "NEW_SESSION" }
  | { type: "SET_SESSIONS"; payload: SessionSummary[] }
  | { type: "SET_SESSIONS_LOADING"; payload: boolean }
  | { type: "LOAD_SESSION"; payload: { sessionId: string; messages: ChatMessage[] } }
  | { type: "TOGGLE_HISTORY" };

const initialState: ChatState = {
  sessionId: null,
  messages: [],
  isLoading: false,
  error: null,
  sessions: [],
  sessionsLoading: false,
  showHistory: false,
};

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "ADD_USER_MESSAGE":
      return {
        ...state,
        messages: [
          ...state.messages,
          { role: "user", content: action.payload },
        ],
        error: null,
      };
    case "ADD_ASSISTANT_MESSAGE":
      return {
        ...state,
        messages: [...state.messages, action.payload],
      };
    case "SET_LOADING":
      return { ...state, isLoading: action.payload };
    case "SET_ERROR":
      return { ...state, error: action.payload };
    case "SET_SESSION_ID":
      return { ...state, sessionId: action.payload };
    case "NEW_SESSION":
      return { ...initialState, sessions: state.sessions };
    case "SET_SESSIONS":
      return { ...state, sessions: action.payload };
    case "SET_SESSIONS_LOADING":
      return { ...state, sessionsLoading: action.payload };
    case "LOAD_SESSION":
      return {
        ...state,
        sessionId: action.payload.sessionId,
        messages: action.payload.messages,
        error: null,
        showHistory: false,
      };
    case "TOGGLE_HISTORY":
      return { ...state, showHistory: !state.showHistory };
    default:
      return state;
  }
}

function getErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    const codeMap: Record<string, string> = {
      UNAUTHORIZED: "Your session has expired. Please log in again.",
      FORBIDDEN: "You don't have permission to use the chat.",
      RATE_LIMITED: "Too many requests. Please wait a moment.",
      LLM_UNAVAILABLE: "The AI assistant is temporarily unavailable. Please try again.",
      INTERNAL_ERROR: "Something went wrong. Please try again.",
    };
    return codeMap[err.error.code] ?? err.error.message;
  }
  if (err instanceof Error) {
    return err.message;
  }
  return "Something went wrong. Please try again.";
}

export function ChatContainer(): preact.JSX.Element {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  const fetchSessions = useCallback(async (): Promise<void> => {
    dispatch({ type: "SET_SESSIONS_LOADING", payload: true });
    try {
      const sessions = await getSessions();
      dispatch({ type: "SET_SESSIONS", payload: sessions });
    } catch {
      // Silently fail — sessions list is non-critical
    } finally {
      dispatch({ type: "SET_SESSIONS_LOADING", payload: false });
    }
  }, []);

  // Load sessions on mount
  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleSend = useCallback(
    async (message: string): Promise<void> => {
      dispatch({ type: "ADD_USER_MESSAGE", payload: message });
      dispatch({ type: "SET_LOADING", payload: true });
      dispatch({ type: "SET_ERROR", payload: null });

      try {
        const response = await sendMessage(message, state.sessionId ?? undefined);

        dispatch({ type: "SET_SESSION_ID", payload: response.session_id });
        dispatch({
          type: "ADD_ASSISTANT_MESSAGE",
          payload: {
            role: "assistant",
            content: response.message.content,
            sources: response.sources,
            tool_calls: response.tool_calls,
          },
        });

        // Refresh sessions list after sending a message
        fetchSessions();
      } catch (err: unknown) {
        dispatch({ type: "SET_ERROR", payload: getErrorMessage(err) });
      } finally {
        dispatch({ type: "SET_LOADING", payload: false });
      }
    },
    [state.sessionId, fetchSessions],
  );

  const handleNewSession = useCallback((): void => {
    dispatch({ type: "NEW_SESSION" });
  }, []);

  const handleRetry = useCallback((): void => {
    const lastUserMsg = [...state.messages].reverse().find((m) => m.role === "user");
    if (lastUserMsg) {
      dispatch({ type: "SET_ERROR", payload: null });
      handleSend(lastUserMsg.content);
    }
  }, [state.messages, handleSend]);

  const handleSelectSession = useCallback(async (sessionId: string): Promise<void> => {
    try {
      dispatch({ type: "SET_LOADING", payload: true });
      const detail = await getSessionDetail(sessionId);
      const messages: ChatMessage[] = detail.messages.map((m) => ({
        role: m.role as "user" | "assistant",
        content: m.content,
        sources: m.sources,
        tool_calls: m.tool_calls,
      }));
      dispatch({ type: "LOAD_SESSION", payload: { sessionId, messages } });
    } catch (err: unknown) {
      dispatch({ type: "SET_ERROR", payload: getErrorMessage(err) });
    } finally {
      dispatch({ type: "SET_LOADING", payload: false });
    }
  }, []);

  const handleToggleHistory = useCallback((): void => {
    dispatch({ type: "TOGGLE_HISTORY" });
  }, []);

  return (
    <div class="flex h-full">
      {/* Session history sidebar */}
      {state.showHistory && (
        <SessionList
          sessions={state.sessions}
          activeSessionId={state.sessionId}
          isLoading={state.sessionsLoading}
          onSelect={handleSelectSession}
          onNewSession={handleNewSession}
          onClose={handleToggleHistory}
        />
      )}

      {/* Main chat area */}
      <div class="flex flex-col flex-1 min-w-0">
        <div class="flex items-center justify-between border-b border-gray-200 px-6 py-3">
          <div class="flex items-center gap-3">
            <button
              type="button"
              onClick={handleToggleHistory}
              class="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
              title={state.showHistory ? "Hide history" : "Show history"}
            >
              <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
            </button>
            <h1 class="text-lg font-semibold leading-7 text-gray-950">Customer 360 Chat</h1>
          </div>
          <Button variant="secondary" size="sm" onClick={handleNewSession}>
            New Conversation
          </Button>
        </div>

        <MessageList messages={state.messages} isLoading={state.isLoading} />

        {state.error && (
          <div class="mx-6 mb-2 flex-shrink-0 flex items-center justify-between rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
            <span>{state.error}</span>
            <button
              type="button"
              onClick={handleRetry}
              class="ml-3 text-xs font-medium text-red-700 underline hover:text-red-900 transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        <div class="border-t border-gray-200 px-6 py-4 flex-shrink-0">
          <ChatInput onSend={handleSend} isLoading={state.isLoading} />
        </div>
      </div>
    </div>
  );
}
