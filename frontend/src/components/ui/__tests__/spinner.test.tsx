import { describe, it, expect } from "vitest";
import { render } from "@testing-library/preact";

import { Spinner } from "../spinner";

describe("Spinner", () => {
  it("renders an SVG element", () => {
    const { container } = render(<Spinner />);
    const svg = container.querySelector("svg");
    expect(svg).toBeTruthy();
  });

  it("has animate-spin class", () => {
    const { container } = render(<Spinner />);
    const svg = container.querySelector("svg");
    expect(svg?.className.baseVal).toContain("animate-spin");
  });

  it("is hidden from accessibility tree", () => {
    const { container } = render(<Spinner />);
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("aria-hidden")).toBe("true");
  });

  it("applies size classes for sm", () => {
    const { container } = render(<Spinner size="sm" />);
    const svg = container.querySelector("svg");
    expect(svg?.className.baseVal).toContain("h-3.5");
  });

  it("applies size classes for lg", () => {
    const { container } = render(<Spinner size="lg" />);
    const svg = container.querySelector("svg");
    expect(svg?.className.baseVal).toContain("h-6");
  });
});
