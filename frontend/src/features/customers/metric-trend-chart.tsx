import { useState, useEffect } from "preact/hooks";

import type { CustomerMetricTrend } from "@/types";

import { getMetricHistory } from "@/api/metrics";
import { formatDate } from "@/lib/format";

import { Card, CardHeader, CardBody } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface MetricTrendChartProps {
  customerId: string;
  metricId: string;
  metricName: string;
}

const CHART_WIDTH = 600;
const CHART_HEIGHT = 160;
const PADDING_TOP = 20;
const PADDING_BOTTOM = 30;
const PADDING_LEFT = 50;
const PADDING_RIGHT = 20;

function buildPolyline(
  points: { x: number; y: number }[],
): string {
  return points.map((p) => `${p.x},${p.y}`).join(" ");
}

export function MetricTrendChart({
  customerId,
  metricId,
  metricName,
}: MetricTrendChartProps): preact.JSX.Element {
  const [trend, setTrend] = useState<CustomerMetricTrend | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    getMetricHistory(customerId, metricId, { limit: 90 })
      .then((data) => {
        if (!cancelled) {
          setTrend(data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError("Failed to load trend data");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [customerId, metricId]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader title={`${metricName} Trend`} />
        <CardBody>
          <Skeleton class="w-full h-48 rounded-lg" />
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader title={`${metricName} Trend`} />
        <CardBody>
          <p class="text-sm text-gray-500 text-center py-8">{error}</p>
        </CardBody>
      </Card>
    );
  }

  if (!trend || trend.data_points.length === 0) {
    return (
      <Card>
        <CardHeader title={`${metricName} Trend`} />
        <CardBody>
          <p class="text-sm text-gray-500 text-center py-8">No trend data available</p>
        </CardBody>
      </Card>
    );
  }

  const dataPoints = trend.data_points;
  const values = dataPoints.map((d) => d.metric_value);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const valRange = maxVal - minVal || 1;

  const plotWidth = CHART_WIDTH - PADDING_LEFT - PADDING_RIGHT;
  const plotHeight = CHART_HEIGHT - PADDING_TOP - PADDING_BOTTOM;

  const points = dataPoints.map((d, i) => ({
    x: PADDING_LEFT + (dataPoints.length > 1 ? (i / (dataPoints.length - 1)) * plotWidth : plotWidth / 2),
    y: PADDING_TOP + plotHeight - ((d.metric_value - minVal) / valRange) * plotHeight,
    value: d.metric_value,
    date: d.recorded_at,
  }));

  const yLabels = [minVal, minVal + valRange / 2, maxVal];
  const xLabelCount = Math.min(5, dataPoints.length);
  const xIndices = Array.from(
    { length: xLabelCount },
    (_, i) => Math.round((i / (xLabelCount - 1 || 1)) * (dataPoints.length - 1)),
  );

  return (
    <Card>
      <CardHeader title={`${metricName} Trend`} />
      <CardBody class="p-4">
        <svg
          viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
          class="w-full h-48 bg-gray-50 rounded-lg border border-gray-200"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Y-axis gridlines and labels */}
          {yLabels.map((val) => {
            const y = PADDING_TOP + plotHeight - ((val - minVal) / valRange) * plotHeight;
            return (
              <g key={val}>
                <line
                  x1={PADDING_LEFT}
                  y1={y}
                  x2={CHART_WIDTH - PADDING_RIGHT}
                  y2={y}
                  stroke="#e2e8f0"
                  stroke-width="1"
                />
                <text
                  x={PADDING_LEFT - 8}
                  y={y + 4}
                  text-anchor="end"
                  class="text-[10px] fill-gray-500"
                >
                  {val % 1 === 0 ? val : val.toFixed(1)}
                </text>
              </g>
            );
          })}

          {/* Line */}
          <polyline
            points={buildPolyline(points)}
            fill="none"
            stroke="#6366f1"
            stroke-width="2"
            stroke-linejoin="round"
            stroke-linecap="round"
          />

          {/* Data points */}
          {points.map((p, i) => (
            <circle
              key={i}
              cx={p.x}
              cy={p.y}
              r="3"
              fill="#6366f1"
              stroke="white"
              stroke-width="1.5"
            />
          ))}

          {/* X-axis labels */}
          {xIndices.map((idx) => {
            const pt = points[idx];
            if (!pt) return null;
            const dp = dataPoints[idx];
            if (!dp) return null;
            return (
              <text
                key={idx}
                x={pt.x}
                y={CHART_HEIGHT - 4}
                text-anchor="middle"
                class="text-[9px] fill-gray-500"
              >
                {formatDate(dp.recorded_at)}
              </text>
            );
          })}
        </svg>
      </CardBody>
    </Card>
  );
}
