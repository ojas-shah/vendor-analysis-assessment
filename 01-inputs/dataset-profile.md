# Dataset Profile

Computed once at project setup. Re-run `python 03-scripts/profile_data.py` if the source file changes.

## Source

- File: `vendors-raw.xlsx`
- Original filename: `RWA - Vendor Spend Strategy (Ojas Shah).xlsx`
- Sheets: 5 (`Vendor Analysis Assessment`, `Top 3 Opportunities`, `Methodology`, `CEOCFO Recommendations`, `Config`)

## Key facts

| Metric | Value |
|---|---|
| Total vendors | 386 |
| Total annual spend (USD) | $7,887,360 |
| Largest single vendor | Salesforce Uk Ltd-Uk — **$3,117,225** (40% of total spend) |
| Vendors over $10K | 79 (these drive ~95% of total spend) |
| Median vendor spend | $1,308 (long tail of small line items) |

## Implications for the analysis

- **Salesforce alone is the story.** $3.1M in CRM spend is highly likely to be the single largest savings opportunity. Renegotiation alone at 20% yields $620K. Tier rationalization (Enterprise vs. Unlimited) on 1,000+ seats could add another $300K. This deserves Opportunity #1 status almost regardless of what else surfaces.
- **Focus QC effort on the top 79.** The long tail of <$10K vendors collectively matters, but per-vendor accuracy is less consequential. Top 79 vendors deserve the closest scrutiny.
- **Real estate is a major bucket.** Several property/space vendors visible in the top 20 (Tog Uk Properties, Innovent Spaces, Zagrebtower, Weking) — consolidation across regional offices is a likely Opportunity #2 candidate.
- **Facilities/admin long tail.** Insurance brokers, food services (M&S Simply Food, Bakemono Bakers, Coles), small office supplies — these are not strategic to scrutinize line-by-line but should be reviewed as a category.

## Schema

The vendor sheet has these columns (only the first 5 are populated in the source):

1. **Vendor Name** — populated
2. **Department** — blank, to be filled
3. **Last 12 months Cost (USD)** — populated
4. **1-line Description on what the Vendor does** — blank, to be filled
5. **Suggestions (Consolidate / Terminate / Optimize costs)** — blank, to be filled
