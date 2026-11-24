# Experimental xemu ↔ Webstation save-archive adapter

This branch is **not ready for deployment**. No production RommDeck synchronization code is modified yet.

## Why

RommDeck currently uploads Xbox saves rooted at `<title-id>/...`, but Webstation's broker-native restore files contain `UDATA/<title-id>/...` and can also contain `TDATA/...`. RomM's selection logic additionally uses the `.saves.zip` filename suffix to distinguish broker-native archives.

## Prototype

`tools/xemu_webstation_archive.py` can convert a single-game RommDeck ZIP to a broker-layout ZIP and convert UDATA-only broker archives back. This tool is for isolated tests; it is not invoked by the sync engine.

Run `python3 -m unittest discover -s tests -p 'test_xemu_webstation_archive.py' -v`.

## Required before wiring into RommDeck

- Validate acceptance by the exact broker release and RomM save metadata API.
- Handle `TDATA` without loss; the current prototype deliberately rejects it on download.
- Preserve RommDeck's hash, timestamp, conflict-resolution and legacy save semantics.
- Verify real Steam Deck → RomM → Webstation → RomM → Steam Deck round trips using backups and a test game.
- Never modify an open xemu disk image.
