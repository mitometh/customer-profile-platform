import { useEffect, useRef } from "preact/hooks";

import type { ChatMessage } from "@/types";

import { MessageBubble } from "@/features/chat/message-bubble";

interface MessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps): preact.JSX.Element {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div class="flex-1 min-h-0 overflow-y-auto px-6 py-4 flex items-center justify-center">
        <p class="text-sm text-gray-500">Ask anything about your customers</p>
      </div>
    );
  }

  return (
    <div class="flex-1 min-h-0 overflow-y-auto px-6 py-4 space-y-4">
      {messages.map((msg, index) => (
        <MessageBubble key={index} message={msg} />
      ))}
      {isLoading && (
        <div class="flex flex-col items-start">
          <span class="text-xs text-gray-500 mb-1">Assistant</span>
          <div class="bg-white border border-gray-200 rounded-2xl rounded-bl-md mr-auto px-4 py-3">
            <div class="flex items-center gap-1" aria-live="polite" aria-label="Assistant is typing">
              <span class="h-2 w-2 rounded-full bg-gray-400 animate-pulse" />
              <span class="h-2 w-2 rounded-full bg-gray-400 animate-pulse [animation-delay:150ms]" />
              <span class="h-2 w-2 rounded-full bg-gray-400 animate-pulse [animation-delay:300ms]" />
            </div>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
