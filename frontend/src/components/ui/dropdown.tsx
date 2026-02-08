import { type ComponentChildren } from "preact";
import { useEffect, useRef, useState } from "preact/hooks";

import { cn } from "@/lib/cn";

interface DropdownItem {
  label: string;
  onClick: () => void;
  icon?: ComponentChildren;
  danger?: boolean;
}

interface DropdownProps {
  trigger: ComponentChildren;
  items: DropdownItem[];
  class?: string;
}

export type { DropdownItem };

export function Dropdown({
  trigger,
  items,
  class: className,
}: DropdownProps): preact.JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent): void => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent): void => {
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const handleToggle = (): void => {
    setIsOpen((prev) => !prev);
  };

  const handleItemClick = (item: DropdownItem): void => {
    item.onClick();
    setIsOpen(false);
  };

  return (
    <div class={cn("relative inline-block", className)} ref={containerRef}>
      <div onClick={handleToggle} class="cursor-pointer">
        {trigger}
      </div>
      {isOpen && (
        <div class="absolute right-0 mt-1 z-50 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-[160px]">
          {items.map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => handleItemClick(item)}
              class={cn(
                "w-full px-3 py-2 text-sm text-left flex items-center gap-2 cursor-pointer",
                item.danger
                  ? "text-red-600 hover:bg-red-50"
                  : "text-gray-700 hover:bg-gray-100",
              )}
            >
              {item.icon && <span class="flex-shrink-0">{item.icon}</span>}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
