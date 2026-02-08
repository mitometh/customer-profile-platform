import { type ComponentChildren } from "preact";

import { cn } from "@/lib/cn";

interface EmptyStateProps {
  icon?: ComponentChildren;
  title: string;
  description?: string;
  action?: ComponentChildren;
  class?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  class: className,
}: EmptyStateProps): preact.JSX.Element {
  return (
    <div class={cn("flex flex-col items-center justify-center py-12 text-center", className)}>
      {icon && (
        <div class="w-12 h-12 text-gray-300 mx-auto">{icon}</div>
      )}
      <h3 class="text-sm font-medium text-gray-900 mt-4">{title}</h3>
      {description && (
        <p class="text-sm text-gray-500 mt-1">{description}</p>
      )}
      {action && (
        <div class="mt-4">{action}</div>
      )}
    </div>
  );
}
