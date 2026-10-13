#!/usr/bin/env python3
"""Check JLCPCB assembly stock for every line of the generated BOM.

usage: python3 tools/jlc_stock.py [--boards N]      (default 5)
Reads m3_design/assembly_review/fab/m3_bom_jlc.csv (run tools/export_fab.py first), queries
JLCPCB's public component search for each LCSC code, writes fab/stock_check.json and lists
every line whose JLC stock is below what the order needs: qty x boards, or JLC's minimum purchase
(minPurchaseNum) when that is larger. Lines with less than twice that are listed as thin, so a single
other buyer cannot empty them before the order. Stock changes daily: re-run right before ordering.
"""
import argparse, csv, datetime, json, subprocess, time
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--boards', type=int, default=5)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(FAB / 'm3_bom_jlc.csv')))
    own = FAB / 'm3_bom_owner.csv'                # owner-fitted parts (pass 5): JLC stock as the LCSC estimate
    rows += list(csv.DictReader(open(own))) if own.exists() else []
    lines, short, thin = [], [], []
    for r in rows:
        it = lookup(r['LCSC Part #']); time.sleep(0.25)
        moq = it.get('minPurchaseNum') or 1
        need = max(int(r['Qty']) * a.boards, moq)
        stock = it.get('stockCount')
        lines.append(dict(lcsc=r['LCSC Part #'], refs=r['Designator'], qty_per_board=int(r['Qty']), jlc_stock=stock,
                          min_purchase=moq, order_qty=need, library=it.get('componentLibraryType'),
                          model=it.get('componentModelEn'), assembly=r['Assembly']))
        if stock is None or stock < need:
            short.append(f"{r['LCSC Part #']} {r['Designator']} stock {stock} < {need} ({r['Assembly']})")
        elif stock < 2 * need:
            thin.append(f"{r['LCSC Part #']} {r['Designator']} stock {stock} for {need}")
    json.dump(dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                   source='jlcpcb.com selectSmtComponentList (stockCount)', boards=a.boards, lines=lines),
              open(FAB / 'stock_check.json', 'w'), indent=1)
    print(f'{len(lines)} BOM lines checked for {a.boards} boards;',
          sum(1 for l in lines if l['library'] == 'expand'), 'extended /', sum(1 for l in lines if l['library'] == 'base'), 'basic')
    print('short:', *short, sep='\n  ') if short else print('short: none')
    print('thin (stock < 2 x order):', *thin, sep='\n  ') if thin else print('thin (stock < 2 x order): none')


if __name__ == '__main__':
    main()
