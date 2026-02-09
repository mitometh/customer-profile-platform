import type { SessionSummary } from "@/types";

import { cn } from "@/lib/cn";

interface SessionListProps {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  isLoading: boolean;
  onSelect: (sessionId: string) => void;
  onNewSession: () => void;
}

function formatRelativeTime(dateStr: string | null): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDays = Math.floor(diffHr / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

function getSessionLabel(session: SessionSummary): string {
  if (session.title) return session.title;
  return `Conversation`;
}

export function SessionList({
  sessions,
  activeSessionId,
  isLoading,
  onSelect,
  onNewSession,
}: SessionListProps): preact.JSX.Element {
  return (
    <div class="w-72 flex-shrink-0 border-r border-gray-200 bg-gray-50 flex flex-col h-full">
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <h2 class="text-sm font-semibold text-gray-700">History</h2>
        <button
          type="button"
          onClick={onNewSession}
          class="p-1 rounded text-gray-500 hover:bg-gray-200 hover:text-gray-700 transition-colors"
          title="New conversation"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto">
        {isLoading && sessions.length === 0 && (
          <div class="px-4 py-8 text-center text-sm text-gray-400">Loading...</div>
        )}

        {!isLoading && sessions.length === 0 && (
          <div class="px-4 py-8 text-center text-sm text-gray-400">No conversations yet</div>
        )}

        {sessions.map((session) => {
          const isActive = session.id === activeSessionId;
          return (
            <button
              key={session.id}
              type="button"
              onClick={() => onSelect(session.id)}
              class={cn(
                "w-full text-left px-4 py-3 border-b border-gray-100 transition-colors",
                isActive
                  ? "bg-indigo-50 border-l-2 border-l-indigo-500"
                  : "hover:bg-gray-100",
              )}
            >
              <div class="flex items-start justify-between gap-2">
                <span
                  class={cn(
                    "text-sm font-medium truncate",
                    isActive ? "text-indigo-700" : "text-gray-800",
                  )}
                >
                  {getSessionLabel(session)}
                </span>
                <span class="text-xs text-gray-400 whitespace-nowrap flex-shrink-0">
                  {formatRelativeTime(session.last_message_at)}
                </span>
              </div>
              <div class="text-xs text-gray-400 mt-0.5">
                {session.message_count} message{session.message_count !== 1 ? "s" : ""}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
