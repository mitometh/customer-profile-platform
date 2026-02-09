import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";

import { ErrorState } from "../error-state";

describe("ErrorState", () => {
  it("renders default title and message", () => {
    render(<ErrorState />);
    expect(screen.getByText("Something went wrong")).toBeTruthy();
    expect(screen.getByText("An error occurred. Please try again.")).toBeTruthy();
  });

  it("renders custom title and message", () => {
    render(<ErrorState title="Not Found" message="The resource was not found." />);
    expect(screen.getByText("Not Found")).toBeTruthy();
    expect(screen.getByText("The resource was not found.")).toBeTruthy();
  });

  it("shows Retry button when onRetry is provided", () => {
    render(<ErrorState onRetry={vi.fn()} />);
    expect(screen.getByText("Retry")).toBeTruthy();
  });

  it("hides Retry button when onRetry is not provided", () => {
    render(<ErrorState />);
    expect(screen.queryByText("Retry")).toBeNull();
  });

  it("calls onRetry when Retry button is clicked", () => {
    const onRetry = vi.fn();
    render(<ErrorState onRetry={onRetry} />);
    fireEvent.click(screen.getByText("Retry"));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
