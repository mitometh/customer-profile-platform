import { type ComponentChildren } from "preact";

import { cn } from "@/lib/cn";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  backTo?: string;
  backLabel?: string;
  actions?: ComponentChildren;
  class?: string;
}

export function PageHeader({
  title,
  subtitle,
  backTo,
  backLabel,
  actions,
  class: className,
}: PageHeaderProps): preact.JSX.Element {
  return (
    <div class={cn("mb-6", className)}>
      {backTo && (
        <a
          href={backTo}
          class="inline-flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-700 mb-2"
        >
          &larr; {backLabel ?? "Back"}
        </a>
      )}
      <div class="flex items-start justify-between">
        <div>
          <h1 class="text-2xl font-bold leading-8 text-gray-950">{title}</h1>
          {subtitle && (
            <p class="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        {actions && <div class="flex items-center gap-3">{actions}</div>}
      </div>
    </div>
  );
}
