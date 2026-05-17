# Department Taxonomy

Source: derived directly from the `Config` tab of the assessment spreadsheet. These are the **only** valid department labels. The first-pass and QC prompts inject this list verbatim so the model cannot invent new categories.

## Canonical departments

- Engineering
- Facilities
- Finance
- G&A
- Legal
- M&A
- Marketing
- Product
- Professional Services
- SaaS
- Sales
- Support

## Notes for the analyst

- **SaaS** is its own department here, alongside Engineering. Most assessment frameworks fold SaaS into the consuming team's budget — this company keeps it separate. Respect that.
- **Professional Services** is for outside firms (consultants, agencies, law firms acting on a per-project basis). Recurring/retainer legal counsel goes under **Legal**.
- **G&A** is the catch-all for general admin not covered elsewhere (HR tools, office supplies, insurance brokers that serve the whole company).
- **M&A** is for vendors specifically supporting acquisition activity (bankers, deal counsel, integration consultants).
- If a vendor genuinely fits none of the above, the prompts will return `Unclassified` and flag for human review rather than guess.
