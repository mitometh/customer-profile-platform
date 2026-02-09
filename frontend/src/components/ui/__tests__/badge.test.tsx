import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/preact";

import { Badge } from "../badge";

describe("Badge", () => {
  it("renders children text", () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText("Active")).toBeTruthy();
  });

  it("applies default variant classes", () => {
    const { container } = render(<Badge>Default</Badge>);
    const span = container.querySelector("span");
    expect(span?.className).toContain("bg-gray-100");
  });

  it("applies success variant classes", () => {
    const { container } = render(<Badge variant="success">OK</Badge>);
    const span = container.querySelector("span");
    expect(span?.className).toContain("bg-green-100");
    expect(span?.className).toContain("text-green-700");
  });

  it("applies danger variant classes", () => {
    const { container } = render(<Badge variant="danger">Error</Badge>);
    const span = container.querySelector("span");
    expect(span?.className).toContain("bg-red-100");
  });

  it("applies custom class name", () => {
    const { container } = render(<Badge class="mt-4">Custom</Badge>);
    const span = container.querySelector("span");
    expect(span?.className).toContain("mt-4");
  });
});
