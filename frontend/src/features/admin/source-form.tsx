import { useState, useEffect } from "preact/hooks";

import type { SourceSummary, SourceCreateResponse } from "@/types";

import { createSource, updateSource } from "@/api/sources";
import { ApiError } from "@/api/client";

import { Modal } from "@/components/ui/modal";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface SourceFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (response?: SourceCreateResponse) => void;
  source?: SourceSummary;
}

interface FormErrors {
  name?: string;
  general?: string;
}

export function SourceForm({
  isOpen,
  onClose,
  onSuccess,
  source,
}: SourceFormProps): preact.JSX.Element {
  const isEditMode = !!source;

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (source) {
        setName(source.name);
        setDescription(source.description ?? "");
        setIsActive(source.is_active);
      } else {
        setName("");
        setDescription("");
        setIsActive(true);
      }
      setErrors({});
    }
  }, [isOpen, source]);

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!name.trim()) {
      newErrors.name = "Name is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (): Promise<void> => {
    if (!validate()) return;

    setIsSubmitting(true);
    setErrors({});

    try {
      if (isEditMode && source) {
        await updateSource(source.id, {
          name,
          description: description || undefined,
          is_active: isActive,
        });
        onSuccess();
      } else {
        const response = await createSource({
          name,
          description: description || undefined,
        });
        onSuccess(response);
      }
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
      title={isEditMode ? "Edit Source" : "Register Source"}
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
            {isEditMode ? "Save Changes" : "Register"}
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

        <Input
          label="Name"
          type="text"
          value={name}
          onInput={(e) => setName((e.target as HTMLInputElement).value)}
          error={errors.name}
          placeholder="e.g., Salesforce, Jira"
        />

        <div class="w-full">
          <label htmlFor="source-description" class="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            id="source-description"
            value={description}
            onInput={(e) => setDescription((e.target as HTMLTextAreaElement).value)}
            placeholder="Optional description"
            rows={3}
            class="block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-950 placeholder:text-gray-500 transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        {isEditMode && (
          <div class="flex items-center gap-3">
            <input
              id="source-active-checkbox"
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive((e.target as HTMLInputElement).checked)}
              class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <label htmlFor="source-active-checkbox" class="text-sm font-medium text-gray-700">
              Active
            </label>
          </div>
        )}
      </form>
    </Modal>
  );
}
