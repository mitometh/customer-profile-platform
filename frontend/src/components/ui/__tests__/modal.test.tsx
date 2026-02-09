import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";

import { Modal } from "../modal";

describe("Modal", () => {
  it("renders nothing when isOpen is false", () => {
    const { container } = render(
      <Modal isOpen={false} onClose={vi.fn()} title="Test">
        Content
      </Modal>,
    );
    expect(container.querySelector("[role='dialog']")).toBeNull();
  });

  it("renders dialog when isOpen is true", () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="Test Modal">
        Modal content
      </Modal>,
    );
    expect(screen.getByRole("dialog")).toBeTruthy();
    expect(screen.getByText("Test Modal")).toBeTruthy();
    expect(screen.getByText("Modal content")).toBeTruthy();
  });

  it("renders footer when provided", () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="Test" footer={<button>Save</button>}>
        Content
      </Modal>,
    );
    expect(screen.getByText("Save")).toBeTruthy();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={onClose} title="Test">
        Content
      </Modal>,
    );
    fireEvent.click(screen.getByLabelText("Close"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose on Escape key", () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={onClose} title="Test">
        Content
      </Modal>,
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("has correct aria attributes", () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="Accessible Modal">
        Content
      </Modal>,
    );
    const dialog = screen.getByRole("dialog");
    expect(dialog.getAttribute("aria-modal")).toBe("true");
    expect(dialog.getAttribute("aria-labelledby")).toBeTruthy();
  });

  it("adds overflow-hidden to body when open", () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="Test">
        Content
      </Modal>,
    );
    expect(document.body.classList.contains("overflow-hidden")).toBe(true);
  });
});
