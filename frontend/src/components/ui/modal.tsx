import { type ComponentChildren } from "preact";
import { useEffect, useRef } from "preact/hooks";

import { cn } from "@/lib/cn";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ComponentChildren;
  size?: "sm" | "md" | "lg";
  footer?: ComponentChildren;
}

const sizes: Record<string, string> = {
  sm: "max-w-sm",
  md: "max-w-lg",
  lg: "max-w-2xl",
};

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = "md",
  footer,
}: ModalProps): preact.JSX.Element | null {
  const titleId = useRef(`modal-title-${Math.random().toString(36).slice(2, 9)}`);

  useEffect(() => {
    if (!isOpen) return;

    document.body.classList.add("overflow-hidden");

    const handleKeyDown = (e: KeyboardEvent): void => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.classList.remove("overflow-hidden");
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleOverlayClick = (e: MouseEvent): void => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      class="fixed inset-0 z-50 bg-gray-950/50 backdrop-blur-sm flex items-center justify-center"
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId.current}
    >
      <div class={cn("bg-white rounded-2xl shadow-xl w-full mx-4", sizes[size])}>
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2
            id={titleId.current}
            class="text-lg font-semibold text-gray-950"
          >
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            class="text-gray-500 hover:text-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded-lg p-1"
            aria-label="Close"
          >
            <svg
              class="h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="px-6 py-5">
          {children}
        </div>
        {footer && (
          <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
