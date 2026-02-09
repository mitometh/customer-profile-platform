import { useState, useEffect } from "preact/hooks";

import type { UserSummary, RoleSummary } from "@/types";

import { createUser, updateUser } from "@/api/users";
import { listRoles } from "@/api/roles";
import { ApiError } from "@/api/client";

import { Modal } from "@/components/ui/modal";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface UserFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  user?: UserSummary;
}

interface FormErrors {
  email?: string;
  full_name?: string;
  password?: string;
  role_id?: string;
  general?: string;
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;

export function UserForm({
  isOpen,
  onClose,
  onSuccess,
  user,
}: UserFormProps): preact.JSX.Element {
  const isEditMode = !!user;

  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [roleId, setRoleId] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [roles, setRoles] = useState<RoleSummary[]>([]);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (user) {
        setEmail(user.email);
        setFullName(user.full_name);
        setPassword("");
        setIsActive(user.is_active);
        setRoleId("");
      } else {
        setEmail("");
        setFullName("");
        setPassword("");
        setRoleId("");
        setIsActive(true);
      }
      setErrors({});
      loadRoles();
    }
  }, [isOpen, user]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadRoles = async (): Promise<void> => {
    try {
      const response = await listRoles({ limit: 100 });
      setRoles(response.data);
      if (user) {
        const matchingRole = response.data.find((r) => r.display_name === user.role || r.name === user.role);
        if (matchingRole) {
          setRoleId(matchingRole.id);
        }
      }
    } catch {
      // Roles will remain empty; user can retry
    }
  };

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!fullName.trim()) {
      newErrors.full_name = "Full name is required";
    }

    if (!isEditMode) {
      if (!email.trim()) {
        newErrors.email = "Email is required";
      } else if (!EMAIL_REGEX.test(email)) {
        newErrors.email = "Please enter a valid email address";
      }

      if (!password) {
        newErrors.password = "Password is required";
      } else if (!PASSWORD_REGEX.test(password)) {
        newErrors.password = "Password must be at least 8 characters with 1 uppercase, 1 lowercase, and 1 digit";
      }
    }

    if (!roleId) {
      newErrors.role_id = "Role is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (): Promise<void> => {
    if (!validate()) return;

    setIsSubmitting(true);
    setErrors({});

    try {
      if (isEditMode && user) {
        await updateUser(user.id, {
          full_name: fullName,
          role_id: roleId,
          is_active: isActive,
        });
      } else {
        await createUser({
          email,
          full_name: fullName,
          password,
          role_id: roleId,
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
      title={isEditMode ? "Edit User" : "Create User"}
      size="md"
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
            {isEditMode ? "Save Changes" : "Create User"}
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
            label="Email"
            type="email"
            value={email}
            onInput={(e) => setEmail((e.target as HTMLInputElement).value)}
            error={errors.email}
            placeholder="user@example.com"
          />
        )}

        <Input
          label="Full Name"
          type="text"
          value={fullName}
          onInput={(e) => setFullName((e.target as HTMLInputElement).value)}
          error={errors.full_name}
          placeholder="John Doe"
        />

        {!isEditMode && (
          <Input
            label="Password"
            type="password"
            value={password}
            onInput={(e) => setPassword((e.target as HTMLInputElement).value)}
            error={errors.password}
            placeholder="Minimum 8 characters"
          />
        )}

        <div class="w-full">
          <label htmlFor="role-select" class="block text-sm font-medium text-gray-700 mb-1">
            Role
          </label>
          <select
            id="role-select"
            value={roleId}
            onChange={(e) => setRoleId((e.target as HTMLSelectElement).value)}
            class={`block w-full rounded-lg border px-3 h-9 text-sm text-gray-950 transition-colors ${
              errors.role_id
                ? "border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500"
                : "border-gray-300 bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            }`}
          >
            <option value="">Select a role</option>
            {roles.map((role) => (
              <option key={role.id} value={role.id}>
                {role.display_name}
              </option>
            ))}
          </select>
          {errors.role_id && (
            <p class="mt-1 text-xs text-red-600">{errors.role_id}</p>
          )}
        </div>

        {isEditMode && (
          <div class="flex items-center gap-3">
            <input
              id="is-active-checkbox"
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive((e.target as HTMLInputElement).checked)}
              class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <label htmlFor="is-active-checkbox" class="text-sm font-medium text-gray-700">
              Active
            </label>
          </div>
        )}
      </form>
    </Modal>
  );
}
