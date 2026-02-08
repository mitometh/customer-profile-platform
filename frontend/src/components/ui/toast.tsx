import { type ComponentChildren, createContext } from "preact";
import { useCallback, useContext, useRef, useState } from "preact/hooks";

import { cn } from "@/lib/cn";

type ToastType = "success" | "error" | "warning" | "info";

interface ToastOptions {
  type: ToastType;
  message: string;
}

interface ToastEntry {
  id: number;
  type: ToastType;
  message: string;
}

interface ToastContextValue {
  showToast: (options: ToastOptions) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const MAX_VISIBLE = 3;

const autoDismissMs: Record<ToastType, number | null> = {
  success: 5000,
  info: 5000,
  warning: 8000,
  error: null,
};

const borderColors: Record<ToastType, string> = {
  success: "border-l-green-500",
  error: "border-l-red-500",
  warning: "border-l-amber-500",
  info: "border-l-blue-500",
};

function SuccessIcon(): preact.JSX.Element {
  return (
    <svg class="h-5 w-5 text-green-500 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function ErrorIcon(): preact.JSX.Element {
  return (
    <svg class="h-5 w-5 text-red-500 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function WarningIcon(): preact.JSX.Element {
  return (
    <svg class="h-5 w-5 text-amber-500 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
    </svg>
  );
}

function InfoIcon(): preact.JSX.Element {
  return (
    <svg class="h-5 w-5 text-blue-500 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
    </svg>
  );
}

const icons: Record<ToastType, () => preact.JSX.Element> = {
  success: SuccessIcon,
  error: ErrorIcon,
  warning: WarningIcon,
  info: InfoIcon,
};

export function ToastProvider({ children }: { children: ComponentChildren }): preact.JSX.Element {
  const [toasts, setToasts] = useState<ToastEntry[]>([]);
  const nextId = useRef(0);
  const timersRef = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());

  const removeToast = useCallback((id: number): void => {
    const timer = timersRef.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timersRef.current.delete(id);
    }
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback((options: ToastOptions): void => {
    const id = nextId.current++;
    const entry: ToastEntry = { id, ...options };

    setToasts((prev) => {
      const next = [...prev, entry];
      if (next.length > MAX_VISIBLE) {
        const removed = next[0];
        if (removed) {
          const timer = timersRef.current.get(removed.id);
          if (timer) {
            clearTimeout(timer);
            timersRef.current.delete(removed.id);
          }
        }
        return next.slice(1);
      }
      return next;
    });

    const duration = autoDismissMs[options.type];
    if (duration !== null) {
      const timer = setTimeout(() => {
        removeToast(id);
      }, duration);
      timersRef.current.set(id, timer);
    }
  }, [removeToast]);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div
        class="fixed top-4 right-4 z-[60] flex flex-col gap-3 w-full max-w-sm sm:max-w-96 px-4 sm:px-0"
        aria-live="polite"
      >
        {toasts.map((toast) => {
          const Icon = icons[toast.type];
          return (
            <div
              key={toast.id}
              class={cn(
                "bg-white rounded-lg shadow-lg border border-gray-200 border-l-4 p-4 flex items-start gap-3",
                borderColors[toast.type],
              )}
            >
              <Icon />
              <p class="flex-1 text-sm text-gray-900">{toast.message}</p>
              <button
                type="button"
                onClick={() => removeToast(toast.id)}
                class="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
                aria-label="Dismiss"
              >
                <svg class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
