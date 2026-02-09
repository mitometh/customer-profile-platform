import { useEffect, useCallback, useState } from "preact/hooks";

import type { SourceSummary, SourceCreateResponse } from "@/types";

import { listSources, deleteSource } from "@/api/sources";
import { usePagination } from "@/hooks/use-pagination";
import { usePermission } from "@/hooks/use-permission";
import { formatDate } from "@/lib/format";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DataTable, type Column } from "@/components/data/data-table";
import { PaginationControls } from "@/components/data/pagination-controls";
import { ConfirmationDialog } from "@/components/feedback/confirmation-dialog";

import { SourceForm } from "@/features/admin/source-form";
import { SourceTokenModal } from "@/features/admin/source-token-modal";

interface SourceListProps {
  class?: string;
}

export function SourceList({ class: className }: SourceListProps): preact.JSX.Element {
  const { hasPermission } = usePermission();
  const canManage = hasPermission("sources.manage");

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingSource, setEditingSource] = useState<SourceSummary | undefined>(undefined);
  const [deleteTarget, setDeleteTarget] = useState<SourceSummary | undefined>(undefined);
  const [isDeleting, setIsDeleting] = useState(false);
  const [tokenModalData, setTokenModalData] = useState<{ token: string; sourceName: string } | null>(null);

  const fetchFn = useCallback(
    (cursor: string | undefined, limit: number) => listSources({ cursor, limit }),
    [],
  );

  const { data, isLoading, hasNext, total, loadMore, refresh } = usePagination<SourceSummary>(fetchFn);

  useEffect(() => {
    refresh();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleRegister = (): void => {
    setEditingSource(undefined);
    setIsFormOpen(true);
  };

  const handleEdit = (source: SourceSummary): void => {
    setEditingSource(source);
    setIsFormOpen(true);
  };

  const handleFormClose = (): void => {
    setIsFormOpen(false);
    setEditingSource(undefined);
  };

  const handleFormSuccess = (response?: SourceCreateResponse): void => {
    setIsFormOpen(false);
    setEditingSource(undefined);
    if (response) {
      setTokenModalData({ token: response.api_token, sourceName: response.name });
    }
    refresh();
  };

  const handleDeleteClick = (source: SourceSummary): void => {
    setDeleteTarget(source);
  };

  const handleDeleteConfirm = async (): Promise<void> => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deleteSource(deleteTarget.id);
      setDeleteTarget(undefined);
      refresh();
    } catch {
      // Error is displayed via toast in a real app
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteCancel = (): void => {
    setDeleteTarget(undefined);
  };

  const handleTokenModalClose = (): void => {
    setTokenModalData(null);
  };

  const columns: Column<SourceSummary>[] = [
    {
      key: "name",
      header: "Name",
      render: (source) => (
        <span class="font-medium text-gray-900">{source.name}</span>
      ),
    },
    {
      key: "description",
      header: "Description",
      render: (source) => (
        <span class="text-sm text-gray-500">{source.description ?? "\u2014"}</span>
      ),
    },
    {
      key: "is_active",
      header: "Status",
      render: (source) => (
        <Badge variant={source.is_active ? "success" : "danger"}>
          {source.is_active ? "Active" : "Inactive"}
        </Badge>
      ),
    },
    {
      key: "created_at",
      header: "Created",
      render: (source) => (
        <span class="text-sm text-gray-500">{formatDate(source.created_at)}</span>
      ),
    },
  ];

  if (canManage) {
    columns.push({
      key: "actions",
      header: "",
      render: (source) => (
        <div class="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
          <Button variant="ghost" size="sm" onClick={() => handleEdit(source)}>
            Edit
          </Button>
          <Button variant="ghost" size="sm" onClick={() => handleDeleteClick(source)}>
            Delete
          </Button>
        </div>
      ),
    });
  }

  return (
    <div class={className}>
      {canManage && (
        <div class="flex justify-end mb-4">
          <Button onClick={handleRegister}>Register Source</Button>
        </div>
      )}

      <DataTable<SourceSummary>
        columns={columns}
        data={data}
        isLoading={isLoading && data.length === 0}
        emptyMessage="No sources found"
      />

      <PaginationControls
        hasNext={hasNext}
        isLoading={isLoading}
        total={total}
        currentCount={data.length}
        onLoadMore={loadMore}
      />

      <SourceForm
        isOpen={isFormOpen}
        onClose={handleFormClose}
        onSuccess={handleFormSuccess}
        source={editingSource}
      />

      <ConfirmationDialog
        isOpen={!!deleteTarget}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        title="Delete Source"
        message={`Are you sure you want to delete "${deleteTarget?.name ?? ""}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={isDeleting}
      />

      {tokenModalData && (
        <SourceTokenModal
          isOpen={!!tokenModalData}
          onClose={handleTokenModalClose}
          token={tokenModalData.token}
          sourceName={tokenModalData.sourceName}
        />
      )}
    </div>
  );
}
