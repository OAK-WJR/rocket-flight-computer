#!/usr/bin/env python3
"""Price the generated BOM at JLCPCB and check the R3 cost targets.

usage: python3 tools/jlc_cost.py [--boards N] [--tier standard|economic] [--max-total USD] [--max-extended N]
Reads m3_design/assembly_review/fab/m3_bom_jlc.csv (run tools/export_fab.py first), queries
JLCPCB's public component search for each LCSC code, prices each line at the quantity the
order needs (qty x boards, at that price break), writes fab/cost_check.json and exits 1 if a
target is missed. REQUIREMENTS M3: R4 must not cost more than R3 per board at 5 boards, counting what the
owner pays for parts: placed-quantity part prices plus JLC's per-part feeder fee for the tier ordered
(jlcpcb.com/help/article/pcb-assembly-price, updated 2026-09-09): Standard PCBA $1.53 per unique LCSC code, Basic or
Extended; Economic PCBA $3.07 per unique Extended code. The order uses Standard (validation pass 6: Economic's
255 +/- 5 C reflow is above four parts' 250 C limits); Standard's larger fixed fees are reported, not gated: setup
and stencil are charged per assembled side (setup $25.56 / $51.12 and stencil $8.21 / $16.42 single / double side;
fetched 2026-10-10), the fixture $16.42 either way, plus a $14.93 handling fee JLC may add. The side count comes from
the CPL's Layer column (R5 places parts on both sides; Economic PCBA is single-sided only).
R3: $54.94 + 48 x $3.07 / 5 = $84.41 per board. Also <= 48 unique extended codes. JLC's minimum purchase
per line (minPurchaseNum) is priced and reported as the order price; attrition extras are not modelled.
PCB and shipping fees are the same for R3 and R4 and are left out; setup, stencil and fixture fees are reported
(not gated). Prices change daily: re-run right before ordering.
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
    ap.add_argument('--tier', choices=('standard', 'economic'), default='standard', help='JLC PCBA tier (docs/ORDERING.md)')
    ap.add_argument('--fee', type=float, default=None, help='override the per-code feeder fee, USD')
    ap.add_argument('--max-total', type=float, default=84.41, help='parts + extended fees per board, USD (REQUIREMENTS M3, R3 value)')
    ap.add_argument('--max-extended', type=int, default=48, help='unique extended (non-Basic) LCSC codes')
    a = ap.parse_args()
    rows = list(csv.DictReader(open(FAB / 'm3_bom_jlc.csv')))
    sides = len({r['Layer'] for r in csv.DictReader(open(FAB / 'm3_cpl_jlc.csv'))})
    # owner-fitted parts (fab/m3_bom_owner.csv, validation pass 5): bought by the owner, so they count in the parts
    # cost, but JLC does not load them, so they carry no extended-part fee
    own = FAB / 'm3_bom_owner.csv'
    for r in (csv.DictReader(open(own)) if own.exists() else []):
        r['owner'] = True
        rows.append(r)
    lines, unpriced = [], []
    for r in rows:
        code, qty = r['LCSC Part #'], int(r['Qty'])
        it = lookup(code); time.sleep(0.25)
        price = unit_price(it, qty * a.boards)
        if price is None:
            unpriced.append(code)
        moq = it.get('minPurchaseNum') or 1
        order_qty = max(qty * a.boards, moq)
        order_price = unit_price(it, order_qty) or 0
        lines.append(dict(lcsc=code, refs=r['Designator'], qty_per_board=qty, unit_usd=price,
                          line_usd_per_board=round((price or 0) * qty, 4), min_purchase=moq,
                          order_usd_per_board=round(order_price * order_qty / a.boards, 4), library=it.get('componentLibraryType'),
                          preferred=it.get('preferredComponentFlag'), stock=it.get('stockCount'), owner_fitted=bool(r.get('owner'))))
    parts = sum(l['line_usd_per_board'] for l in lines)
    order = sum(l['order_usd_per_board'] for l in lines)
    # JLC charges the extended-part fee per unique LCSC code, not per BOM row
    # (J1/J9/J120/J121 share C2915641 but export as separate rows).
    fee = a.fee if a.fee is not None else {'standard': 1.53, 'economic': 3.07}[a.tier]
    extended = sorted({l['lcsc'] for l in lines if l['library'] != 'base' and not l['owner_fitted']})
    charged = extended if a.tier == 'economic' else sorted({l['lcsc'] for l in lines if not l['owner_fitted']})
    total = parts + len(charged) * fee / a.boards
    # setup + stencil per assembled side; Standard also charges a fixture fee ($16.42 up to 29 boards, either side
    # count) and may add a $14.93 handling fee. Economic assembles one side only.
    fixed = {'standard': (25.56 + 8.21) * sides + 16.42, 'economic': 8.18 + 1.53}
    if a.tier == 'economic' and sides > 1:
        print('Economic PCBA assembles one side only; this board has parts on both sides')
    json.dump(dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), boards=a.boards,
                   tier=a.tier, sides=sides, fee_usd_per_code=fee, charged_codes=len(charged),
                   fixed_fees_usd_per_order=round(fixed[a.tier], 2),
                   handling_fee_may_apply_usd=14.93 if a.tier == 'standard' else 0.0,
                   parts_usd_per_board=round(parts, 2), feeder_fee_usd_per_order=round(len(charged) * fee, 2),
                   total_usd_per_board=round(total, 2), order_usd_per_board_with_min_purchase=round(order, 2),
                   extended_codes=extended, lines=lines),
              open(FAB / 'cost_check.json', 'w'), indent=1)
    print(f'{len(lines)} BOM lines at {a.boards} boards, {a.tier} PCBA: parts ${parts:.2f}/board + {len(charged)} codes x ${fee:.2f} / '
          f'{a.boards} = ${total:.2f}/board (target <= ${a.max_total:.2f}); unique extended codes {len(extended)} (target <= {a.max_extended})')
    print(f'  fixed fees per order ({a.tier}, {sides}-sided): ${fixed[a.tier]:.2f} (setup, stencil' +
          (', fixture; JLC may add a $14.93 handling fee' if a.tier == 'standard' else '') +
          ('); Economic assembles one side only' if sides > 1 else f'); Economic would be ${fixed["economic"]:.2f}') +
          f'; one side: ${25.56 + 8.21 + 16.42:.2f}. Not in the target: PCB, edge rails, joints and shipping')
    print(f'  with JLC minimum purchases: ${order:.2f}/board ordered (attrition extras not modelled)')
    for l in lines:
        if l['owner_fitted']:
            print(f"  owner-fitted, no JLC fee: {l['refs']} {l['lcsc']} ${l['line_usd_per_board']:.3f}/board (JLC price as the LCSC estimate)")
    for l in lines:
        if l['min_purchase'] > l['qty_per_board'] * a.boards:
            print(f"  minimum purchase {l['min_purchase']} for {l['lcsc']} ({l['refs'][:40]}): ${l['order_usd_per_board']:.2f}/board")
    for l in sorted(lines, key=lambda l: -l['line_usd_per_board'])[:8]:
        print(f"  ${l['line_usd_per_board']:7.3f}  {l['lcsc']:<10} {l['library'] or '?':<6} {l['refs'][:50]}")
    if unpriced:
        print('unpriced:', *unpriced)
    ok = total <= a.max_total and len(extended) <= a.max_extended and not unpriced
    print('cost targets: ' + ('met' if ok else 'NOT met'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
