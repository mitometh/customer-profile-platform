import { Button } from "@/components/ui/button";

interface PaginationControlsProps {
  hasNext: boolean;
  isLoading: boolean;
  total: number | null;
  currentCount: number;
  onLoadMore: () => void;
}

export function PaginationControls({
  hasNext,
  isLoading,
  total,
  currentCount,
  onLoadMore,
}: PaginationControlsProps): preact.JSX.Element {
  const showingText = total !== null
    ? `Showing ${currentCount} of ${total}`
    : `Showing ${currentCount} results`;

  return (
    <div class="bg-gray-50 px-6 py-3 text-sm text-gray-500 flex items-center justify-between">
      <span>{showingText}</span>
      {hasNext && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onLoadMore}
          disabled={!hasNext || isLoading}
          loading={isLoading}
        >
          Load More
        </Button>
      )}
    </div>
  );
}
