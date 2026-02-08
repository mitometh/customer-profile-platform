import { cn } from "@/lib/cn";

interface InputProps extends Omit<preact.JSX.InputHTMLAttributes<HTMLInputElement>, "class" | "size"> {
  label?: string;
  error?: string;
  disabled?: boolean;
  class?: string;
}

export function Input({
  label,
  error,
  class: className,
  id,
  disabled,
  ...rest
}: InputProps): preact.JSX.Element {
  const inputId = id ?? (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <div class="w-full">
      {label && (
        <label
          htmlFor={inputId}
          class="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        disabled={disabled}
        class={cn(
          "block w-full rounded-lg border px-3 h-9 text-sm text-gray-950 placeholder:text-gray-500 transition-colors",
          error
            ? "border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500"
            : "border-gray-300 bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500",
          disabled && "border-gray-200 bg-gray-50 cursor-not-allowed",
          className,
        )}
        {...rest}
      />
      {error && (
        <p class="mt-1 text-xs text-red-600">{error}</p>
      )}
    </div>
  );
}
