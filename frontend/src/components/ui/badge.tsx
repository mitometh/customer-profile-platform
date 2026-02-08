import { type ComponentChildren } from "preact";

import { cn } from "@/lib/cn";

interface BadgeProps {
  variant?: "default" | "primary" | "success" | "warning" | "danger";
  children: ComponentChildren;
  class?: string;
}

const variants: Record<string, string> = {
  default: "bg-gray-100 text-gray-700",
  primary: "bg-indigo-100 text-indigo-700",
  success: "bg-green-100 text-green-700",
  warning: "bg-amber-100 text-amber-700",
  danger: "bg-red-100 text-red-700",
};

export function Badge({
  variant = "default",
  children,
  class: className,
}: BadgeProps): preact.JSX.Element {
  return (
    <span
      class={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
