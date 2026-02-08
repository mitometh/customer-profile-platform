import { cn } from "@/lib/cn";

interface SkeletonProps {
  class?: string;
  width?: string;
  height?: string;
}

export function Skeleton({ class: className, width, height }: SkeletonProps): preact.JSX.Element {
  return (
    <div
      class={cn("animate-pulse bg-gray-200 rounded", className)}
      style={{ width, height }}
    />
  );
}
