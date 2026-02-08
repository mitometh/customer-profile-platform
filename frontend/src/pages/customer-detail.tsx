import { useState, useEffect, useCallback } from "preact/hooks";

import { route } from "preact-router";

import type { CustomerDetail } from "@/types";

import { getCustomer, deleteCustomer } from "@/api/customers";
import { ApiError } from "@/api/client";
import { usePermission } from "@/hooks/use-permission";
import { useToast } from "@/components/ui/toast";

import { AuthGuard } from "@/components/layout/auth-guard";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";
import { ErrorState } from "@/components/data/error-state";
import { EmptyState } from "@/components/data/empty-state";
import { ConfirmationDialog } from "@/components/feedback/confirmation-dialog";

import { CustomerProfile } from "@/features/customers/customer-profile";
import { CustomerMetrics } from "@/features/customers/customer-metrics";
import { CustomerTimeline } from "@/features/customers/customer-timeline";
import { CustomerForm } from "@/features/customers/customer-form";

interface CustomerDetailPageProps {
  id?: string;
}

export function CustomerDetailPage({ id }: CustomerDetailPageProps): preact.JSX.Element {
  const [customer, setCustomer] = useState<CustomerDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const { hasPermission } = usePermission();
  const { showToast } = useToast();

  const fetchCustomer = useCallback(async (): Promise<void> => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await getCustomer(id);
      setCustomer(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err);
      }
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchCustomer();
  }, [fetchCustomer]);

  const handleEditSuccess = (): void => {
    setShowEditForm(false);
    fetchCustomer();
  };

  const handleDelete = async (): Promise<void> => {
    if (!id) return;
    setIsDeleting(true);
    try {
      await deleteCustomer(id);
      showToast({ type: "success", message: "Customer deleted successfully" });
      route("/customers");
    } catch (err) {
      if (err instanceof ApiError) {
        showToast({ type: "error", message: err.error.message });
      } else {
        showToast({ type: "error", message: "Failed to delete customer" });
      }
    } finally {
      setIsDeleting(false);
      setShowDeleteDialog(false);
    }
  };

  const canManage = hasPermission("customers.manage");

  return (
    <AuthGuard permission="customers.read">
      {isLoading && (
        <div>
          <div class="mb-6">
            <Skeleton class="h-4 w-32 mb-2" />
            <Skeleton class="h-8 w-64" />
          </div>
          <div class="grid grid-cols-12 gap-6">
            <div class="col-span-12 lg:col-span-4">
              <Card class="p-6">
                <div class="space-y-4">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i}>
                      <Skeleton class="h-3 w-20 mb-1" />
                      <Skeleton class="h-4 w-full" />
                    </div>
                  ))}
                </div>
              </Card>
            </div>
            <div class="col-span-12 lg:col-span-8">
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Card key={i} class="p-4">
                    <Skeleton class="h-3 w-24 mb-2" />
                    <Skeleton class="h-8 w-16" />
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {!isLoading && error && (
        <>
          {error.status === 404 ? (
            <EmptyState
              title="Customer not found"
              description="The customer you are looking for does not exist or has been deleted."
            />
          ) : (
            <ErrorState
              message="Failed to load customer data."
              onRetry={fetchCustomer}
            />
          )}
        </>
      )}

      {!isLoading && !error && customer && (
        <>
          <PageHeader
            title={customer.company_name}
            backTo="/customers"
            backLabel="Back to Customers"
            actions={
              canManage ? (
                <>
                  <Button
                    variant="secondary"
                    onClick={() => setShowEditForm(true)}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="danger"
                    onClick={() => setShowDeleteDialog(true)}
                  >
                    Delete
                  </Button>
                </>
              ) : undefined
            }
          />

          <div class="grid grid-cols-12 gap-6">
            <div class="col-span-12 lg:col-span-4">
              <CustomerProfile
                customer={customer}
                onEdit={canManage ? () => setShowEditForm(true) : undefined}
                onDelete={canManage ? () => setShowDeleteDialog(true) : undefined}
              />
            </div>
            <div class="col-span-12 lg:col-span-8">
              <CustomerMetrics
                metrics={customer.metrics}
                customerId={customer.id}
              />
            </div>
          </div>

          <div class="mt-8">
            <h2 class="text-lg font-semibold text-gray-950 mb-4">Activity Timeline</h2>
            <CustomerTimeline customerId={customer.id} />
          </div>

          {showEditForm && (
            <CustomerForm
              isOpen={showEditForm}
              onClose={() => setShowEditForm(false)}
              onSuccess={handleEditSuccess}
              customer={customer}
            />
          )}

          <ConfirmationDialog
            isOpen={showDeleteDialog}
            onClose={() => setShowDeleteDialog(false)}
            onConfirm={handleDelete}
            title="Delete Customer"
            message={`Are you sure you want to delete ${customer.company_name}? This action cannot be undone.`}
            confirmLabel="Delete"
            variant="danger"
            isLoading={isDeleting}
          />
        </>
      )}
    </AuthGuard>
  );
}
