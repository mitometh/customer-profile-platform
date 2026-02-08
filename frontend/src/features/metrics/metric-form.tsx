import { useState, useEffect } from "preact/hooks";

import type { MetricCatalogEntry, MetricValueType } from "@/types";

import { createMetric, updateMetric } from "@/api/metrics";
import { ApiError } from "@/api/client";

import { Modal } from "@/components/ui/modal";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface MetricFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  metric?: MetricCatalogEntry;
}

interface FormErrors {
  name?: string;
  display_name?: string;
  value_type?: string;
  general?: string;
}

const VALUE_TYPES: { value: MetricValueType; label: string }[] = [
  { value: "integer", label: "Integer" },
  { value: "decimal", label: "Decimal" },
  { value: "percentage", label: "Percentage" },
];

export function MetricForm({
  isOpen,
  onClose,
  onSuccess,
  metric,
}: MetricFormProps): preact.JSX.Element {
  const isEditMode = !!metric;

  const [name, setName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [description, setDescription] = useState("");
  const [unit, setUnit] = useState("");
  const [valueType, setValueType] = useState<MetricValueType>("integer");
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (metric) {
        setName(metric.name);
        setDisplayName(metric.display_name);
        setDescription(metric.description ?? "");
        setUnit(metric.unit ?? "");
        setValueType(metric.value_type);
      } else {
        setName("");
        setDisplayName("");
        setDescription("");
        setUnit("");
        setValueType("integer");
      }
      setErrors({});
    }
  }, [isOpen, metric]);

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!isEditMode && !name.trim()) {
      newErrors.name = "Name is required";
    }

    if (!displayName.trim()) {
      newErrors.display_name = "Display name is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (): Promise<void> => {
    if (!validate()) return;

    setIsSubmitting(true);
    setErrors({});

    try {
      if (isEditMode && metric) {
        await updateMetric(metric.id, {
          display_name: displayName,
          description: description || undefined,
          unit: unit || undefined,
          value_type: valueType,
        });
      } else {
        await createMetric({
          name,
          display_name: displayName,
          description: description || undefined,
          unit: unit || undefined,
          value_type: valueType,
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
      title={isEditMode ? "Edit Metric" : "Create Metric"}
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
            {isEditMode ? "Save Changes" : "Create Metric"}
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
            placeholder="e.g., monthly_revenue"
          />
        )}

        <Input
          label="Display Name"
          type="text"
          value={displayName}
          onInput={(e) => setDisplayName((e.target as HTMLInputElement).value)}
          error={errors.display_name}
          placeholder="e.g., Monthly Revenue"
        />

        <div class="w-full">
          <label htmlFor="metric-description" class="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            id="metric-description"
            value={description}
            onInput={(e) => setDescription((e.target as HTMLTextAreaElement).value)}
            placeholder="Optional description"
            rows={2}
            class="block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-950 placeholder:text-gray-500 transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        <Input
          label="Unit"
          type="text"
          value={unit}
          onInput={(e) => setUnit((e.target as HTMLInputElement).value)}
          placeholder="e.g., USD, %, count"
        />

        <div class="w-full">
          <label htmlFor="metric-value-type" class="block text-sm font-medium text-gray-700 mb-1">
            Value Type
          </label>
          <select
            id="metric-value-type"
            value={valueType}
            onChange={(e) => setValueType((e.target as HTMLSelectElement).value as MetricValueType)}
            class="block w-full rounded-lg border border-gray-300 bg-white px-3 h-9 text-sm text-gray-950 transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
          >
            {VALUE_TYPES.map((vt) => (
              <option key={vt.value} value={vt.value}>
                {vt.label}
              </option>
            ))}
          </select>
        </div>
      </form>
    </Modal>
  );
}
