import { type ComponentChildren } from "preact";

import { cn } from "@/lib/cn";

import { Skeleton } from "@/components/ui/skeleton";

interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => ComponentChildren;
  class?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  onRowClick?: (item: T) => void;
  isLoading?: boolean;
  emptyMessage?: string;
}

export type { Column };

export function DataTable<T extends object>({
  columns,
  data,
  onRowClick,
  isLoading = false,
  emptyMessage = "No data found",
}: DataTableProps<T>): preact.JSX.Element {
  const skeletonRows = 5;

  return (
    <div class="overflow-hidden rounded-xl border border-gray-200">
      <table class="w-full">
        <thead>
          <tr class="bg-gray-50">
            {columns.map((col) => (
              <th
                key={col.key}
                class={cn(
                  "px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                  col.class,
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading && (
            <>
              {Array.from({ length: skeletonRows }).map((_, rowIndex) => (
                <tr key={`skeleton-${rowIndex}`} class="border-b border-gray-100">
                  {columns.map((col) => (
                    <td key={col.key} class="px-6 py-4">
                      <Skeleton height="16px" width="75%" />
                    </td>
                  ))}
                </tr>
              ))}
            </>
          )}
          {!isLoading && data.length === 0 && (
            <tr>
              <td
                colSpan={columns.length}
                class="px-6 py-12 text-center text-sm text-gray-500"
              >
                {emptyMessage}
              </td>
            </tr>
          )}
          {!isLoading && data.map((item, rowIndex) => (
            <tr
              key={rowIndex}
              class={cn(
                "border-b border-gray-100 hover:bg-gray-50",
                onRowClick && "cursor-pointer",
              )}
              onClick={onRowClick ? () => onRowClick(item) : undefined}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  class={cn("px-6 py-4 text-sm text-gray-900", col.class)}
                >
                  {col.render
                    ? col.render(item)
                    : String((item as Record<string, unknown>)[col.key] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
