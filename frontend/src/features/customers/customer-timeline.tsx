import { useState, useEffect, useCallback } from "preact/hooks";

import type { EventSummary, EventFilters, EventType } from "@/types";

import { getCustomerEvents } from "@/api/events";
import { cn } from "@/lib/cn";
import { formatDateTime } from "@/lib/format";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { PaginationControls } from "@/components/data/pagination-controls";
import { EmptyState } from "@/components/data/empty-state";

import { EventFilterBar } from "@/features/customers/event-filter-bar";

interface CustomerTimelineProps {
  customerId: string;
}

const EVENT_DOT_COLORS: Record<EventType, string> = {
  support_ticket: "bg-amber-500",
  meeting: "bg-indigo-500",
  usage_event: "bg-gray-500",
};

const EVENT_BORDER_COLORS: Record<EventType, string> = {
  support_ticket: "border-l-amber-300",
  meeting: "border-l-indigo-300",
  usage_event: "border-l-gray-300",
};

const EVENT_BADGE_VARIANTS: Record<EventType, "warning" | "primary" | "default"> = {
  support_ticket: "warning",
  meeting: "primary",
  usage_event: "default",
};

const EVENT_TYPE_LABELS: Record<EventType, string> = {
  support_ticket: "Support Ticket",
  meeting: "Meeting",
  usage_event: "Usage Event",
};

export function CustomerTimeline({ customerId }: CustomerTimelineProps): preact.JSX.Element {
  const [events, setEvents] = useState<EventSummary[]>([]);
  const [filters, setFilters] = useState<EventFilters>({});
  const [isLoading, setIsLoading] = useState(true);
  const [hasNext, setHasNext] = useState(false);
  const [total, setTotal] = useState<number | null>(null);
  const [nextCursor, setNextCursor] = useState<string | undefined>(undefined);

  const fetchEvents = useCallback(
    async (cursor?: string, append: boolean = false): Promise<void> => {
      setIsLoading(true);
      try {
        const response = await getCustomerEvents(customerId, {
          ...filters,
          cursor,
        });
        if (append) {
          setEvents((prev) => [...prev, ...response.data]);
        } else {
          setEvents(response.data);
        }
        setHasNext(response.pagination.has_next);
        setTotal(response.pagination.total);
        setNextCursor(response.pagination.next_cursor ?? undefined);
      } catch {
        // Error is handled by clearing data on failure
        if (!append) {
          setEvents([]);
        }
      } finally {
        setIsLoading(false);
      }
    },
    [customerId, filters],
  );

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const handleLoadMore = (): void => {
    if (nextCursor) {
      fetchEvents(nextCursor, true);
    }
  };

  const handleFilterChange = (newFilters: EventFilters): void => {
    setFilters(newFilters);
  };

  return (
    <div>
      <div class="mb-4">
        <EventFilterBar filters={filters} onChange={handleFilterChange} />
      </div>

      {isLoading && events.length === 0 && (
        <div class="space-y-4 pl-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} class="flex gap-4">
              <Skeleton class="w-3 h-3 rounded-full flex-shrink-0 mt-1" />
              <div class="flex-1 space-y-2">
                <Skeleton class="h-4 w-32" />
                <Skeleton class="h-24 w-full rounded-lg" />
              </div>
            </div>
          ))}
        </div>
      )}

      {!isLoading && events.length === 0 && (
        <EmptyState
          title="No events found"
          description="No activity events match the current filters."
        />
      )}

      {events.length > 0 && (
        <div class="relative">
          {/* Vertical timeline line */}
          <div class="absolute left-[5px] top-2 bottom-2 border-l-2 border-gray-200" />

          <div class="space-y-6">
            {events.map((event) => (
              <div key={event.id} class="relative pl-8">
                {/* Timeline dot */}
                <div
                  class={cn(
                    "absolute left-0 top-1 w-3 h-3 rounded-full",
                    EVENT_DOT_COLORS[event.event_type],
                  )}
                />

                {/* Date */}
                <p class="text-xs text-gray-500 mb-1">
                  {formatDateTime(event.occurred_at)}
                </p>

                {/* Event card */}
                <div
                  class={cn(
                    "border-l-[3px] bg-white rounded-lg p-4 border border-gray-200",
                    EVENT_BORDER_COLORS[event.event_type],
                  )}
                >
                  <div class="flex items-center justify-between gap-2">
                    <h4 class="text-sm font-medium text-gray-900 truncate">
                      {event.title}
                    </h4>
                    <div class="flex items-center gap-2 flex-shrink-0">
                      <Badge variant={EVENT_BADGE_VARIANTS[event.event_type]}>
                        {EVENT_TYPE_LABELS[event.event_type]}
                      </Badge>
                      {event.source_name && (
                        <Badge>{event.source_name}</Badge>
                      )}
                    </div>
                  </div>

                  {event.description && (
                    <p class="text-sm text-gray-600 mt-1">{event.description}</p>
                  )}

                  {event.data && Object.keys(event.data).length > 0 && (
                    <div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                      {Object.entries(event.data).map(([key, val]) => (
                        <span key={key}>
                          <span class="font-medium">{key}</span>: {String(val)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {events.length > 0 && (
        <div class="mt-4">
          <PaginationControls
            hasNext={hasNext}
            isLoading={isLoading}
            total={total}
            currentCount={events.length}
            onLoadMore={handleLoadMore}
          />
        </div>
      )}
    </div>
  );
}
