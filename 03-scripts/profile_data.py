"""Profile the source data and write a summary to 01-inputs/dataset-profile.md.

Run this once after dropping vendors-raw.xlsx into 01-inputs/.
"""

from __future__ import annotations

from _common import INPUTS_DIR, load_source_vendors


def main() -> None:
    vendors = load_source_vendors()
    spends = sorted([v["spend"] for v in vendors], reverse=True)
    total = sum(spends)
    top1 = vendors[0] if vendors else {"name": "n/a", "spend": 0}

    print(f"Vendors: {len(vendors)}")
    print(f"Total spend: ${total:,.2f}")
    print(f"Largest vendor: {top1['name']} — ${top1['spend']:,.2f}")
    print(f"Vendors over $10K: {sum(1 for s in spends if s > 10000)}")
    print(f"Vendors over $50K: {sum(1 for s in spends if s > 50000)}")
    print(f"Median: ${spends[len(spends) // 2]:,.2f}")
    print()
    print("Top 20 by spend:")
    for v in sorted(vendors, key=lambda x: -x["spend"])[:20]:
        print(f"  ${v['spend']:>14,.2f}  {v['name']}")


if __name__ == "__main__":
    main()
