import { describe, it, expect, vi, afterEach } from "vitest";

import { listCustomers, getCustomer, createCustomer, updateCustomer, deleteCustomer } from "../customers";

vi.mock("../client", () => ({
  request: vi.fn(),
  ApiError: class extends Error {
    constructor(
      public status: number,
      public error: { code: string; message: string },
    ) {
      super(error.message);
    }
  },
}));

import { request } from "../client";

const mockRequest = vi.mocked(request);

describe("listCustomers", () => {
  afterEach(() => vi.clearAllMocks());

  it("calls with default limit and no search", async () => {
    mockRequest.mockResolvedValue({ data: [], pagination: {} });
    await listCustomers();

    const url = mockRequest.mock.calls[0]?.[0] as string;
    expect(url).toContain("/api/customers?");
    expect(url).toContain("limit=20");
    expect(url).not.toContain("search=");
    expect(url).not.toContain("cursor=");
  });

  it("includes search param when provided", async () => {
    mockRequest.mockResolvedValue({ data: [], pagination: {} });
    await listCustomers({ search: "acme" });

    const url = mockRequest.mock.calls[0]?.[0] as string;
    expect(url).toContain("search=acme");
  });

  it("includes cursor for pagination", async () => {
    mockRequest.mockResolvedValue({ data: [], pagination: {} });
    await listCustomers({ cursor: "abc123", limit: 10 });

    const url = mockRequest.mock.calls[0]?.[0] as string;
    expect(url).toContain("cursor=abc123");
    expect(url).toContain("limit=10");
  });
});

describe("getCustomer", () => {
  afterEach(() => vi.clearAllMocks());

  it("calls GET /api/customers/:id", async () => {
    mockRequest.mockResolvedValue({ id: "c1" });
    await getCustomer("c1");
    expect(mockRequest).toHaveBeenCalledWith("/api/customers/c1");
  });
});

describe("createCustomer", () => {
  afterEach(() => vi.clearAllMocks());

  it("calls POST /api/customers with body", async () => {
    const data = {
      company_name: "Acme",
      contact_name: "John",
      email: "john@acme.com",
      contract_value: 50000,
      currency_code: "USD",
      signup_date: "2024-01-15",
    };
    mockRequest.mockResolvedValue({ id: "new", ...data });
    await createCustomer(data);

    expect(mockRequest).toHaveBeenCalledWith("/api/customers", {
      method: "POST",
      body: JSON.stringify(data),
    });
  });
});

describe("updateCustomer", () => {
  afterEach(() => vi.clearAllMocks());

  it("calls PATCH /api/customers/:id with body", async () => {
    const data = { company_name: "Updated Corp" };
    mockRequest.mockResolvedValue({ id: "c1", ...data });
    await updateCustomer("c1", data);

    expect(mockRequest).toHaveBeenCalledWith("/api/customers/c1", {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  });
});

describe("deleteCustomer", () => {
  afterEach(() => vi.clearAllMocks());

  it("calls DELETE /api/customers/:id", async () => {
    mockRequest.mockResolvedValue(undefined);
    await deleteCustomer("c1");

    expect(mockRequest).toHaveBeenCalledWith("/api/customers/c1", {
      method: "DELETE",
    });
  });
});
