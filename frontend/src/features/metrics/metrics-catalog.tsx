import { useState, useEffect } from "preact/hooks";

import type { MetricCatalogEntry } from "@/types";

import { getCatalog, deleteMetric } from "@/api/metrics";
import { ApiError } from "@/api/client";
import { usePermission } from "@/hooks/use-permission";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/data/empty-state";
import { ErrorState } from "@/components/data/error-state";
import { ConfirmationDialog } from "@/components/feedback/confirmation-dialog";

import { MetricForm } from "@/features/metrics/metric-form";

interface MetricsCatalogProps {
  class?: string;
}

export function MetricsCatalog({ class: className }: MetricsCatalogProps): preact.JSX.Element {
  const { hasPermission } = usePermission();
  const canManage = hasPermission("metrics.catalog.manage");

  const [metrics, setMetrics] = useState<MetricCatalogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingMetric, setEditingMetric] = useState<MetricCatalogEntry | undefined>(undefined);
  const [deletingMetric, setDeletingMetric] = useState<MetricCatalogEntry | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const loadCatalog = async (): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getCatalog();
      setMetrics(response.metrics);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.error.message);
      } else {
        setError("Failed to load metrics catalog");
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCatalog();
  }, []);

  const handleCreate = (): void => {
    setEditingMetric(undefined);
    setIsFormOpen(true);
  };

  const handleEdit = (metric: MetricCatalogEntry): void => {
    setEditingMetric(metric);
    setIsFormOpen(true);
  };

  const handleFormClose = (): void => {
    setIsFormOpen(false);
    setEditingMetric(undefined);
  };

  const handleFormSuccess = (): void => {
    setIsFormOpen(false);
    setEditingMetric(undefined);
    loadCatalog();
  };

  const handleDeleteClick = (metric: MetricCatalogEntry): void => {
    setDeletingMetric(metric);
  };

  const handleDeleteConfirm = async (): Promise<void> => {
    if (!deletingMetric) return;
    setIsDeleting(true);
    try {
      await deleteMetric(deletingMetric.id);
      setDeletingMetric(null);
      loadCatalog();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.error.message);
      } else {
        setError("Failed to delete metric");
      }
      setDeletingMetric(null);
    } finally {
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return (
      <div class={className}>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardBody>
                <Skeleton height="20px" width="60%" class="mb-3" />
                <Skeleton height="14px" width="40%" class="mb-2" />
                <Skeleton height="14px" width="100%" class="mb-2" />
                <Skeleton height="14px" width="80%" />
              </CardBody>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error && metrics.length === 0) {
    return (
      <div class={className}>
        <ErrorState
          title="Failed to load catalog"
          message={error}
          onRetry={loadCatalog}
        />
      </div>
    );
  }

  if (metrics.length === 0) {
    return (
      <div class={className}>
        <EmptyState
          title="No metrics defined"
          description="The metrics catalog is currently empty."
        />
        {canManage && (
          <div class="flex justify-center mt-4">
            <Button onClick={handleCreate}>Create First Metric</Button>
          </div>
        )}

        <MetricForm
          isOpen={isFormOpen}
          onClose={handleFormClose}
          onSuccess={handleFormSuccess}
          metric={editingMetric}
        />
      </div>
    );
  }

  return (
    <div class={className}>
      {canManage && (
        <div class="flex justify-end mb-4">
          <Button onClick={handleCreate}>Create Metric</Button>
        </div>
      )}

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {metrics.map((metric) => (
          <Card key={metric.id}>
            <CardBody>
              <div class="space-y-2">
                <div class="flex items-start justify-between">
                  <h3 class="text-base font-semibold text-gray-900">
                    {metric.display_name}
                  </h3>
                  {canManage && (
                    <div class="flex items-center gap-1 ml-2 flex-shrink-0">
                      <button
                        type="button"
                        onClick={() => handleEdit(metric)}
                        class="p-1 text-gray-400 hover:text-indigo-600 transition-colors rounded"
                        aria-label={`Edit ${metric.display_name}`}
                      >
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                          <path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
                        </svg>
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteClick(metric)}
                        class="p-1 text-gray-400 hover:text-red-600 transition-colors rounded"
                        aria-label={`Delete ${metric.display_name}`}
                      >
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                          <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                        </svg>
                      </button>
                    </div>
                  )}
                </div>
                <p class="font-mono text-xs text-gray-500">{metric.name}</p>
                {metric.description && (
                  <p class="text-sm text-gray-600">{metric.description}</p>
                )}
                <div class="flex items-center gap-2 pt-1">
                  {metric.unit && <Badge variant="default">{metric.unit}</Badge>}
                  <Badge variant="primary">{metric.value_type}</Badge>
                </div>
              </div>
            </CardBody>
          </Card>
        ))}
      </div>

      <MetricForm
        isOpen={isFormOpen}
        onClose={handleFormClose}
        onSuccess={handleFormSuccess}
        metric={editingMetric}
      />

      <ConfirmationDialog
        isOpen={!!deletingMetric}
        onClose={() => setDeletingMetric(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Metric"
        message={`Are you sure you want to delete "${deletingMetric?.display_name ?? ""}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
}
