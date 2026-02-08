import { useState } from "preact/hooks";

import type { CustomerDetail } from "@/types";

import { createCustomer, updateCustomer } from "@/api/customers";
import { ApiError } from "@/api/client";

import { useToast } from "@/components/ui/toast";

import { Modal } from "@/components/ui/modal";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface CustomerFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  customer?: CustomerDetail;
}

interface FormState {
  company_name: string;
  contact_name: string;
  email: string;
  contract_value: string;
  currency_code: string;
  signup_date: string;
}

interface FormErrors {
  company_name?: string;
  contact_name?: string;
  email?: string;
  contract_value?: string;
  currency_code?: string;
  signup_date?: string;
  general?: string;
}

function getInitialState(customer?: CustomerDetail): FormState {
  return {
    company_name: customer?.company_name ?? "",
    contact_name: customer?.contact_name ?? "",
    email: customer?.email ?? "",
    contract_value: customer ? String(customer.contract_value) : "",
    currency_code: customer?.currency_code ?? "USD",
    signup_date: customer?.signup_date ?? "",
  };
}

function validate(state: FormState, isEdit: boolean): FormErrors {
  const errors: FormErrors = {};

  if (!isEdit) {
    if (!state.company_name.trim()) errors.company_name = "Company name is required";
    if (!state.contact_name.trim()) errors.contact_name = "Contact name is required";
    if (!state.email.trim()) errors.email = "Email is required";
    if (!state.contract_value.trim()) {
      errors.contract_value = "Contract value is required";
    } else if (isNaN(Number(state.contract_value)) || Number(state.contract_value) < 0) {
      errors.contract_value = "Contract value must be a non-negative number";
    }
    if (!state.currency_code.trim()) errors.currency_code = "Currency code is required";
    if (!state.signup_date.trim()) errors.signup_date = "Signup date is required";
  } else {
    if (state.contract_value.trim() && (isNaN(Number(state.contract_value)) || Number(state.contract_value) < 0)) {
      errors.contract_value = "Contract value must be a non-negative number";
    }
  }

  return errors;
}

export function CustomerForm({
  isOpen,
  onClose,
  onSuccess,
  customer,
}: CustomerFormProps): preact.JSX.Element {
  const isEdit = !!customer;
  const [form, setForm] = useState<FormState>(() => getInitialState(customer));
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { showToast } = useToast();

  const handleChange = (field: keyof FormState) => (e: Event): void => {
    const value = (e.target as HTMLInputElement).value;
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const submitForm = async (): Promise<void> => {
    const validationErrors = validate(form, isEdit);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      if (isEdit && customer) {
        const updateData: Record<string, unknown> = {};
        if (form.company_name.trim()) updateData.company_name = form.company_name.trim();
        if (form.contact_name.trim()) updateData.contact_name = form.contact_name.trim();
        if (form.email.trim()) updateData.email = form.email.trim();
        if (form.contract_value.trim()) updateData.contract_value = Number(form.contract_value);
        if (form.currency_code.trim()) updateData.currency_code = form.currency_code.trim();

        await updateCustomer(customer.id, updateData);
        showToast({ type: "success", message: "Customer updated successfully" });
      } else {
        await createCustomer({
          company_name: form.company_name.trim(),
          contact_name: form.contact_name.trim(),
          email: form.email.trim(),
          contract_value: Number(form.contract_value),
          currency_code: form.currency_code.trim(),
          signup_date: form.signup_date,
        });
        showToast({ type: "success", message: "Customer created successfully" });
      }

      onSuccess();
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 400 && err.error.details) {
          const fieldErrors: FormErrors = {};
          for (const [key, value] of Object.entries(err.error.details)) {
            if (key in form) {
              fieldErrors[key as keyof FormErrors] = String(value);
            }
          }
          setErrors(fieldErrors);
        } else {
          setErrors({ general: err.error.message });
        }
      } else {
        setErrors({ general: "An unexpected error occurred. Please try again." });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFormSubmit = (e: Event): void => {
    e.preventDefault();
    submitForm();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? "Edit Customer" : "Create Customer"}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={submitForm}
            loading={isSubmitting}
            disabled={isSubmitting}
          >
            {isEdit ? "Save Changes" : "Create Customer"}
          </Button>
        </>
      }
    >
      <form onSubmit={handleFormSubmit} class="space-y-4">
        {errors.general && (
          <div class="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
            {errors.general}
          </div>
        )}
        <Input
          label="Company Name"
          value={form.company_name}
          onInput={handleChange("company_name")}
          error={errors.company_name}
          placeholder="Acme Corp"
        />
        <Input
          label="Contact Name"
          value={form.contact_name}
          onInput={handleChange("contact_name")}
          error={errors.contact_name}
          placeholder="John Smith"
        />
        <Input
          label="Email"
          type="email"
          value={form.email}
          onInput={handleChange("email")}
          error={errors.email}
          placeholder="john@acme.com"
        />
        <div class="grid grid-cols-2 gap-4">
          <Input
            label="Contract Value"
            type="number"
            value={form.contract_value}
            onInput={handleChange("contract_value")}
            error={errors.contract_value}
            placeholder="150000"
          />
          <Input
            label="Currency Code"
            value={form.currency_code}
            onInput={handleChange("currency_code")}
            error={errors.currency_code}
            placeholder="USD"
          />
        </div>
        {!isEdit && (
          <Input
            label="Signup Date"
            type="date"
            value={form.signup_date}
            onInput={handleChange("signup_date")}
            error={errors.signup_date}
          />
        )}
      </form>
    </Modal>
  );
}
