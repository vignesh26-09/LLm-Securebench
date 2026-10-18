# Run dashboard metric integration

The chosen model's `/results/:runId` page shows a shared 0–100% automated-rule bar chart, detector match counts, response-time line chart, eight source-native metric cards, case results, and a final production-selection warning. Rule scores are not attack-success rates.

The report API now projects numeric BSDA component distances, recovery ratios, SAEA step effects, DRAA evidence-feature counts, PRI observations/coverage, dataset components, held-out ML metrics when present, and descriptive statistics. Missing values remain missing. Records are restricted to the run, its evaluations, and its dataset version. Recovery's `rc` and `recovery` aliases are recognized.

The calculator calls the eight backend compute endpoints with explicitly supplied JSON. Its ephemeral results do not overwrite or attach to the selected model's evidence. The Vite proxy forwards `/metrics/catalog` and `/metrics/compute` without intercepting frontend metric routes.

Each individual metric page now exposes its own backend calculator even when no
saved record exists. A successful calculation can be saved explicitly as an
immutable `engineering_only` record; the record list and catalog refresh after
saving. Saving does not link the result to a selected model, establish input
provenance, or confer scientific validation. A second save of identical input
returns HTTP 409, preserving the existing record. BSDA, recovery and SAEA
continue to show empty scientific evidence until qualifying measurements are
actually supplied and validated; absent measurements are not rendered as zero.

Metric tiles and the evidence galaxy are original local UI implementations, not installed React Bits Pro source. Card 8 and Stats 16 installation was attempted with the shadcn CLI but refused because `REACTBITS_LICENSE_KEY` is not available. Existing `components.json` includes the Pro and starter registries with the required Authorization environment substitution. To install licensed blocks later, provide the license key in frontend `.env.local` (never commit it), then run the requested shadcn add command from `frontend`.

The galaxy indicates record presence, including blocked and uncalibrated records—not passed metrics or a safe model. The conclusion does not approve production use without independently validated outcomes and a use-case-specific decision rule.

## Verification

- 69 targeted metric-engine/API tests passed across all eight families.
- 30 report, projection, metric API, and local execution tests passed (overlaps the suite above).
- All 32 frontend tests passed; production build and ESLint passed.
- Browser verified a real statistics API calculation, record filtering, source values/units, and the final conclusion on a saved Gemma run.
- Responsive check at a 390-pixel viewport found no horizontal page overflow; desktop viewport was restored.
- Existing run `6de2c3b48e174600b0482c50d0fd5c75` has records for five families, not completed measurements for all eight. No missing research scores were filled in.
