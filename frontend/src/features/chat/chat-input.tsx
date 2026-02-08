import { useState, useRef, useCallback } from "preact/hooks";

import { cn } from "@/lib/cn";

import { Button } from "@/components/ui/button";

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
}

export function ChatInput({ onSend, isLoading }: ChatInputProps): preact.JSX.Element {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback((): void => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    const lineHeight = 20;
    const maxHeight = lineHeight * 3 + 24; // 3 rows + padding
    textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`;
  }, []);

  const handleInput = useCallback(
    (e: Event): void => {
      const target = e.target as HTMLTextAreaElement;
      setValue(target.value);
      adjustHeight();
    },
    [adjustHeight],
  );

  const handleSend = useCallback((): void => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, isLoading, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent): void => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  const isEmpty = value.trim().length === 0;

  return (
    <div class="flex items-end gap-3">
      <textarea
        ref={textareaRef}
        value={value}
        onInput={handleInput}
        onKeyDown={handleKeyDown}
        placeholder="Ask about your customers..."
        rows={1}
        disabled={isLoading}
        class={cn(
          "flex-1 resize-none rounded-lg border border-gray-300 px-4 py-3 text-sm placeholder:text-gray-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors",
          isLoading && "opacity-50 cursor-not-allowed",
        )}
        aria-label="Chat message input"
      />
      <Button
        variant="primary"
        onClick={handleSend}
        disabled={isEmpty || isLoading}
        loading={isLoading}
      >
        Send
      </Button>
    </div>
  );
}
