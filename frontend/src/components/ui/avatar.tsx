import { cn } from "@/lib/cn";

interface AvatarProps {
  name: string;
  size?: "sm" | "md" | "lg";
  class?: string;
}

const sizes: Record<string, string> = {
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-12 w-12 text-base",
};

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1]?.[0] ?? "" : "";
  return (first + last).toUpperCase();
}

export function Avatar({
  name,
  size = "md",
  class: className,
}: AvatarProps): preact.JSX.Element {
  const initials = getInitials(name);

  return (
    <span
      class={cn(
        "inline-flex items-center justify-center rounded-full bg-indigo-100 text-indigo-700 font-medium",
        sizes[size],
        className,
      )}
      aria-label={name}
    >
      {initials}
    </span>
  );
}
