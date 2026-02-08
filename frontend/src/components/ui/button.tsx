import { type ComponentChildren } from "preact";

import { cn } from "@/lib/cn";

import { Spinner } from "@/components/ui/spinner";

interface ButtonProps {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  children: ComponentChildren;
  class?: string;
  type?: "button" | "submit" | "reset";
}

const variants: Record<string, string> = {
  primary: "bg-indigo-600 text-white hover:bg-indigo-700",
  secondary: "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50",
  ghost: "text-gray-600 hover:bg-gray-100",
  danger: "bg-red-600 text-white hover:bg-red-700",
};

const sizes: Record<string, string> = {
  sm: "h-8 px-3 text-xs",
  md: "h-9 px-4 text-sm",
  lg: "h-10 px-5 text-sm",
};

const spinnerSizes: Record<string, "sm" | "md"> = {
  sm: "sm",
  md: "md",
  lg: "md",
};

export function Button({
  variant = "primary",
  size = "md",
  disabled = false,
  loading = false,
  onClick,
  children,
  class: className,
  type = "button",
}: ButtonProps): preact.JSX.Element {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      class={cn(
        "inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2",
        variants[variant],
        sizes[size],
        (disabled || loading) && "opacity-50 cursor-not-allowed",
        className,
      )}
    >
      {loading && <Spinner class="mr-2" size={spinnerSizes[size]} />}
      {children}
    </button>
  );
}
