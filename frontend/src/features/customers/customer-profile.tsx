import type { CustomerDetail } from "@/types";

import { formatCurrency, formatDate } from "@/lib/format";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardBody } from "@/components/ui/card";
import { KeyValue } from "@/components/data/key-value";

interface CustomerProfileProps {
  customer: CustomerDetail;
  onEdit?: () => void;
  onDelete?: () => void;
}

export function CustomerProfile({
  customer,
  onEdit,
  onDelete,
}: CustomerProfileProps): preact.JSX.Element {
  const items = [
    { label: "Contact", value: customer.contact_name },
    {
      label: "Email",
      value: (
        <a
          href={`mailto:${customer.email}`}
          class="text-indigo-600 hover:text-indigo-700"
        >
          {customer.email}
        </a>
      ),
    },
    ...(customer.phone ? [{ label: "Phone", value: customer.phone }] : []),
    ...(customer.industry ? [{ label: "Industry", value: customer.industry }] : []),
    {
      label: "Contract Value",
      value: formatCurrency(customer.contract_value, customer.currency_code),
    },
    { label: "Signup Date", value: formatDate(customer.signup_date) },
    {
      label: "Source",
      value: customer.source_name ? (
        <Badge variant="primary">{customer.source_name}</Badge>
      ) : (
        <span class="text-gray-400">&mdash;</span>
      ),
    },
    { label: "Created", value: formatDate(customer.created_at) },
  ];

  return (
    <Card>
      <CardHeader title="Profile" />
      <CardBody>
        <KeyValue items={items} />
        {(onEdit || onDelete) && (
          <div class="flex items-center gap-3 mt-4 pt-4 border-t border-gray-100">
            {onEdit && (
              <Button variant="secondary" size="sm" onClick={onEdit}>
                Edit
              </Button>
            )}
            {onDelete && (
              <Button variant="ghost" size="sm" onClick={onDelete} class="text-red-600 hover:bg-red-50 hover:text-red-700">
                Delete
              </Button>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
