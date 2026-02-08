import { useState, useCallback } from "preact/hooks";

import type { Source } from "@/types";

import { cn } from "@/lib/cn";

interface SourceCitationProps {
  sources: Source[];
}

function truncateUuid(uuid: string): string {
  if (uuid.length <= 12) return uuid;
  return `${uuid.slice(0, 8)}...`;
}

export function SourceCitation({ sources }: SourceCitationProps): preact.JSX.Element {
  const [isExpanded, setIsExpanded] = useState(false);

  const toggle = useCallback((): void => {
    setIsExpanded((prev) => !prev);
  }, []);

  return (
    <div class="bg-gray-50 rounded-lg p-3 mt-2 text-xs font-mono">
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
        <span>Sources ({sources.length})</span>
      </button>
      {isExpanded && (
        <ul class="mt-2 space-y-2" role="list">
          {sources.map((source, index) => (
            <li key={index} class="border-t border-gray-200 pt-2 first:border-t-0 first:pt-0">
              <div class="flex items-baseline gap-2">
                <span class="text-gray-700 font-medium">{source.table}</span>
                <span class="text-gray-500" title={source.record_id}>
                  {truncateUuid(source.record_id)}
                </span>
              </div>
              <div class="text-gray-500 mt-0.5">
                {Object.keys(source.fields_used).join(", ")}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
