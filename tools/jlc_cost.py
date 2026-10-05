#!/usr/bin/env python3
"""Price the generated BOM at JLCPCB and check the R3 cost targets.

usage: python3 tools/jlc_cost.py [--boards N] [--max-parts USD] [--max-extended N]
Reads m3_design/assembly_review/fab/m3_bom_jlc.csv (run tools/export_fab.py first), queries
JLCPCB's public component search for each LCSC code, prices each line at the quantity the
order needs (qty x boards, at that price break), writes fab/cost_check.json and exits 1 if a
target is missed. Default targets are the achievable M3-ASSY-R3 floor (docs/M3_R3.md): parts <= $56 per
board and <= 48 unique extended LCSC codes at 5 boards. Prices are at the placed quantity;
JLC order minimums and attrition add roughly $4/board at 5 boards (not modelled here). Prices change daily: re-run right before ordering.
The extended-part loading fee and PCB/PCBA fees are not included; see docs/ORDERING.md.
"""
import argparse, csv, datetime, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAB = ROOT / 'm3_design/assembly_review/fab'
API = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'


def lookup(code):
    body = json.dumps({'keyword': code, 'currentPage': 1, 'pageSize': 5})
    out = subprocess.run(['curl', '-s', '-A', 'Mozilla/5.0', '-H', 'Content-Type: application/json', '-X', 'POST', API, '-d', body],
                         capture_output=True, text=True).stdout
    try:
        for it in json.loads(out)['data']['componentPageInfo']['list'] or []:
            if it.get('componentCode') == code:
                return it
    except (ValueError, KeyError, TypeError):
        pass
    return {}


def unit_price(item, need):
    """Price per part at the break that covers `need` parts (JLC lists breaks as start..end, end -1 = open)."""
    breaks = item.get('componentPrices') or []
    for p in breaks:
        if p['startNumber'] <= need and (p['endNumber'] == -1 or need <= p['endNumber']):
            return p['productPrice']
    return breaks[0]['productPrice'] if breaks else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--boards', type=int, default=5)
    ap.add_argument('--max-parts', type=float, default=56.0, help='parts cost per board, USD')
    ap.add_argument('--max-extended', type=int, default=48, help='unique extended (non-Basic) LCSC codes')
    a = ap.parse_args()
    rows = list(csv.DictReader(open(FAB / 'm3_bom_jlc.csv')))
    lines, unpriced = [], []
    for r in rows:
        code, qty = r['LCSC Part #'], int(r['Qty'])
        it = lookup(code); time.sleep(0.25)
        price = unit_price(it, qty * a.boards)
        if price is None:
            unpriced.append(code)
        lines.append(dict(lcsc=code, refs=r['Designator'], qty_per_board=qty, unit_usd=price,
                          line_usd_per_board=round((price or 0) * qty, 4), library=it.get('componentLibraryType'),
                          preferred=it.get('preferredComponentFlag'), stock=it.get('stockCount')))
    parts = sum(l['line_usd_per_board'] for l in lines)
    # JLC charges the extended-part fee per unique LCSC code, not per BOM row
    # (J1/J9/J120/J121 share C2915641 but export as separate rows).
    extended = sorted({l['lcsc'] for l in lines if l['library'] != 'base'})
    json.dump(dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), boards=a.boards,
                   parts_usd_per_board=round(parts, 2), extended_codes=extended, lines=lines),
              open(FAB / 'cost_check.json', 'w'), indent=1)
    print(f'{len(lines)} BOM lines at {a.boards} boards: parts ${parts:.2f}/board (target <= ${a.max_parts:.2f}), '
          f'unique extended codes {len(extended)} (target <= {a.max_extended})')
    for l in sorted(lines, key=lambda l: -l['line_usd_per_board'])[:8]:
        print(f"  ${l['line_usd_per_board']:7.3f}  {l['lcsc']:<10} {l['library'] or '?':<6} {l['refs'][:50]}")
    if unpriced:
        print('unpriced:', *unpriced)
    ok = parts <= a.max_parts and len(extended) <= a.max_extended and not unpriced
    print('cost targets: ' + ('met' if ok else 'NOT met'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
