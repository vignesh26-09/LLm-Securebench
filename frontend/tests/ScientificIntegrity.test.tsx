import { screen } from "@testing-library/react";
import { BSDAPage, DRAAPage, MatchedHallucinationPage, PRIPage, SAEAPage } from "../src/pages/MetricPages";
import { renderWithProviders } from "./test-utils";

describe("scientific integrity safeguards", () => {
  beforeEach(() => { vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({ items: [], limit: 25, offset: 0 }), { status: 200, headers: { "Content-Type": "application/json" } })))); });
  afterEach(() => vi.unstubAllGlobals());
  it("renders BSDA components independently and no composite score", async () => { renderWithProviders(<BSDAPage />); expect(screen.getByText("Semantic distance")).toBeInTheDocument(); expect(screen.getByText("Safety distance")).toBeInTheDocument(); expect(screen.queryByText(/^BSDA Score:/)).not.toBeInTheDocument(); });
  it("keeps DRAA to its allowed Mode A/B evidence scope", () => { renderWithProviders(<DRAAPage />); expect(screen.getByText("Mode C is not available.")).toBeInTheDocument(); expect(screen.queryByText(/^Case risk:/)).not.toBeInTheDocument(); });
  it("does not assign PRI qualitative robustness grades", () => { renderWithProviders(<PRIPage />); expect(screen.queryByText(/Good|Moderate|Excellent/)).not.toBeInTheDocument(); });
  it("uses the corrected CV_obs interpretation", () => { renderWithProviders(<SAEAPage />); expect(screen.getByText(/CV_obs means observed cumulative vulnerability/)).toBeInTheDocument(); expect(screen.queryByText(/coefficient of variance/i)).not.toBeInTheDocument(); });
  it("explains the matched factual metric without claiming prediction or verified labels", () => { renderWithProviders(<MatchedHallucinationPage />); expect(screen.getByText(/not a prediction of the next response/i)).toBeInTheDocument(); expect(screen.getByText(/automated judge scores cannot supply factual ground truth/i)).toBeInTheDocument(); });
});
