import { useEffect, useCallback, useState } from "preact/hooks";

import type { RoleSummary } from "@/types";

import { listRoles } from "@/api/roles";
import { usePagination } from "@/hooks/use-pagination";
import { usePermission } from "@/hooks/use-permission";
import { formatDate } from "@/lib/format";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DataTable, type Column } from "@/components/data/data-table";
import { PaginationControls } from "@/components/data/pagination-controls";

import { RoleDetail } from "@/features/admin/role-detail";
import { RoleForm } from "@/features/admin/role-form";

interface RoleListProps {
  class?: string;
}

export function RoleList({ class: className }: RoleListProps): preact.JSX.Element {
  const { hasPermission } = usePermission();
  const canManage = hasPermission("roles.manage");

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [detailRoleId, setDetailRoleId] = useState<string | null>(null);

  const fetchFn = useCallback(
    (cursor: string | undefined, limit: number) => listRoles({ cursor, limit }),
    [],
  );

  const { data, isLoading, hasNext, total, loadMore, refresh } = usePagination<RoleSummary>(fetchFn);

  useEffect(() => {
    refresh();
  }, []);

  const handleCreateRole = (): void => {
    setIsFormOpen(true);
  };

  const handleRowClick = (role: RoleSummary): void => {
    setDetailRoleId(role.id);
  };

  const handleFormClose = (): void => {
    setIsFormOpen(false);
  };

  const handleFormSuccess = (): void => {
    setIsFormOpen(false);
    refresh();
  };

  const handleDetailClose = (): void => {
    setDetailRoleId(null);
  };

  const handleDetailRefresh = (): void => {
    setDetailRoleId(null);
    refresh();
  };

  const columns: Column<RoleSummary>[] = [
    {
      key: "name",
      header: "Name",
      render: (role) => (
        <span class="font-mono text-sm">{role.name}</span>
      ),
    },
    {
      key: "display_name",
      header: "Display Name",
    },
    {
      key: "description",
      header: "Description",
      render: (role) => (
        <span class="text-sm text-gray-500">{role.description ?? "\u2014"}</span>
      ),
    },
    {
      key: "is_system",
      header: "System",
      render: (role) =>
        role.is_system ? <Badge variant="primary">System</Badge> : null,
    },
    {
      key: "permission_count",
      header: "Permissions",
      render: (role) => (
        <Badge variant="default">{String(role.permission_count)}</Badge>
      ),
    },
    {
      key: "created_at",
      header: "Created",
      render: (role) => (
        <span class="text-sm text-gray-500">{formatDate(role.created_at)}</span>
      ),
    },
  ];

  return (
    <div class={className}>
      {canManage && (
        <div class="flex justify-end mb-4">
          <Button onClick={handleCreateRole}>Create Role</Button>
        </div>
      )}

      <DataTable<RoleSummary>
        columns={columns}
        data={data}
        onRowClick={handleRowClick}
        isLoading={isLoading && data.length === 0}
        emptyMessage="No roles found"
      />

      <PaginationControls
        hasNext={hasNext}
        isLoading={isLoading}
        total={total}
        currentCount={data.length}
        onLoadMore={loadMore}
      />

      {detailRoleId && (
        <RoleDetail
          roleId={detailRoleId}
          isOpen={!!detailRoleId}
          onClose={handleDetailClose}
          onRefresh={handleDetailRefresh}
        />
      )}

      <RoleForm
        isOpen={isFormOpen}
        onClose={handleFormClose}
        onSuccess={handleFormSuccess}
      />
    </div>
  );
}
