#!/usr/bin/env python3
"""Bind final procurement evidence to current CAD; cost-only is preliminary."""
import argparse
import datetime
import json
from pathlib import Path

from fab_manifest import verify_manifest
from jlc_stock import FAB, input_hashes


def verify(folder, cost_only=False, now=None, board=None):
    folder = Path(folder)
    if not cost_only:
        verify_manifest(board or folder.parent / 'm3.kicad_pcb', folder)
    now = now or datetime.datetime.now(datetime.timezone.utc)
    for name in (['cost_check.json'] if cost_only else ['cost_check.json', 'stock_check.json']):
        report = json.loads((folder / name).read_text())
        is_cost = name == 'cost_check.json'
        boards = report.get('boards')
        if type(boards) is not int or boards < 1:
            raise ValueError(f'{name}: board quantity must be a positive integer')
        if report.get('inputs_sha256') != input_hashes(folder, include_cpl=is_cost):
            raise ValueError(f'{name}: BOM/CPL changed or report lacks input binding')
        checked = datetime.datetime.fromisoformat(
            report.get('supplier_checked_utc', report['checked_utc']).replace('Z', '+00:00'))
        if checked.tzinfo is None or not 0 <= (now - checked).total_seconds() <= 86400:
            raise ValueError(f'{name}: supplier evidence is missing a timezone, future-dated or older than 24 hours')
        if not report.get('lines') or report.get('ok') is not True:
            raise ValueError(f'{name}: procurement target is not met')
        if is_cost:
            cost = report
            if (report.get('targets') != {'max_total': 84.41, 'max_extended': 48}
                    or report.get('errors') or report['total_usd_per_board'] > 84.41
                    or len(report['extended_codes']) > 48):
                raise ValueError(f'{name}: required $84.41 / 48-code targets were changed or missed')
            default_fee = {'standard': 1.53, 'economic': 3.07}.get(report.get('tier'))
            if not cost_only and (default_fee is None or report.get('fee_usd_per_code') != default_fee):
                raise ValueError(f'{name}: unknown assembly tier or nonstandard feeder fee; '
                                 'fee overrides are preliminary, not release evidence')
        else:
            if boards != cost['boards']:
                raise ValueError(f'{name}: board quantity differs from the cost report')
            if report.get('short'):
                raise ValueError(f'{name}: supplier inventory is insufficient')
    return cost


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fab', type=Path, default=FAB)
    parser.add_argument('--board', type=Path, help='CAD source for final verification; default: FAB/../m3.kicad_pcb')
    parser.add_argument('--cost-only', action='store_true',
                        help='preliminary pricing only; skips current CAD/fab binding and stock verification')
    args = parser.parse_args()
    try:
        cost = verify(args.fab, args.cost_only, board=args.board)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'Procurement evidence: FAIL: {error}\n')
    if args.cost_only:
        print('Procurement evidence: PRELIMINARY cost check OK; BOM/CPL and recent supplier data verified. '
              'Current CAD/fab binding and stock were not verified. Not a release pass.')
    else:
        print('Procurement evidence: OK; current CAD/fab outputs, BOM/CPL, recent supplier data and required targets')
    print(f"Components + feeder fees ({cost['boards']} boards, {cost['tier']}): "
          f"${cost['total_usd_per_board']:.2f}/board; "
          f"ordered components with minimum purchases: ${cost['order_usd_per_board_with_min_purchase']:.2f}/board. "
          'The $84.41 target excludes fixed assembly fees, PCB fabrication and shipping.')
