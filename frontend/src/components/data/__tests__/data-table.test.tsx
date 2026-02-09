import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";

import { DataTable } from "../data-table";
import type { Column } from "../data-table";

interface TestItem {
  id: string;
  name: string;
  email: string;
}

const columns: Column<TestItem>[] = [
  { key: "name", header: "Name" },
  { key: "email", header: "Email" },
];

const sampleData: TestItem[] = [
  { id: "1", name: "Alice", email: "alice@test.com" },
  { id: "2", name: "Bob", email: "bob@test.com" },
];

describe("DataTable", () => {
  it("renders column headers", () => {
    render(<DataTable columns={columns} data={[]} />);
    expect(screen.getByText("Name")).toBeTruthy();
    expect(screen.getByText("Email")).toBeTruthy();
  });

  it("renders data rows", () => {
    render(<DataTable columns={columns} data={sampleData} />);
    expect(screen.getByText("Alice")).toBeTruthy();
    expect(screen.getByText("bob@test.com")).toBeTruthy();
  });

  it("shows empty message when no data", () => {
    render(<DataTable columns={columns} data={[]} emptyMessage="Nothing here" />);
    expect(screen.getByText("Nothing here")).toBeTruthy();
  });

  it("shows default empty message", () => {
    render(<DataTable columns={columns} data={[]} />);
    expect(screen.getByText("No data found")).toBeTruthy();
  });

  it("shows skeleton rows when loading", () => {
    const { container } = render(<DataTable columns={columns} data={[]} isLoading={true} />);
    // Should show skeleton rows, not the empty message
    expect(screen.queryByText("No data found")).toBeNull();
    // 5 skeleton rows * 2 columns = 10 skeleton cells
    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBe(10);
  });

  it("calls onRowClick when a row is clicked", () => {
    const handleClick = vi.fn();
    render(<DataTable columns={columns} data={sampleData} onRowClick={handleClick} />);

    fireEvent.click(screen.getByText("Alice"));
    expect(handleClick).toHaveBeenCalledWith(sampleData[0]);
  });

  it("uses custom render function for columns", () => {
    const customColumns: Column<TestItem>[] = [
      {
        key: "name",
        header: "Name",
        render: (item) => <strong data-testid="custom">{item.name}</strong>,
      },
    ];

    render(<DataTable columns={customColumns} data={sampleData} />);
    expect(screen.getAllByTestId("custom")).toHaveLength(2);
  });
});
