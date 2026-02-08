import { type ComponentChildren } from "preact";

import { cn } from "@/lib/cn";

interface KeyValueItem {
  label: string;
  value: ComponentChildren;
}

interface KeyValueProps {
  items: KeyValueItem[];
  class?: string;
}

export function KeyValue({ items, class: className }: KeyValueProps): preact.JSX.Element {
  return (
    <dl class={cn("divide-y divide-gray-100", className)}>
      {items.map((item) => (
        <div key={item.label} class="py-3 last:border-0">
          <dt class="text-sm text-gray-500">{item.label}</dt>
          <dd class="text-sm font-medium text-gray-900 mt-0.5">{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}
