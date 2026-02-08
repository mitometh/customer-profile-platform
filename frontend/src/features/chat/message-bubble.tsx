import type { ChatMessage } from "@/types";

import { cn } from "@/lib/cn";

import { SourceCitation } from "@/features/chat/source-citation";
import { ToolCallDetail } from "@/features/chat/tool-call-detail";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps): preact.JSX.Element {
  const isUser = message.role === "user";
  const hasSources = !isUser && message.sources && message.sources.length > 0;
  const hasToolCalls = !isUser && message.tool_calls && message.tool_calls.length > 0;

  return (
    <div class={cn("flex flex-col", isUser ? "items-end" : "items-start")}>
      <span class="text-xs text-gray-500 mb-1">
        {isUser ? "You" : "Assistant"}
      </span>
      <div
        class={cn(
          "px-4 py-3 max-w-[80%]",
          isUser
            ? "bg-indigo-600 text-white rounded-2xl rounded-br-md ml-auto"
            : "bg-white border border-gray-200 rounded-2xl rounded-bl-md mr-auto",
        )}
      >
        <p
          class={cn(
            "text-sm whitespace-pre-wrap",
            !isUser && "text-gray-900",
          )}
        >
          {message.content}
        </p>
      </div>
      {hasSources && (
        <div class="max-w-[80%] w-full mr-auto">
          <SourceCitation sources={message.sources!} />
        </div>
      )}
      {hasToolCalls && (
        <div class="max-w-[80%] w-full mr-auto">
          <ToolCallDetail toolCalls={message.tool_calls!} />
        </div>
      )}
    </div>
  );
}
