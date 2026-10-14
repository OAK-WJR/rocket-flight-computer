#!/usr/bin/env python3
"""Price the generated BOM at JLCPCB and retain the $84.41 / 48-code cost targets.

usage: python3 tools/jlc_cost.py [--boards N] [--tier standard|economic] [--max-total USD] [--max-extended N]
Reads m3_design/assembly_review/fab/m3_bom_jlc.csv (run tools/export_fab.py first), queries
JLCPCB's public component search once per LCSC code, prices the aggregate quantity the
order needs (qty x boards, at that price break), binds fab/cost_check.json to BOM/CPL hashes
and exits 1 if a target is missed or supplier pricing is unknown. REQUIREMENTS M3 counts what the
owner pays for parts: placed-quantity part prices plus JLC's per-part feeder fee for the tier ordered
(jlcpcb.com/help/article/pcb-assembly-price, updated 2026-09-09): Standard PCBA $1.53 per unique LCSC code, Basic or
Extended; Economic PCBA $3.07 per unique Extended code. The order uses Standard (validation pass 6: Economic's
255 +/- 5 C reflow exceeds retained parts' 250 C limits); Standard's larger fixed fees are reported, not gated: setup
and stencil are charged per assembled side (setup $25.56 / $51.12 and stencil $8.21 / $16.42 single / double side;
fetched 2026-10-10), the fixture $16.42 either way, plus a $14.93 handling fee JLC may add. The side count comes from
the CPL's Layer column (R5 places parts on both sides; Economic PCBA is single-sided only).
R3: $54.94 + 48 x $3.07 / 5 = $84.41 per board. Also <= 48 unique extended codes. JLC's minimum purchase
per line (minPurchaseNum) is priced and reported as the order price; attrition extras are not modelled.
PCB, rails, soldering and shipping charges are outside this component/feeder target;
setup, stencil and fixture fees are reported (not gated). Prices change daily: re-run before ordering.
"""
import argparse, csv, datetime, hashlib, json, math, sys, time
from pathlib import Path

from jlc_stock import input_hashes, lookup, purchase_quantity, read_bom, supplier_snapshot

ROOT = Path(__file__).resolve().parent.parent
FAB = ROOT / 'm3_design/assembly_review/fab'


def unit_price(item, need):
    """Price per part at the break that covers `need` parts (JLC lists breaks as start..end, end -1 = open)."""
    breaks = item.get('componentPrices') or []
    for p in breaks:
        try:
            price = float(p['productPrice'])
            if p['startNumber'] <= need and (p['endNumber'] == -1 or need <= p['endNumber']):
                return price if math.isfinite(price) and price >= 0 else None
        except (KeyError, TypeError, ValueError):
            continue
    return None


def assembly_sides(path):
    with path.open(newline='') as source:
        sides = {row['Layer'] for row in csv.DictReader(source)}
    if not sides or not sides <= {'Top', 'Bottom'}:
        raise ValueError(f'invalid or empty CPL assembly sides: {sides}')
    return len(sides)


def cost_report(parts, boards, tier, sides, fee=None, max_total=84.41, max_extended=48, fetch=None):
    if boards <= 0 or sides not in (1, 2):
        raise ValueError('positive board quantity and one or two assembly sides required')
    if tier not in ('standard', 'economic'):
        raise ValueError('unknown assembly tier')
    if tier == 'economic' and sides != 1:
        raise ValueError('Economic PCBA assembles one side only; this board has parts on both sides')
    fee = {'standard': 1.53, 'economic': 3.07}[tier] if fee is None else fee
    if not math.isfinite(fee) or fee < 0:
        raise ValueError('invalid feeder fee')
    fetch = fetch or lookup
    lines, errors = [], []
    for part in parts:
        item = fetch(part['lcsc'])
        quantity = part['qty_per_board'] * boards
        try:
            minimum, order_qty = purchase_quantity(item, quantity)
        except ValueError as error:
            minimum, order_qty = None, quantity
            errors.append(f"{part['lcsc']}: {error}")
        price, order_price = unit_price(item, quantity), unit_price(item, order_qty)
        library = item.get('componentLibraryType')
        if price is None or order_price is None:
            errors.append(f"{part['lcsc']}: missing applicable price")
        if library not in ('base', 'expand'):
            errors.append(f"{part['lcsc']}: unknown library tier {library!r}")
        lines.append(dict(part, unit_usd=price, line_usd_per_board=(price or 0) * part['qty_per_board'],
            min_purchase=minimum, order_qty=order_qty, order_usd_per_board=(order_price or 0) * order_qty / boards,
            library=library, preferred=item.get('preferredComponentFlag'), stock=item.get('stockCount'),
            owner_fitted=part['jlc_qty_per_board'] == 0))
    subtotal = sum(line['line_usd_per_board'] for line in lines)
    ordered = sum(line['order_usd_per_board'] for line in lines)
    extended = sorted(line['lcsc'] for line in lines if line['library'] == 'expand' and not line['owner_fitted'])
    charged = extended if tier == 'economic' else sorted(line['lcsc'] for line in lines if not line['owner_fitted'])
    total = subtotal + len(charged) * fee / boards
    fixed = (25.56 + 8.21) * sides + 16.42 if tier == 'standard' else 8.18 + 1.53
    return dict(boards=boards, tier=tier, sides=sides, fee_usd_per_code=fee, charged_codes=len(charged),
        fixed_fees_usd_per_order=round(fixed, 2), handling_fee_may_apply_usd=14.93 if tier == 'standard' else 0.0,
        parts_usd_per_board=round(subtotal, 2), feeder_fee_usd_per_order=round(len(charged) * fee, 2),
        total_usd_per_board=round(total, 2), order_usd_per_board_with_min_purchase=round(ordered, 2),
        extended_codes=extended, lines=lines, errors=errors, targets=dict(max_total=max_total, max_extended=max_extended),
        ok=total <= max_total and len(extended) <= max_extended and not errors)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--boards', type=int, default=5)
    ap.add_argument('--tier', choices=('standard', 'economic'), default='standard', help='JLC PCBA tier (docs/ORDERING.md)')
    ap.add_argument('--fee', type=float, default=None, help='override the per-code feeder fee, USD')
    ap.add_argument('--max-total', type=float, default=84.41, help='parts + extended fees per board, USD (REQUIREMENTS M3, R3 value)')
    ap.add_argument('--max-extended', type=int, default=48, help='unique extended (non-Basic) LCSC codes')
    ap.add_argument('--fab', type=Path, default=FAB)
    ap.add_argument('--snapshot', type=Path, help='exact public supplier responses fetched within the last 24 hours')
    a = ap.parse_args()
    output = a.fab / 'cost_check.json'
    output.unlink(missing_ok=True)
    try:
        before = input_hashes(a.fab, include_cpl=True)
        snapshot = supplier_snapshot(a.snapshot) if a.snapshot else None
        def fetch(code):
            if snapshot:
                return snapshot['parts'].get(code, {})
            item = lookup(code)
            time.sleep(0.25)
            return item
        report = cost_report(read_bom(a.fab), a.boards, a.tier, assembly_sides(a.fab / 'm3_cpl_jlc.csv'),
                             a.fee, a.max_total, a.max_extended, fetch)
        if before != input_hashes(a.fab, include_cpl=True):
            raise ValueError('BOM or CPL changed during cost check')
    except (OSError, ValueError, KeyError) as error:
        ap.exit(1, f'Cost check: FAIL: {error}\n')
    report.update(checked_utc=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                  source='jlcpcb.com selectSmtComponentList', inputs_sha256=before)
    if snapshot:
        report.update(supplier_checked_utc=snapshot['checked_utc'],
                      supplier_snapshot_sha256=hashlib.sha256(a.snapshot.read_bytes()).hexdigest())
    output.write_text(json.dumps(report, indent=1) + '\n')
    lines, sides, extended = report['lines'], report['sides'], report['extended_codes']
    fee, charged, total = report['fee_usd_per_code'], report['charged_codes'], report['total_usd_per_board']
    print(f"{len(lines)} unique codes at {a.boards} boards, {a.tier} PCBA: parts ${report['parts_usd_per_board']:.2f}/board + "
          f'{charged} codes x ${fee:.2f} / {a.boards} = ${total:.2f}/board (target <= ${a.max_total:.2f}); '
          f'unique extended codes {len(extended)} (target <= {a.max_extended})')
    print(f"  fixed fees per order ({a.tier}, {sides}-sided): ${report['fixed_fees_usd_per_order']:.2f} (setup, stencil" +
          (', fixture; JLC may add a $14.93 handling fee' if a.tier == 'standard' else '') +
          ('); Economic assembles one side only' if sides > 1 else '); Economic would be $9.71') +
          f'; one side: ${25.56 + 8.21 + 16.42:.2f}. Not in the target: PCB, edge rails, joints and shipping')
    print(f"  with JLC minimum purchases: ${report['order_usd_per_board_with_min_purchase']:.2f}/board ordered (attrition extras not modelled)")
    for l in lines:
        if l['owner_fitted']:
            print(f"  owner-fitted, no JLC fee: {l['refs']} {l['lcsc']} ${l['line_usd_per_board']:.3f}/board (JLC price as the LCSC estimate)")
    for l in lines:
        if l['min_purchase'] and l['min_purchase'] > l['qty_per_board'] * a.boards:
            print(f"  minimum purchase {l['min_purchase']} for {l['lcsc']} ({l['refs'][:40]}): ${l['order_usd_per_board']:.2f}/board")
    for l in sorted(lines, key=lambda l: -l['line_usd_per_board'])[:8]:
        print(f"  ${l['line_usd_per_board']:7.3f}  {l['lcsc']:<10} {l['library'] or '?':<6} {l['refs'][:50]}")
    if report['errors']:
        print('unverified:', *report['errors'], sep='\n  ')
    print('cost targets: ' + ('met' if report['ok'] else 'NOT met'))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
