import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";

interface ConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  variant?: "danger" | "primary";
  isLoading?: boolean;
}

export function ConfirmationDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = "Confirm",
  variant = "primary",
  isLoading = false,
}: ConfirmationDialogProps): preact.JSX.Element {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            variant={variant}
            onClick={onConfirm}
            loading={isLoading}
            disabled={isLoading}
          >
            {confirmLabel}
          </Button>
        </>
      }
    >
      <p class="text-sm text-gray-600">{message}</p>
    </Modal>
  );
}
