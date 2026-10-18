import { screen } from "@testing-library/react";
import { StatusBadge } from "../src/components/common/StatusBadge";
import { renderWithProviders } from "./test-utils";

describe("StatusBadge", () => {
  it("keeps not-applicable distinct from a score", () => { renderWithProviders(<StatusBadge status="not_applicable" />); expect(screen.getByText("not applicable")).toBeInTheDocument(); });
  it("does not silently turn a missing scientific status into zero", () => { renderWithProviders(<StatusBadge status={null} />); expect(screen.getByText("not supplied")).toBeInTheDocument(); });
});
