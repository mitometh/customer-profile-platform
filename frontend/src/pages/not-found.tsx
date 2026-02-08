import { AppShell } from "@/components/layout/app-shell";

export function NotFoundPage(): preact.JSX.Element {
  return (
    <AppShell>
      <div class="flex flex-col items-center justify-center py-16">
        <svg
          class="h-12 w-12 text-gray-300"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="m20.25 7.5-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5m6 4.125 2.25 2.25m0 0 2.25 2.25M12 13.875l2.25-2.25M12 13.875l-2.25 2.25M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z"
          />
        </svg>
        <h2 class="mt-4 text-sm font-medium text-gray-900">Page not found</h2>
        <p class="mt-1 text-sm text-gray-500">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <a
          href="/"
          class="mt-4 inline-flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-700"
        >
          &larr; Go home
        </a>
      </div>
    </AppShell>
  );
}
