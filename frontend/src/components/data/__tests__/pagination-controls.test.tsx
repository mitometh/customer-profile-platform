import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";

import { PaginationControls } from "../pagination-controls";

describe("PaginationControls", () => {
  it("shows count with total when available", () => {
    render(
      <PaginationControls
        hasNext={false}
        isLoading={false}
        total={100}
        currentCount={20}
        onLoadMore={vi.fn()}
      />,
    );
    expect(screen.getByText("Showing 20 of 100")).toBeTruthy();
  });

  it("shows count without total when null", () => {
    render(
      <PaginationControls
        hasNext={false}
        isLoading={false}
        total={null}
        currentCount={5}
        onLoadMore={vi.fn()}
      />,
    );
    expect(screen.getByText("Showing 5 results")).toBeTruthy();
  });

  it("shows Load More button when hasNext is true", () => {
    render(
      <PaginationControls
        hasNext={true}
        isLoading={false}
        total={100}
        currentCount={20}
        onLoadMore={vi.fn()}
      />,
    );
    expect(screen.getByText("Load More")).toBeTruthy();
  });

  it("hides Load More button when hasNext is false", () => {
    render(
      <PaginationControls
        hasNext={false}
        isLoading={false}
        total={20}
        currentCount={20}
        onLoadMore={vi.fn()}
      />,
    );
    expect(screen.queryByText("Load More")).toBeNull();
  });

  it("calls onLoadMore when button is clicked", () => {
    const onLoadMore = vi.fn();
    render(
      <PaginationControls
        hasNext={true}
        isLoading={false}
        total={100}
        currentCount={20}
        onLoadMore={onLoadMore}
      />,
    );
    fireEvent.click(screen.getByText("Load More"));
    expect(onLoadMore).toHaveBeenCalledTimes(1);
  });
});
