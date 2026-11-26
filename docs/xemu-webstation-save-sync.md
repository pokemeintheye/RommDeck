# Experimental Xbox xemu ↔ Webstation save sync

**Development branch, not a release. Do not enable on a live Steam Deck until the native build and end-to-end restore have been verified with backup saves.**

## Implemented

- RommDeck's C synchronization engine has an explicit opt-in: `ROMM_XEMU_WEBSTATION_ARCHIVES=1`.
- For **xemu** / `xbox` profiles only, new uploads use the `<title-id>.saves.zip` filename and the broker's **`saves/UDATA/<title-id>/...`** and **`saves/TDATA/<title-id>/...`** ZIP members.
- The existing RommDeck format remains the default for uploads when the variable is unset.
- The downloader supports both RommDeck's legacy title-ID-rooted ZIP format and native Webstation `saves/UDATA/<title-id>/...` and `saves/TDATA/<title-id>/...` ZIPs. For xemu image files, both trees are restored together in a temporary HDD copy before that image is swapped into place.
- An incoming broker archive containing another title's directory or otherwise unsupported data is **rejected before modifying the xemu disk image**. TDATA-containing archives are still refused for folder-backed Xbox emulators, where a two-tree atomic swap is not implemented.
- This path uses the existing extraction, backups, image-not-running guard and sync conflict-resolution logic. Nothing is written to the Unraid host by this branch.

## Not yet supported

- End-to-end validation of the new `TDATA` HDD read/write path on a disposable xemu image, including rollback and sync hash behavior.
- A verified end-to-end test with the user's broker build and production RomM configuration.
- Verified native build/test workflow result.

## Tests

The Python reference converter has six synthetic unit tests:

```powershell
python -m unittest discover -s tests -p "test_xemu_webstation_archive.py" -v
```

They do not exercise the C synchronization engine. The branch adds GitHub Actions checks for `make steamdeck` and the six reference tests. The upstream `make unit` target cannot run in this fork because its test fixtures are missing.

## Safe manual test plan (after compilation)

1. Back up the Steam Deck's xemu HDD image and copy the save ZIP from RomM.
2. Use a disposable RomM test installation and a test game, not existing progress.
3. Opt in with `ROMM_XEMU_WEBSTATION_ARCHIVES=1` in the RommDeck service's **test** environment only.
4. Launch xemu, save, close it normally, then sync and confirm a `.saves.zip` upload whose entries begin `saves/UDATA/<title-id>/`.
5. Launch in Webstation and confirm the game reads it; save, exit, sync down, then verify the original data persists on the Deck.
6. Verify a Webstation ZIP with `saves/TDATA/` restores only the selected game's TDATA on a disposable HDD copy; confirm UDATA is preserved.
7. Verify another Xbox game and older `<title-id>.zip` remain readable.

This is a draft PR. No change should be merged until the tests and real round trip pass.
