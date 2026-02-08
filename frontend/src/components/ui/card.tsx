import { type ComponentChildren } from "preact";

import { cn } from "@/lib/cn";

interface CardProps {
  children: ComponentChildren;
  class?: string;
}

export function Card({ children, class: className }: CardProps): preact.JSX.Element {
  return (
    <div class={cn("bg-white rounded-xl border border-gray-200 shadow-sm", className)}>
      {children}
    </div>
  );
}

interface CardHeaderProps {
  title?: string;
  action?: ComponentChildren;
  children?: ComponentChildren;
  class?: string;
}

export function CardHeader({
  title,
  action,
  children,
  class: className,
}: CardHeaderProps): preact.JSX.Element {
  return (
    <div class={cn("px-6 py-4 border-b border-gray-200", className)}>
      {(title || action) ? (
        <div class="flex items-center justify-between">
          {title && (
            <h3 class="text-lg font-semibold text-gray-950">{title}</h3>
          )}
          {action && <div>{action}</div>}
        </div>
      ) : (
        children
      )}
    </div>
  );
}

interface CardBodyProps {
  children: ComponentChildren;
  class?: string;
}

export function CardBody({ children, class: className }: CardBodyProps): preact.JSX.Element {
  return (
    <div class={cn("px-6 py-5", className)}>
      {children}
    </div>
  );
}

interface CardFooterProps {
  children: ComponentChildren;
  class?: string;
}

export function CardFooter({ children, class: className }: CardFooterProps): preact.JSX.Element {
  return (
    <div class={cn("px-6 py-3 border-t border-gray-200", className)}>
      {children}
    </div>
  );
}
