#!/usr/bin/env python3
"""Check JLCPCB assembly stock for every line of the generated BOM.

usage: python3 tools/jlc_stock.py [--boards N]      (default 5)
Reads m3_design/assembly_review/fab/m3_bom_jlc.csv (run tools/export_fab.py first), queries
JLCPCB's public component search once per LCSC code, writes fab/stock_check.json and fails
when stock is unknown or below the aggregate demand: qty x boards, or JLC's minimum purchase
(minPurchaseNum) when that is larger. Lines with less than twice that are listed as thin, so a single
other buyer cannot empty them before the order. Stock changes daily: re-run right before ordering.
"""
import argparse, csv, datetime, hashlib, json, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAB = ROOT / 'm3_design/assembly_review/fab'
API = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'


def supplier_snapshot(path, now=None):
    """Reuse a recent exact supplier response without relabelling it as a live query."""
    path = Path(path)
    data = json.loads(path.read_text())
    checked = datetime.datetime.fromisoformat(data['checked_utc'].replace('Z', '+00:00'))
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if checked.tzinfo is None or not 0 <= (now - checked).total_seconds() <= 86400:
        raise ValueError('supplier snapshot must be timezone-qualified and at most 24 hours old')
    if data.get('source') != API or not isinstance(data.get('parts'), dict):
        raise ValueError('unrecognized supplier snapshot source or format')
    for code, item in data['parts'].items():
        if not isinstance(item, dict) or item.get('componentCode') != code:
            raise ValueError(f'invalid exact supplier identity for {code}')
    return data


def lookup(code):
    body = json.dumps({'keyword': code, 'currentPage': 1, 'pageSize': 5})
    try:
        out = subprocess.run(['curl', '-fsS', '--max-time', '15', '-A', 'Mozilla/5.0', '-H',
            'Content-Type: application/json', '-X', 'POST', API, '-d', body],
            capture_output=True, text=True, timeout=20, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    try:
        for it in json.loads(out)['data']['componentPageInfo']['list'] or []:
            if it.get('componentCode') == code:
                return it
    except (ValueError, KeyError, TypeError):
        pass
    return {}


def input_hashes(folder, include_cpl=False):
    names = ['m3_bom_jlc.csv']
    if (folder / 'm3_bom_owner.csv').exists():
        names.append('m3_bom_owner.csv')
    if include_cpl:
        names.append('m3_cpl_jlc.csv')
    return {name: hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in names}


def read_bom(folder):
    """One purchase per code, including codes shared by multiple footprint/BOM rows."""
    parts, refs_seen = {}, set()
    for name, owner in (('m3_bom_jlc.csv', False), ('m3_bom_owner.csv', True)):
        path = folder / name
        if owner and not path.exists():
            continue
        with path.open(newline='') as source:
            for row in csv.DictReader(source):
                code = row['LCSC Part #'].strip()
                refs = [ref.strip() for ref in row['Designator'].split(',')]
                qty = int(row['Qty'])
                if not re.fullmatch(r'C\d+', code) or qty <= 0 or not all(refs) or len(set(refs)) != qty:
                    raise ValueError(f'invalid BOM row: {row}')
                if refs_seen.intersection(refs):
                    raise ValueError(f'duplicate BOM designator: {refs_seen.intersection(refs)}')
                refs_seen.update(refs)
                part = parts.setdefault(code, dict(lcsc=code, refs=[], qty_per_board=0,
                    jlc_qty_per_board=0, owner_qty_per_board=0, assembly=set()))
                part['refs'].extend(refs)
                part['qty_per_board'] += qty
                part['owner_qty_per_board' if owner else 'jlc_qty_per_board'] += qty
                part['assembly'].add(row.get('Assembly', ''))
    if not parts:
        raise ValueError('empty BOM')
    return [dict(part, refs=','.join(sorted(part['refs'])), assembly='; '.join(sorted(part['assembly'])))
            for _, part in sorted(parts.items())]


def count(value):
    """Accept an integer supplier count; unknown, negative and fractional values fail closed."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if number >= 0 and str(number) == str(value) else None


def purchase_quantity(item, quantity):
    raw = item.get('minPurchaseNum')
    minimum = 1 if raw in (None, 0, '0') else count(raw)
    if minimum is None:
        raise ValueError(f'unknown minimum purchase: {raw!r}')
    return minimum, max(quantity, minimum)


def stock_report(parts, boards, fetch=None):
    if boards <= 0:
        raise ValueError('board quantity must be positive')
    fetch = fetch or lookup
    lines, short, thin = [], [], []
    for part in parts:
        item = fetch(part['lcsc'])
        stock = count(item.get('stockCount'))
        try:
            minimum, need = purchase_quantity(item, part['qty_per_board'] * boards)
        except ValueError as error:
            minimum, need = None, part['qty_per_board'] * boards
            short.append(f"{part['lcsc']} {error}")
        line = dict(part, jlc_stock=stock, min_purchase=minimum, order_qty=need,
                    library=item.get('componentLibraryType'), model=item.get('componentModelEn'))
        lines.append(line)
        if stock is None or stock < need:
            short.append(f"{part['lcsc']} {part['refs']} stock {stock} < {need}")
        elif stock < 2 * need:
            thin.append(f"{part['lcsc']} {part['refs']} stock {stock} for {need}")
    return dict(boards=boards, lines=lines, short=short, thin=thin, ok=not short)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--boards', type=int, default=5)
    ap.add_argument('--fab', type=Path, default=FAB)
    ap.add_argument('--snapshot', type=Path, help='exact public supplier responses fetched within the last 24 hours')
    a = ap.parse_args()
    output = a.fab / 'stock_check.json'
    output.unlink(missing_ok=True)
    try:
        before = input_hashes(a.fab)
        snapshot = supplier_snapshot(a.snapshot) if a.snapshot else None
        def fetch(code):
            if snapshot:
                return snapshot['parts'].get(code, {})
            item = lookup(code)
            time.sleep(0.25)
            return item
        report = stock_report(read_bom(a.fab), a.boards, fetch)
        if before != input_hashes(a.fab):
            raise ValueError('BOM changed during stock check')
    except (OSError, ValueError, KeyError) as error:
        ap.exit(1, f'Stock check: FAIL: {error}\n')
    report.update(checked_utc=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                  source='jlcpcb.com selectSmtComponentList (stockCount)', inputs_sha256=before)
    if snapshot:
        report.update(supplier_checked_utc=snapshot['checked_utc'],
                      supplier_snapshot_sha256=hashlib.sha256(a.snapshot.read_bytes()).hexdigest())
    output.write_text(json.dumps(report, indent=1) + '\n')
    lines, short, thin = report['lines'], report['short'], report['thin']
    print(f'{len(lines)} unique codes checked for {a.boards} boards;',
          sum(1 for l in lines if l['library'] == 'expand'), 'extended /', sum(1 for l in lines if l['library'] == 'base'), 'basic')
    print('short:', *short, sep='\n  ') if short else print('short: none')
    print('thin (stock < 2 x order):', *thin, sep='\n  ') if thin else print('thin (stock < 2 x order): none')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
