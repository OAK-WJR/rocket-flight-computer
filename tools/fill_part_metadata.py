#!/usr/bin/env python3
"""Fill missing verified part identities, preserving every other native CAD field.

Dry-run by default. --write updates only fitted PCB parts and their hierarchical
schematic instances, using the existing LCSC code without substituting parts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'quality_audit'))
from audit_artifacts import is_fitted_footprint
from sexpr import patch, properties, quote, read

FIELDS = ('Manufacturer', 'Manufacturer Part')


def instances(root):
    if root.key not in ('kicad_pcb', 'kicad_sch'):
        raise ValueError('Expected a native PCB or schematic')
    # Do not touch nested library symbol definitions.
    return root.children('footprint' if root.key == 'kicad_pcb' else 'symbol')


def identity_preserved(before, after, changes):
    """Restore exactly the allowed field edits and compare complete parsed trees."""
    old, new = read(before), read(after)
    nodes = {}
    for node in instances(new):
        props = properties(node)
        ref = props['Reference'].items[2].atom
        if ref in nodes:
            raise ValueError('Duplicate reference ' + ref)
        nodes[ref] = node
    for change in changes:
        field = change['field']
        if field not in FIELDS:
            raise ValueError('Unexpected metadata field ' + field)
        node = nodes[change['ref']]
        prop = properties(node)[field]
        if prop.items[2].atom != change['after']:
            raise ValueError('Metadata result differs from proposed change')
        if change['before'] is None:
            node.items.remove(prop)
        else:
            prop.items[2].atom = change['before']
    return old.value() == new.value()


def fill(text, catalog, fitted_refs=None):
    root = read(text)
    pcb = root.key == 'kicad_pcb'
    if not pcb and fitted_refs is None:
        raise ValueError('Schematic repair requires fitted PCB references')
    edits, changes, seen = [], [], set()
    uuids = set(re.findall(r'\(uuid\s+"?([a-fA-F0-9-]+)', text))
    for node in instances(root):
        props = properties(node)
        ref = props['Reference'].items[2].atom
        if ref in seen:
            raise ValueError('Duplicate reference ' + ref)
        seen.add(ref)
        if pcb and not is_fitted_footprint(node.value()):
            continue
        if not pcb and ref not in fitted_refs:
            continue
        code = props.get('LCSC')
        if code is None or not code.items[2].atom.strip():
            raise ValueError('Missing LCSC identity for ' + ref)
        missing = [key for key in FIELDS if key not in props or not props[key].items[2].atom.strip()]
        if not missing:
            continue
        part = catalog.get(code.items[2].atom)
        if part is None or any(not part.get(key, '').strip() for key in FIELDS):
            raise ValueError('No complete verified identity for ' + ref + ' / ' + code.items[2].atom)
        for key in FIELDS:
            if key not in missing and props[key].items[2].atom != part[key]:
                raise ValueError('Existing identity disagrees with catalog for ' + ref + ' / ' + key)
        hidden = code.children('hide')
        if not hidden or hidden[0].items[1].atom != 'yes':
            raise ValueError('Expected hidden LCSC template for ' + ref)
        additions = []
        for key in missing:
            existing = props.get(key)
            if existing:
                hidden = existing.children('hide')
                if not hidden or hidden[0].items[1].atom != 'yes':
                    raise ValueError('Expected hidden identity target for ' + ref + ' / ' + key)
            changes.append({'ref': ref, 'lcsc': code.items[2].atom, 'field': key,
                            'before': existing.items[2].atom if existing else None,
                            'after': part[key]})
            if existing:
                value = existing.items[2]
                edits.append((value.start, value.end, quote(part[key])))
                continue
            template = read(text[code.start:code.end])
            replacements = [(template.items[1].start, template.items[1].end, quote(key)),
                            (template.items[2].start, template.items[2].end, quote(part[key]))]
            if pcb:
                ids = template.children('uuid')
                if len(ids) != 1:
                    raise ValueError('Expected unique PCB property UUID for ' + ref)
                identifier = str(uuid4())
                while identifier in uuids:
                    identifier = str(uuid4())
                uuids.add(identifier)
                token = ids[0].items[1]
                replacements.append((token.start, token.end, quote(identifier)))
            additions.append(patch(text[code.start:code.end], replacements))
        if additions:
            line_start = text.rfind('\n', 0, code.start) + 1
            indent = text[line_start:code.start]
            if indent.strip():
                indent = '\t\t'
            edits.append((code.end, code.end, ''.join('\n' + indent + item for item in additions)))
    result = patch(text, edits)
    if not identity_preserved(text, result, changes):
        raise RuntimeError('CAD changed outside the intended identity fields')
    return result, changes


def fitted_parts(text):
    result = {}
    for node in read(text).children('footprint'):
        if is_fitted_footprint(node.value()):
            props = properties(node)
            ref = props['Reference'].items[2].atom
            if ref in result:
                raise ValueError('Duplicate fitted reference ' + ref)
            result[ref] = props.get('LCSC').items[2].atom if props.get('LCSC') else ''
    return result


def plan(project, catalog):
    board = project / 'm3.kicad_pcb'
    paths = [board, *sorted(project.glob('*.kicad_sch'))]
    before = {path: path.read_text() for path in paths}
    fitted = fitted_parts(before[board])
    seen = set()
    for path in paths[1:]:
        for symbol in instances(read(before[path])):
            props = properties(symbol)
            ref = props['Reference'].items[2].atom
            if ref not in fitted:
                continue
            if ref in seen:
                raise ValueError('Duplicate hierarchical schematic reference ' + ref)
            seen.add(ref)
            if not props.get('LCSC') or props['LCSC'].items[2].atom != fitted[ref]:
                raise ValueError('PCB/schematic LCSC disagreement for ' + ref)
    if seen != fitted.keys():
        raise ValueError('Fitted references missing from schematic: ' + ', '.join(sorted(fitted.keys() - seen)))
    return [(path, before[path], *fill(before[path], catalog, fitted)) for path in paths]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=ROOT / 'm3_design/assembly_review')
    parser.add_argument('--catalog', type=Path, default=Path(__file__).with_name('verified_part_metadata.json'))
    parser.add_argument('--write', action='store_true', help='Apply the verified changes; default is dry-run')
    parser.add_argument('--report', type=Path, help='Optional JSON change evidence')
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text())
    plans = plan(args.project, catalog['parts'])
    if args.write:
        # Validate every file before the first write; reject concurrent CAD edits.
        for path, before, _, _ in plans:
            if path.read_text() != before:
                raise RuntimeError('Concurrent modification: ' + str(path))
        for path, before, after, _ in plans:
            if before != after:
                path.write_text(after)
    evidence = {'mode': 'write' if args.write else 'dry-run',
                'catalog_sha256': hashlib.sha256(args.catalog.read_bytes()).hexdigest(),
                'source': catalog['source'], 'reviewed_date': catalog['reviewed_date'],
                'files': [{'file': path.name,
                           'before_sha256': hashlib.sha256(before.encode()).hexdigest(),
                           'after_sha256': hashlib.sha256(after.encode()).hexdigest(),
                           'other_cad_fields_unchanged': identity_preserved(before, after, changes),
                           'changes': changes}
                          for path, before, after, changes in plans]}
    if args.report:
        args.report.write_text(json.dumps(evidence, indent=2) + '\n')
    print(evidence['mode'] + ': ' + str(sum(len(c) for _, _, _, c in plans)) +
          ' identity fields across ' + str(sum(bool(c) for _, _, _, c in plans)) + ' files')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
