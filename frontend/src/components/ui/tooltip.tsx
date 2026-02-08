import { type ComponentChildren } from "preact";
import { useRef, useState } from "preact/hooks";

import { cn } from "@/lib/cn";

interface TooltipProps {
  content: string;
  children: ComponentChildren;
  class?: string;
}

export function Tooltip({
  content,
  children,
  class: className,
}: TooltipProps): preact.JSX.Element {
  const [isVisible, setIsVisible] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const show = (): void => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, 200);
  };

  const hide = (): void => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setIsVisible(false);
  };

  return (
    <div
      class={cn("relative inline-block", className)}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      {isVisible && (
        <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 pointer-events-none">
          <div class="bg-gray-900 text-white text-xs rounded-lg px-2 py-1 whitespace-nowrap">
            {content}
          </div>
          <div class="flex justify-center">
            <div class="w-2 h-2 bg-gray-900 rotate-45 -mt-1" />
          </div>
        </div>
      )}
    </div>
  );
}
