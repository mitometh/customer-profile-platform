import { describe, it, expect } from "vitest";

import { validate, getInitialState } from "../customer-form";
import type { CustomerDetail } from "@/types";

describe("getInitialState", () => {
  it("returns empty state when no customer provided", () => {
    const state = getInitialState();
    expect(state.company_name).toBe("");
    expect(state.contact_name).toBe("");
    expect(state.email).toBe("");
    expect(state.contract_value).toBe("");
    expect(state.currency_code).toBe("USD");
    expect(state.signup_date).toBe("");
  });

  it("populates state from existing customer", () => {
    const customer = {
      id: "c1",
      company_name: "Acme",
      contact_name: "John",
      email: "john@acme.com",
      contract_value: 50000,
      currency_code: "EUR",
      signup_date: "2024-01-15",
    } as CustomerDetail;

    const state = getInitialState(customer);
    expect(state.company_name).toBe("Acme");
    expect(state.contact_name).toBe("John");
    expect(state.email).toBe("john@acme.com");
    expect(state.contract_value).toBe("50000");
    expect(state.currency_code).toBe("EUR");
    expect(state.signup_date).toBe("2024-01-15");
  });
});

describe("validate (create mode)", () => {
  const blank = {
    company_name: "",
    contact_name: "",
    email: "",
    contract_value: "",
    currency_code: "",
    signup_date: "",
  };

  it("returns errors for all blank fields", () => {
    const errors = validate(blank, false);
    expect(errors.company_name).toBeDefined();
    expect(errors.contact_name).toBeDefined();
    expect(errors.email).toBeDefined();
    expect(errors.contract_value).toBeDefined();
    expect(errors.currency_code).toBeDefined();
    expect(errors.signup_date).toBeDefined();
  });

  it("returns no errors for valid input", () => {
    const valid = {
      company_name: "Acme",
      contact_name: "John",
      email: "john@acme.com",
      contract_value: "50000",
      currency_code: "USD",
      signup_date: "2024-01-15",
    };
    const errors = validate(valid, false);
    expect(Object.keys(errors)).toHaveLength(0);
  });

  it("rejects negative contract value", () => {
    const state = {
      company_name: "Acme",
      contact_name: "John",
      email: "john@acme.com",
      contract_value: "-100",
      currency_code: "USD",
      signup_date: "2024-01-15",
    };
    const errors = validate(state, false);
    expect(errors.contract_value).toContain("non-negative");
  });

  it("rejects non-numeric contract value", () => {
    const state = {
      company_name: "Acme",
      contact_name: "John",
      email: "john@acme.com",
      contract_value: "abc",
      currency_code: "USD",
      signup_date: "2024-01-15",
    };
    const errors = validate(state, false);
    expect(errors.contract_value).toBeDefined();
  });

  it("accepts zero contract value", () => {
    const state = {
      company_name: "Acme",
      contact_name: "John",
      email: "john@acme.com",
      contract_value: "0",
      currency_code: "USD",
      signup_date: "2024-01-15",
    };
    const errors = validate(state, false);
    expect(errors.contract_value).toBeUndefined();
  });
});

describe("validate (edit mode)", () => {
  it("does not require fields in edit mode", () => {
    const blank = {
      company_name: "",
      contact_name: "",
      email: "",
      contract_value: "",
      currency_code: "",
      signup_date: "",
    };
    const errors = validate(blank, true);
    expect(Object.keys(errors)).toHaveLength(0);
  });

  it("still validates contract value format if provided", () => {
    const state = {
      company_name: "",
      contact_name: "",
      email: "",
      contract_value: "not-a-number",
      currency_code: "",
      signup_date: "",
    };
    const errors = validate(state, true);
    expect(errors.contract_value).toBeDefined();
  });

  it("allows valid contract value in edit mode", () => {
    const state = {
      company_name: "",
      contact_name: "",
      email: "",
      contract_value: "25000",
      currency_code: "",
      signup_date: "",
    };
    const errors = validate(state, true);
    expect(errors.contract_value).toBeUndefined();
  });
});
