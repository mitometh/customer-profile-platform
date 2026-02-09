import { useEffect, useCallback } from "preact/hooks";

import type { UserSummary } from "@/types";

import { listUsers } from "@/api/users";
import { usePagination } from "@/hooks/use-pagination";
import { usePermission } from "@/hooks/use-permission";
import { formatDate } from "@/lib/format";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DataTable, type Column } from "@/components/data/data-table";
import { PaginationControls } from "@/components/data/pagination-controls";

import { UserForm } from "@/features/admin/user-form";

import { useState } from "preact/hooks";

interface UserListProps {
  class?: string;
}

export function UserList({ class: className }: UserListProps): preact.JSX.Element {
  const { hasPermission } = usePermission();
  const canManage = hasPermission("users.manage");

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserSummary | undefined>(undefined);

  const fetchFn = useCallback(
    (cursor: string | undefined, limit: number) => listUsers({ cursor, limit }),
    [],
  );

  const { data, isLoading, hasNext, total, loadMore, refresh } = usePagination<UserSummary>(fetchFn);

  useEffect(() => {
    refresh();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleRowClick = (user: UserSummary): void => {
    if (!canManage) return;
    setEditingUser(user);
    setIsFormOpen(true);
  };

  const handleAddUser = (): void => {
    setEditingUser(undefined);
    setIsFormOpen(true);
  };

  const handleFormClose = (): void => {
    setIsFormOpen(false);
    setEditingUser(undefined);
  };

  const handleFormSuccess = (): void => {
    setIsFormOpen(false);
    setEditingUser(undefined);
    refresh();
  };

  const columns: Column<UserSummary>[] = [
    {
      key: "full_name",
      header: "Name",
      render: (user) => (
        <span class="font-medium text-gray-900">{user.full_name}</span>
      ),
    },
    {
      key: "email",
      header: "Email",
    },
    {
      key: "role",
      header: "Role",
      render: (user) => (
        <Badge variant="primary">{user.role}</Badge>
      ),
    },
    {
      key: "is_active",
      header: "Status",
      render: (user) => (
        <Badge variant={user.is_active ? "success" : "danger"}>
          {user.is_active ? "Active" : "Inactive"}
        </Badge>
      ),
    },
    {
      key: "last_login_at",
      header: "Last Login",
      render: (user) => (
        <span class="text-sm text-gray-500">
          {user.last_login_at ? formatDate(user.last_login_at) : "Never"}
        </span>
      ),
    },
  ];

  return (
    <div class={className}>
      {canManage && (
        <div class="flex justify-end mb-4">
          <Button onClick={handleAddUser}>Add User</Button>
        </div>
      )}

      <DataTable<UserSummary>
        columns={columns}
        data={data}
        onRowClick={canManage ? handleRowClick : undefined}
        isLoading={isLoading && data.length === 0}
        emptyMessage="No users found"
      />

      <PaginationControls
        hasNext={hasNext}
        isLoading={isLoading}
        total={total}
        currentCount={data.length}
        onLoadMore={loadMore}
      />

      <UserForm
        isOpen={isFormOpen}
        onClose={handleFormClose}
        onSuccess={handleFormSuccess}
        user={editingUser}
      />
    </div>
  );
}
