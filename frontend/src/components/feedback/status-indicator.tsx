import { cn } from "@/lib/cn";

type StatusType = "up" | "down" | "healthy" | "degraded" | "unhealthy";

interface StatusIndicatorProps {
  status: StatusType;
  label?: string;
  class?: string;
}

const dotColors: Record<StatusType, string> = {
  up: "bg-green-500",
  healthy: "bg-green-500",
  degraded: "bg-amber-500",
  down: "bg-red-500",
  unhealthy: "bg-red-500",
};

export function StatusIndicator({
  status,
  label,
  class: className,
}: StatusIndicatorProps): preact.JSX.Element {
  return (
    <span class={cn("inline-flex items-center gap-2", className)}>
      <span class={cn("w-2.5 h-2.5 rounded-full", dotColors[status])} />
      {label && <span class="text-sm text-gray-700">{label}</span>}
    </span>
  );
}
