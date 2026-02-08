import { useState } from "preact/hooks";

import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";

interface SourceTokenModalProps {
  isOpen: boolean;
  onClose: () => void;
  token: string;
  sourceName: string;
}

export function SourceTokenModal({
  isOpen,
  onClose,
  token,
  sourceName,
}: SourceTokenModalProps): preact.JSX.Element {
  const [isCopied, setIsCopied] = useState(false);

  const handleCopy = async (): Promise<void> => {
    try {
      await navigator.clipboard.writeText(token);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch {
      // Fallback: select the text for manual copy
    }
  };

  const handleDismiss = (): void => {
    setIsCopied(false);
    onClose();
  };

  // Pass a no-op to onClose so overlay click and Escape do not dismiss
  const noop = (): void => {
    // Intentionally empty: user must click "I've copied the token"
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={noop}
      title="Source API Token"
      size="md"
      footer={
        <Button onClick={handleDismiss}>
          I've copied the token
        </Button>
      }
    >
      <div class="space-y-4">
        <div class="flex items-start gap-3 p-3 rounded-lg bg-amber-100 text-amber-700">
          <svg
            class="h-5 w-5 flex-shrink-0 mt-0.5"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
            />
          </svg>
          <p class="text-sm font-medium">
            This token will not be shown again. Copy it now.
          </p>
        </div>

        <div>
          <p class="text-sm font-medium text-gray-700 mb-1">Source</p>
          <p class="text-sm text-gray-900">{sourceName}</p>
        </div>

        <div>
          <p class="text-sm font-medium text-gray-700 mb-1">API Token</p>
          <div class="font-mono text-sm bg-gray-100 p-3 rounded-lg break-all border border-gray-200 text-gray-900">
            {token}
          </div>
        </div>

        <Button
          variant="secondary"
          onClick={handleCopy}
          class="w-full"
        >
          {isCopied ? "Copied!" : "Copy to clipboard"}
        </Button>
      </div>
    </Modal>
  );
}
