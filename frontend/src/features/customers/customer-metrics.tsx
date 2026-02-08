import { useState } from "preact/hooks";

import type { CustomerMetricValue } from "@/types";

import { cn } from "@/lib/cn";
import { formatMetricValue } from "@/lib/format";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

import { MetricTrendChart } from "@/features/customers/metric-trend-chart";

interface CustomerMetricsProps {
  metrics: CustomerMetricValue[];
  customerId: string;
}

function getHealthStatus(value: number): { label: string; variant: "success" | "warning" | "danger" } {
  if (value >= 70) return { label: "Healthy", variant: "success" };
  if (value >= 40) return { label: "Needs Attention", variant: "warning" };
  return { label: "At Risk", variant: "danger" };
}

function getHealthValueColor(value: number): string {
  if (value >= 70) return "text-green-700";
  if (value >= 40) return "text-amber-700";
  return "text-red-700";
}

function getHealthBarColor(value: number): string {
  if (value >= 70) return "bg-green-500";
  if (value >= 40) return "bg-amber-500";
  return "bg-red-500";
}

function isHealthScore(metric: CustomerMetricValue): boolean {
  return metric.metric_name === "health_score" || metric.display_name.toLowerCase().includes("health");
}

export function CustomerMetrics({ metrics, customerId }: CustomerMetricsProps): preact.JSX.Element {
  const [expandedMetricId, setExpandedMetricId] = useState<string | null>(null);

  const handleToggleTrend = (metricId: string): void => {
    setExpandedMetricId((prev) => (prev === metricId ? null : metricId));
  };

  if (metrics.length === 0) {
    return (
      <div class="py-8 text-center">
        <p class="text-sm text-gray-500">No metrics available</p>
      </div>
    );
  }

  return (
    <div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric) => {
          const isHealth = isHealthScore(metric);
          const healthStatus = isHealth ? getHealthStatus(metric.metric_value) : null;

          return (
            <Card
              key={metric.metric_definition_id}
              class="cursor-pointer hover:border-indigo-200 transition-colors"
            >
              <div
                class="p-4"
                onClick={() => handleToggleTrend(metric.metric_definition_id)}
              >
                <p class="text-xs text-gray-500 truncate">{metric.display_name}</p>
                <div class="flex items-baseline mt-1">
                  <span
                    class={cn(
                      "text-2xl font-bold",
                      isHealth ? getHealthValueColor(metric.metric_value) : "text-gray-900",
                    )}
                  >
                    {formatMetricValue(metric.metric_value, metric.value_type, metric.unit)}
                  </span>
                  {metric.unit && !isHealth && (
                    <span class="text-sm text-gray-500 ml-1">{metric.unit}</span>
                  )}
                </div>
                {isHealth && healthStatus && (
                  <>
                    <div class="mt-2 h-2 w-full rounded-full bg-gray-100">
                      <div
                        class={cn("h-2 rounded-full", getHealthBarColor(metric.metric_value))}
                        style={{ width: `${Math.min(100, Math.max(0, metric.metric_value))}%` }}
                      />
                    </div>
                    <div class="mt-2">
                      <Badge variant={healthStatus.variant}>{healthStatus.label}</Badge>
                    </div>
                  </>
                )}
              </div>
            </Card>
          );
        })}
      </div>
      {expandedMetricId && (
        <div class="mt-4">
          <MetricTrendChart
            customerId={customerId}
            metricId={expandedMetricId}
            metricName={
              metrics.find((m) => m.metric_definition_id === expandedMetricId)?.display_name ?? ""
            }
          />
        </div>
      )}
    </div>
  );
}
