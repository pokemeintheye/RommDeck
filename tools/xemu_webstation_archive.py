"""Reference Xbox save archive adapter for RommDeck/Webstation.

This is a diagnostic tool; the native C implementation is used for synchronization.
It refuses unsafe or ambiguous inputs rather than silently losing saves.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import time
import zipfile
from pathlib import PurePosixPath, Path

TITLE = re.compile(r"[0-9a-fA-F]{8}\Z")
MANIFEST = '.broker-manifest.json'


class UnsafeArchive(ValueError):
    pass


def _entries(data: bytes) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for item in zf.infolist():
            if item.is_dir():
                continue
            name = item.filename
            parts = PurePosixPath(name).parts
            if (not name or '\\' in name or name.startswith('/') or
                any(part in ('', '.', '..') for part in name.split('/')) or
                any(part.startswith('.') for part in parts if part != MANIFEST)):
                raise UnsafeArchive(f'Unsafe archive member: {name!r}')
            if name in result:
                raise UnsafeArchive(f'Duplicate archive member: {name!r}')
            result[name] = zf.read(item)
    return result


def _write(entries: dict[str, bytes]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for path, content in sorted(entries.items()):
            zf.writestr(path, content)
    return out.getvalue()


def rommdeck_to_webstation(data: bytes, title_id: str) -> bytes:
    """Wrap a single UDATA title save in a broker-native restore archive."""
    if not TITLE.fullmatch(title_id):
        raise ValueError('title ID must be eight hexadecimal characters')
    members = _entries(data)
    if not members:
        raise UnsafeArchive('Empty save archive')
    result = {}
    for name, content in members.items():
        parts = name.split('/')
        if parts[0] == 'TDATA':
            if len(parts) < 3 or parts[1].lower() != title_id.lower():
                raise UnsafeArchive(f'Expected TDATA/title-ID member, got {name!r}')
            result['saves/' + name] = content
        elif len(parts) >= 2 and parts[0].lower() == title_id.lower():
            result['saves/UDATA/' + name] = content
        else:
            raise UnsafeArchive(f'Expected title-ID-rooted or TDATA member, got {name!r}')
    manifest = {
        'version': 1,
        'created_at': time.time(),
        'session': {'emulator': 'xemu', 'platform': 'xbox'},
        'files': [{'path': name, 'kind': 'save'} for name in sorted(result)],
    }
    result[MANIFEST] = json.dumps(manifest, separators=(',', ':')).encode()
    return _write(result)


def webstation_to_rommdeck(data: bytes, title_id: str) -> bytes:
    """Unwrap a native broker archive without silently dropping other save types."""
    if not TITLE.fullmatch(title_id):
        raise ValueError('title ID must be eight hexadecimal characters')
    members = _entries(data)
    result = {}
    for name, content in members.items():
        if name == MANIFEST:
            continue
        parts = name.split('/')
        if len(parts) >= 4 and parts[0] == 'saves' and parts[1].upper() in ('UDATA', 'TDATA') and parts[2].lower() == title_id.lower():
            relative = '/'.join(parts[2:])
            if parts[1].upper() == 'TDATA':
                relative = 'TDATA/' + relative
            result[relative] = content
        else:
            raise UnsafeArchive(f'Not safely representable by RommDeck Xbox layout: {name!r}')
    if not result:
        raise UnsafeArchive('No UDATA save for requested title')
    return _write(result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('direction', choices=['to-webstation', 'to-rommdeck'])
    parser.add_argument('title_id')
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    transform = rommdeck_to_webstation if args.direction == 'to-webstation' else webstation_to_rommdeck
    args.destination.write_bytes(transform(args.source.read_bytes(), args.title_id))


if __name__ == '__main__':
    main()
