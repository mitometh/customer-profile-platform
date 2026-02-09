import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/preact";

import { KeyValue } from "../key-value";

describe("KeyValue", () => {
  it("renders label and value pairs", () => {
    render(
      <KeyValue
        items={[
          { label: "Name", value: "Alice" },
          { label: "Email", value: "alice@test.com" },
        ]}
      />,
    );
    expect(screen.getByText("Name")).toBeTruthy();
    expect(screen.getByText("Alice")).toBeTruthy();
    expect(screen.getByText("Email")).toBeTruthy();
    expect(screen.getByText("alice@test.com")).toBeTruthy();
  });

  it("renders JSX values", () => {
    render(
      <KeyValue
        items={[
          { label: "Status", value: <span data-testid="status">Active</span> },
        ]}
      />,
    );
    expect(screen.getByTestId("status")).toBeTruthy();
    expect(screen.getByText("Active")).toBeTruthy();
  });

  it("renders empty when no items", () => {
    const { container } = render(<KeyValue items={[]} />);
    const dl = container.querySelector("dl");
    expect(dl).toBeTruthy();
    expect(dl?.children).toHaveLength(0);
  });
});
