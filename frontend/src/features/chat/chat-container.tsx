import { useReducer, useCallback } from "preact/hooks";

import type { ChatMessage } from "@/types";

import { sendMessage } from "@/api/chat";
import { ApiError } from "@/api/client";

import { Button } from "@/components/ui/button";

import { MessageList } from "@/features/chat/message-list";
import { ChatInput } from "@/features/chat/chat-input";

interface ChatState {
  sessionId: string | null;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
}

type ChatAction =
  | { type: "ADD_USER_MESSAGE"; payload: string }
  | { type: "ADD_ASSISTANT_MESSAGE"; payload: ChatMessage }
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "SET_ERROR"; payload: string | null }
  | { type: "SET_SESSION_ID"; payload: string }
  | { type: "NEW_SESSION" };

const initialState: ChatState = {
  sessionId: null,
  messages: [],
  isLoading: false,
  error: null,
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
      return { ...initialState };
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
      } catch (err: unknown) {
        dispatch({ type: "SET_ERROR", payload: getErrorMessage(err) });
      } finally {
        dispatch({ type: "SET_LOADING", payload: false });
      }
    },
    [state.sessionId],
  );

  const handleNewSession = useCallback((): void => {
    dispatch({ type: "NEW_SESSION" });
  }, []);

  const handleRetry = useCallback((): void => {
    // Find the last user message and retry it
    const lastUserMsg = [...state.messages].reverse().find((m) => m.role === "user");
    if (lastUserMsg) {
      // Remove the failed user message and resend
      dispatch({ type: "SET_ERROR", payload: null });
      handleSend(lastUserMsg.content);
    }
  }, [state.messages, handleSend]);

  return (
    <div class="flex flex-col h-full">
      <div class="flex items-center justify-between border-b border-gray-200 px-6 py-3">
        <h1 class="text-lg font-semibold leading-7 text-gray-950">Customer 360 Chat</h1>
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
  );
}
