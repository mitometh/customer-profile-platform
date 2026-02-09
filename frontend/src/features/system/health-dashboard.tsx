import { useState, useEffect, useRef } from "preact/hooks";

import type { HealthResponse } from "@/api/health";

import { getHealth } from "@/api/health";
import { ApiError } from "@/api/client";

import { Card, CardBody } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/data/error-state";
import { StatusIndicator } from "@/components/feedback/status-indicator";

interface HealthDashboardProps {
  class?: string;
}

const SERVICE_LABELS: Record<string, string> = {
  database: "Database",
  redis: "Redis",
  message_broker: "Message Broker",
  llm_provider: "LLM Provider",
};

const STATUS_LABELS: Record<string, string> = {
  healthy: "All Systems Operational",
  degraded: "Degraded Performance",
  unhealthy: "System Outage",
};

const REFRESH_INTERVAL_MS = 30_000;

export function HealthDashboard({ class: className }: HealthDashboardProps): preact.JSX.Element {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadHealth = async (): Promise<void> => {
    setIsLoading((prev) => health === null ? true : prev);
    setError(null);
    try {
      const data = await getHealth();
      setHealth(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.error.message);
      } else {
        setError("Failed to load health status");
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();

    intervalRef.current = setInterval(() => {
      loadHealth();
    }, REFRESH_INTERVAL_MS);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (isLoading && !health) {
    return (
      <div class={className}>
        <Card class="mb-6">
          <CardBody>
            <Skeleton height="32px" width="200px" class="mb-2" />
            <Skeleton height="16px" width="160px" />
          </CardBody>
        </Card>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardBody>
                <Skeleton height="16px" width="120px" class="mb-3" />
                <Skeleton height="20px" width="60px" />
              </CardBody>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error && !health) {
    return (
      <div class={className}>
        <ErrorState
          title="Failed to load health status"
          message={error}
          onRetry={loadHealth}
        />
      </div>
    );
  }

  if (!health) {
    return <div class={className} />;
  }

  const checkEntries = Object.entries(health.checks);

  return (
    <div class={className}>
      <Card class="mb-6">
        <CardBody>
          <div class="flex items-center gap-4">
            <StatusIndicator status={health.status} />
            <div>
              <h2 class="text-lg font-semibold text-gray-900">
                {STATUS_LABELS[health.status] ?? health.status}
              </h2>
              <p class="text-sm text-gray-500">
                Overall system status
              </p>
            </div>
          </div>
        </CardBody>
      </Card>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {checkEntries.map(([key, value]) => {
          const isUp = value === "up";
          const label = isUp ? "Up" : value === "not_checked" ? "Not Checked" : "Down";
          const indicatorStatus = isUp ? "up" : value === "not_checked" ? "degraded" : "down";

          return (
            <Card key={key}>
              <CardBody>
                <div class="flex items-center justify-between">
                  <p class="text-sm font-medium text-gray-900">
                    {SERVICE_LABELS[key] ?? key}
                  </p>
                  <StatusIndicator
                    status={indicatorStatus}
                    label={label}
                  />
                </div>
              </CardBody>
            </Card>
          );
        })}
      </div>

      <div class="mt-6 text-sm text-gray-500">
        Version: {health.version}
      </div>
    </div>
  );
}
