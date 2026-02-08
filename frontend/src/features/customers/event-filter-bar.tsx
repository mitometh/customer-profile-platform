import type { EventFilters } from "@/types";

import { Button } from "@/components/ui/button";

interface EventFilterBarProps {
  filters: EventFilters;
  onChange: (filters: EventFilters) => void;
}

export function EventFilterBar({ filters, onChange }: EventFilterBarProps): preact.JSX.Element {
  const handleTypeChange = (e: Event): void => {
    const value = (e.target as HTMLSelectElement).value;
    onChange({
      ...filters,
      event_type: value === "" ? undefined : (value as EventFilters["event_type"]),
      cursor: undefined,
    });
  };

  const handleSinceChange = (e: Event): void => {
    const value = (e.target as HTMLInputElement).value;
    onChange({
      ...filters,
      since: value || undefined,
      cursor: undefined,
    });
  };

  const handleUntilChange = (e: Event): void => {
    const value = (e.target as HTMLInputElement).value;
    onChange({
      ...filters,
      until: value || undefined,
      cursor: undefined,
    });
  };

  const handleClear = (): void => {
    onChange({});
  };

  const hasFilters = filters.event_type || filters.since || filters.until;

  return (
    <div class="flex flex-wrap items-center gap-3">
      <select
        value={filters.event_type ?? ""}
        onChange={handleTypeChange}
        class="block rounded-lg border border-gray-300 bg-white px-3 h-9 text-sm text-gray-950 transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
      >
        <option value="">All Types</option>
        <option value="support_ticket">Support Ticket</option>
        <option value="meeting">Meeting</option>
        <option value="usage_event">Usage Event</option>
      </select>
      <input
        type="date"
        value={filters.since ?? ""}
        onChange={handleSinceChange}
        placeholder="Since"
        class="block rounded-lg border border-gray-300 bg-white px-3 h-9 text-sm text-gray-950 transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
        aria-label="Since date"
      />
      <input
        type="date"
        value={filters.until ?? ""}
        onChange={handleUntilChange}
        placeholder="Until"
        class="block rounded-lg border border-gray-300 bg-white px-3 h-9 text-sm text-gray-950 transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
        aria-label="Until date"
      />
      {hasFilters && (
        <Button variant="ghost" size="sm" onClick={handleClear}>
          Clear filters
        </Button>
      )}
    </div>
  );
}
