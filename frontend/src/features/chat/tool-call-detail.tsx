import { useState, useCallback } from "preact/hooks";

import type { ToolCall } from "@/types";

import { cn } from "@/lib/cn";

interface ToolCallDetailProps {
  toolCalls: ToolCall[];
}

function formatInputValue(value: unknown): string {
  if (value === null || value === undefined) return "null";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

export function ToolCallDetail({ toolCalls }: ToolCallDetailProps): preact.JSX.Element {
  const [isExpanded, setIsExpanded] = useState(false);

  const toggle = useCallback((): void => {
    setIsExpanded((prev) => !prev);
  }, []);

  return (
    <div class="bg-gray-50 rounded-lg p-3 mt-2 text-xs">
      <button
        type="button"
        onClick={toggle}
        class="flex items-center gap-1 w-full text-left text-gray-700 font-medium hover:text-gray-900 transition-colors"
        aria-expanded={isExpanded}
      >
        <svg
          class={cn(
            "h-3 w-3 text-gray-400 transition-transform",
            isExpanded && "rotate-90",
          )}
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="m8.25 4.5 7.5 7.5-7.5 7.5"
          />
        </svg>
        <span>Tools used ({toolCalls.length})</span>
      </button>
      {isExpanded && (
        <ul class="mt-2 space-y-2" role="list">
          {toolCalls.map((call, index) => (
            <li key={index} class="border-t border-gray-200 pt-2 first:border-t-0 first:pt-0">
              <div class="flex items-center gap-2">
                <span class="inline-flex items-center rounded-md bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700">
                  {call.tool}
                </span>
                <span class="text-gray-500">{call.result_count} results</span>
              </div>
              {Object.keys(call.input).length > 0 && (
                <div class="mt-1 text-gray-500 font-mono">
                  {Object.entries(call.input).map(([key, val]) => (
                    <div key={key}>
                      <span class="text-gray-600">{key}</span>: {formatInputValue(val)}
                    </div>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
