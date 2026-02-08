import { useState, useEffect } from "preact/hooks";

import type { RoleDetail as RoleDetailType } from "@/types";

import { getRoleDetail, deleteRole } from "@/api/roles";
import { ApiError } from "@/api/client";
import { usePermission } from "@/hooks/use-permission";

import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { ErrorState } from "@/components/data/error-state";
import { ConfirmationDialog } from "@/components/feedback/confirmation-dialog";

import { RoleForm } from "@/features/admin/role-form";

interface RoleDetailProps {
  roleId: string;
  isOpen: boolean;
  onClose: () => void;
  onRefresh?: () => void;
}

export function RoleDetail({
  roleId,
  isOpen,
  onClose,
  onRefresh,
}: RoleDetailProps): preact.JSX.Element {
  const { hasPermission } = usePermission();
  const canManage = hasPermission("roles.manage");

  const [role, setRole] = useState<RoleDetailType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (isOpen && roleId) {
      loadRole();
    }
  }, [isOpen, roleId]);

  const loadRole = async (): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getRoleDetail(roleId);
      setRole(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.error.message);
      } else {
        setError("Failed to load role details");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (): void => {
    setIsFormOpen(true);
  };

  const handleFormClose = (): void => {
    setIsFormOpen(false);
  };

  const handleFormSuccess = (): void => {
    setIsFormOpen(false);
    loadRole();
    onRefresh?.();
  };

  const handleDeleteClick = (): void => {
    setIsDeleteOpen(true);
  };

  const handleDeleteConfirm = async (): Promise<void> => {
    if (!role) return;
    setIsDeleting(true);
    try {
      await deleteRole(role.id);
      setIsDeleteOpen(false);
      onClose();
      onRefresh?.();
    } catch {
      // Error handled via toast in production
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteCancel = (): void => {
    setIsDeleteOpen(false);
  };

  const canDelete = role && !role.is_system && role.user_count === 0;

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title="Role Details"
        size="lg"
        footer={
          role && canManage && !role.is_system ? (
            <>
              {canDelete && (
                <Button variant="danger" onClick={handleDeleteClick}>
                  Delete
                </Button>
              )}
              <Button onClick={handleEdit}>
                Edit
              </Button>
            </>
          ) : undefined
        }
      >
        {isLoading && (
          <div class="flex items-center justify-center py-12">
            <Spinner size="lg" />
          </div>
        )}

        {error && (
          <ErrorState
            title="Failed to load role"
            message={error}
            onRetry={loadRole}
          />
        )}

        {!isLoading && !error && role && (
          <div class="space-y-6">
            <div class="space-y-3">
              <div class="flex items-center gap-3">
                <h3 class="text-base font-semibold text-gray-900">{role.display_name}</h3>
                {role.is_system && <Badge variant="primary">System</Badge>}
              </div>
              <p class="font-mono text-sm text-gray-500">{role.name}</p>
              {role.description && (
                <p class="text-sm text-gray-600">{role.description}</p>
              )}
              <p class="text-sm text-gray-500">
                {role.user_count} {role.user_count === 1 ? "user" : "users"} assigned
              </p>
            </div>

            <div>
              <h4 class="text-sm font-medium text-gray-900 mb-3">
                Permissions ({role.permissions.length})
              </h4>
              <div class="space-y-2">
                {role.permissions.map((perm) => (
                  <div
                    key={perm.id}
                    class="flex items-start gap-3 py-2 border-b border-gray-100 last:border-b-0"
                  >
                    <span class="font-mono text-sm text-indigo-600 flex-shrink-0">
                      {perm.code}
                    </span>
                    <span class="text-sm text-gray-600">{perm.description}</span>
                  </div>
                ))}
                {role.permissions.length === 0 && (
                  <p class="text-sm text-gray-500">No permissions assigned</p>
                )}
              </div>
            </div>
          </div>
        )}
      </Modal>

      {role && (
        <RoleForm
          isOpen={isFormOpen}
          onClose={handleFormClose}
          onSuccess={handleFormSuccess}
          role={role}
        />
      )}

      <ConfirmationDialog
        isOpen={isDeleteOpen}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        title="Delete Role"
        message={`Are you sure you want to delete the role "${role?.display_name ?? ""}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={isDeleting}
      />
    </>
  );
}
