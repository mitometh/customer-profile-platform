import { useState, useEffect } from "preact/hooks";

import type { RoleDetail, Permission } from "@/types";

import { createRole, updateRole, getPermissions } from "@/api/roles";
import { ApiError } from "@/api/client";

import { Modal } from "@/components/ui/modal";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

interface RoleFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  role?: RoleDetail;
}

interface FormErrors {
  name?: string;
  display_name?: string;
  permissions?: string;
  general?: string;
}

export function RoleForm({
  isOpen,
  onClose,
  onSuccess,
  role,
}: RoleFormProps): preact.JSX.Element {
  const isEditMode = !!role;

  const [name, setName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [description, setDescription] = useState("");
  const [allPermissions, setAllPermissions] = useState<Permission[]>([]);
  const [selectedPermissions, setSelectedPermissions] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingPermissions, setIsLoadingPermissions] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (role) {
        setName(role.name);
        setDisplayName(role.display_name);
        setDescription(role.description ?? "");
        setSelectedPermissions(new Set(role.permissions.map((p) => p.id)));
      } else {
        setName("");
        setDisplayName("");
        setDescription("");
        setSelectedPermissions(new Set());
      }
      setErrors({});
      loadPermissions();
    }
  }, [isOpen, role]);

  const loadPermissions = async (): Promise<void> => {
    setIsLoadingPermissions(true);
    try {
      const permissions = await getPermissions();
      setAllPermissions(permissions);
    } catch {
      // Permissions will remain empty
    } finally {
      setIsLoadingPermissions(false);
    }
  };

  const togglePermission = (permId: string): void => {
    setSelectedPermissions((prev) => {
      const next = new Set(prev);
      if (next.has(permId)) {
        next.delete(permId);
      } else {
        next.add(permId);
      }
      return next;
    });
  };

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!isEditMode && !name.trim()) {
      newErrors.name = "Name is required";
    }

    if (!displayName.trim()) {
      newErrors.display_name = "Display name is required";
    }

    if (selectedPermissions.size === 0) {
      newErrors.permissions = "At least one permission must be selected";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (): Promise<void> => {
    if (!validate()) return;

    setIsSubmitting(true);
    setErrors({});

    try {
      const permissionIds = Array.from(selectedPermissions);

      if (isEditMode && role) {
        await updateRole(role.id, {
          display_name: displayName,
          description: description || undefined,
          permissions: permissionIds,
        });
      } else {
        await createRole({
          name,
          display_name: displayName,
          description: description || undefined,
          permissions: permissionIds,
        });
      }
      onSuccess();
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors({ general: err.error.message });
      } else {
        setErrors({ general: "An unexpected error occurred" });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFormSubmit = (e: Event): void => {
    e.preventDefault();
    handleSubmit();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? "Edit Role" : "Create Role"}
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            loading={isSubmitting}
            disabled={isSubmitting}
          >
            {isEditMode ? "Save Changes" : "Create Role"}
          </Button>
        </>
      }
    >
      <form onSubmit={handleFormSubmit} class="space-y-4">
        {errors.general && (
          <div class="p-3 rounded-lg bg-red-100 text-red-700 text-sm">
            {errors.general}
          </div>
        )}

        {!isEditMode && (
          <Input
            label="Name"
            type="text"
            value={name}
            onInput={(e) => setName((e.target as HTMLInputElement).value)}
            error={errors.name}
            placeholder="e.g., custom_role"
          />
        )}

        <Input
          label="Display Name"
          type="text"
          value={displayName}
          onInput={(e) => setDisplayName((e.target as HTMLInputElement).value)}
          error={errors.display_name}
          placeholder="e.g., Custom Role"
        />

        <div class="w-full">
          <label htmlFor="role-description" class="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            id="role-description"
            value={description}
            onInput={(e) => setDescription((e.target as HTMLTextAreaElement).value)}
            placeholder="Optional description"
            rows={2}
            class="block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-950 placeholder:text-gray-500 transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        <div>
          <p class="text-sm font-medium text-gray-700 mb-2">Permissions</p>
          {errors.permissions && (
            <p class="mb-2 text-xs text-red-600">{errors.permissions}</p>
          )}

          {isLoadingPermissions ? (
            <div class="flex items-center justify-center py-6">
              <Spinner size="md" />
            </div>
          ) : (
            <div class="grid grid-cols-1 gap-2 max-h-64 overflow-y-auto border border-gray-200 rounded-lg p-3">
              {allPermissions.map((perm) => (
                <label
                  key={perm.id}
                  class="flex items-start gap-3 py-1.5 cursor-pointer hover:bg-gray-50 rounded px-1"
                >
                  <input
                    type="checkbox"
                    checked={selectedPermissions.has(perm.id)}
                    onChange={() => togglePermission(perm.id)}
                    class="mt-0.5 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <div class="flex-1 min-w-0">
                    <span class="font-mono text-sm text-indigo-600 block">{perm.code}</span>
                    <span class="text-sm text-gray-600">{perm.description}</span>
                  </div>
                </label>
              ))}
              {allPermissions.length === 0 && (
                <p class="text-sm text-gray-500 text-center py-4">No permissions available</p>
              )}
            </div>
          )}
        </div>
      </form>
    </Modal>
  );
}
