"""Replay independently reviewed native PCB object changes; reject partial state."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'quality_audit'))
from sexpr import read, patch


def semantic(value):
    """Generated UUIDs may differ on rebuild; every other CAD field is guarded."""
    if not isinstance(value, list):
        return value
    return [semantic(item) for item in value
            if not (isinstance(item, list) and item and item[0] == 'uuid')]


def apply_delta(text, data):
    root = read(text)
    objects = [n for n in root.items if n.key in ('footprint', 'segment', 'via', 'zone', 'gr_text', 'gr_line')]
    index = {}
    def key(value):
        return json.dumps(semantic(value), separators=(',', ':'))
    for node in objects:
        index.setdefault(key(node.value()), []).append(node)
    def find(source):
        found = index.get(key(read(source).value()), [])
        if len(found) > 1:
            raise RuntimeError('Ambiguous patch object; inspect native CAD.')
        return found[0] if found else None
    before = [find(s) for s in data['before']]
    after = [find(s) for s in data['after']]
    if all(n is not None for n in after) and not any(n is not None for n in before):
        return text
    if any(n is not None for n in after) or not all(n is not None for n in before):
        raise RuntimeError('Changed or partial scoped repair; inspect native CAD.')
    edits = [(n.start, n.end, '') for n in before]
    edits.append((root.end - 1, root.end - 1, '\n\t' + '\n\t'.join(data['after']) + '\n'))
    result = patch(text, edits)
    identifiers = []
    def collect(value):
        if isinstance(value, list):
            if value and value[0] == 'uuid':
                identifiers.append(value[1])
            for item in value:
                collect(item)
    collect(read(result).value())
    if len(identifiers) != len(set(identifiers)):
        raise RuntimeError('Patch creates duplicate UUIDs; no write performed.')
    return result
