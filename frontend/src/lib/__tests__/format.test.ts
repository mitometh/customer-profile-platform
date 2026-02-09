import { describe, it, expect } from "vitest";

import {
  formatCurrency,
  formatNumber,
  formatPercentage,
  formatMetricValue,
} from "../format";

describe("formatCurrency", () => {
  it("formats USD by default", () => {
    expect(formatCurrency(1000)).toBe("$1,000");
  });

  it("formats large numbers with comma separators", () => {
    expect(formatCurrency(1234567)).toBe("$1,234,567");
  });

  it("formats zero", () => {
    expect(formatCurrency(0)).toBe("$0");
  });

  it("accepts different currency codes", () => {
    const result = formatCurrency(500, "EUR");
    expect(result).toContain("500");
  });
});

describe("formatNumber", () => {
  it("formats integers with comma separators", () => {
    expect(formatNumber(1000)).toBe("1,000");
    expect(formatNumber(1234567)).toBe("1,234,567");
  });

  it("handles zero", () => {
    expect(formatNumber(0)).toBe("0");
  });

  it("handles decimals", () => {
    expect(formatNumber(1234.56)).toBe("1,234.56");
  });
});

describe("formatPercentage", () => {
  it("formats with one decimal place and percent sign", () => {
    expect(formatPercentage(85.5)).toBe("85.5%");
  });

  it("pads to one decimal place", () => {
    expect(formatPercentage(100)).toBe("100.0%");
  });

  it("handles zero", () => {
    expect(formatPercentage(0)).toBe("0.0%");
  });
});

describe("formatMetricValue", () => {
  it("formats percentage type", () => {
    expect(formatMetricValue(85.5, "percentage", "%")).toBe("85.5%");
  });

  it("formats decimal type to 2 places", () => {
    expect(formatMetricValue(3.14159, "decimal", "")).toBe("3.14");
  });

  it("formats integer type with rounding", () => {
    expect(formatMetricValue(1234.7, "integer", "")).toBe("1,235");
  });

  it("falls back to string for unknown type", () => {
    expect(formatMetricValue(42, "unknown", "")).toBe("42");
  });
});
