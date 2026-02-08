import { type ComponentChildren } from "preact";

import { Spinner } from "@/components/ui/spinner";

interface LoadingOverlayProps {
  isLoading: boolean;
  children: ComponentChildren;
}

export function LoadingOverlay({
  isLoading,
  children,
}: LoadingOverlayProps): preact.JSX.Element {
  return (
    <div class="relative">
      {children}
      {isLoading && (
        <div class="absolute inset-0 bg-white/60 flex items-center justify-center z-10">
          <Spinner size="lg" />
        </div>
      )}
    </div>
  );
}
