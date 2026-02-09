import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/preact";

import { EmptyState } from "../empty-state";

describe("EmptyState", () => {
  it("renders title", () => {
    render(<EmptyState title="No results" />);
    expect(screen.getByText("No results")).toBeTruthy();
  });

  it("renders description when provided", () => {
    render(
      <EmptyState title="No data" description="Try adjusting your filters" />,
    );
    expect(screen.getByText("Try adjusting your filters")).toBeTruthy();
  });

  it("does not render description when not provided", () => {
    const { container } = render(<EmptyState title="No data" />);
    const paragraphs = container.querySelectorAll("p");
    expect(paragraphs.length).toBe(0);
  });

  it("renders action slot", () => {
    render(
      <EmptyState
        title="Empty"
        action={<button>Add new</button>}
      />,
    );
    expect(screen.getByText("Add new")).toBeTruthy();
  });

  it("renders icon when provided", () => {
    render(
      <EmptyState
        title="Empty"
        icon={<span data-testid="icon">icon</span>}
      />,
    );
    expect(screen.getByTestId("icon")).toBeTruthy();
  });
});
