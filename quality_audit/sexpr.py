"""Small lossless S-expression reader; edits use token spans, not reserialization."""
from dataclasses import dataclass, field
import hashlib
import json
import re

TOKEN = re.compile(r'\s+|"(?:\\.|[^"\\])*"|[()]|[^\s()"\\]+')


@dataclass
class Node:
    start: int
    end: int
    atom: str = None
    items: list = field(default_factory=list)

    @property
    def key(self):
        return self.items[0].atom if self.items else None

    def children(self, key):
        return [x for x in self.items if x.atom is None and x.key == key]

    def value(self):
        return self.atom if self.atom is not None else [x.value() for x in self.items]


def read(text):
    stack, roots, pos = [], [], 0
    while pos < len(text):
        match = TOKEN.match(text, pos)
        if match is None:
            raise ValueError('Invalid or unterminated token at character %d' % pos)
        token = match.group()
        start, pos = pos, match.end()
        if token.isspace():
            continue
        if token == ')':
            if not stack:
                raise ValueError('Unbalanced closing parenthesis')
            stack.pop().end = pos
            continue
        node = Node(start, pos)
        (stack[-1].items if stack else roots).append(node)
        if token == '(':
            stack.append(node)
        else:
            node.atom = (re.sub(r'\\(["\\])', r'\1', token[1:-1])
                         if token.startswith('"') else token)
    if stack or len(roots) != 1 or roots[0].atom is not None:
        raise ValueError('Expected exactly one complete list')
    return roots[0]


def quote(value):
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def patch(text, edits):
    """Replace disjoint spans; reject overlapping/out-of-range edits."""
    last = len(text)
    for start, end, replacement in sorted(edits, reverse=True):
        if not 0 <= start <= end <= last:
            raise ValueError('Overlapping or invalid edit')
        text = text[:start] + replacement + text[end:]
        last = start
    read(text)
    return text


def properties(fp):
    result = {}
    for p in fp.children('property'):
        if len(p.items) < 3:
            raise ValueError('Malformed footprint property')
        name = p.items[1].atom
        if name in result:
            raise ValueError('Duplicate property: ' + name)
        result[name] = p
    return result


def protected_digest(text):
    """Hash everything except distributor metadata/descriptions and model filenames.

    Preserves Reference/Value, placement, pads, tracks, nets, zones (including fills),
    silkscreen, settings, UUIDs and model scale/rotation/offset.
    """
    root = read(text)

    def footprint(fp):
        result = []
        for node in fp.items:
            if node.key == 'descr':
                continue
            if node.key == 'property' and node.items[1].atom in (
                    'LCSC', 'LCSC Part', 'Description'):
                continue
            if node.key == 'model':
                result.append(['model', '<path>'] + [n.value() for n in node.items[2:]])
            else:
                result.append(node.value())
        return result

    if root.key == 'kicad_pcb':
        obj = [footprint(n) if n.key == 'footprint' else n.value() for n in root.items]
    elif root.key in ('footprint', 'module'):
        obj = footprint(root)
    else:
        raise ValueError('Not a PCB or footprint')
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()
