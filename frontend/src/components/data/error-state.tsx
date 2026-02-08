import { cn } from "@/lib/cn";

import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  class?: string;
}

export function ErrorState({
  title = "Something went wrong",
  message = "An error occurred. Please try again.",
  onRetry,
  class: className,
}: ErrorStateProps): preact.JSX.Element {
  return (
    <div class={cn("flex flex-col items-center justify-center py-12 text-center", className)}>
      <div class="w-12 h-12 text-red-400 mx-auto">
        <svg
          class="w-12 h-12"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
          />
        </svg>
      </div>
      <h3 class="text-sm font-medium text-gray-900 mt-4">{title}</h3>
      <p class="text-sm text-gray-500 mt-1">{message}</p>
      {onRetry && (
        <div class="mt-4">
          <Button variant="secondary" onClick={onRetry}>
            Retry
          </Button>
        </div>
      )}
    </div>
  );
}
