# Experimental Xbox xemu ↔ Webstation save sync

**Development branch, not a release. Do not enable on a live Steam Deck until the native build and end-to-end restore have been verified with backup saves.**

## Implemented

- RommDeck's C synchronization engine has an explicit opt-in: `ROMM_XEMU_WEBSTATION_ARCHIVES=1`.
- For **xemu** / `xbox` profiles only, new uploads use the `<title-id>.saves.zip` filename and the broker's **`saves/UDATA/<title-id>/...`** ZIP members.
- The existing RommDeck format remains the default for uploads when the variable is unset.
- The downloader supports both RommDeck's legacy title-ID-rooted ZIP format and native Webstation `saves/UDATA/<title-id>/...` ZIPs.
- An incoming broker archive containing `TDATA`, another title's directory, or otherwise unsupported data is **rejected before modifying the xemu disk image**. It is not silently truncated.
- This path uses the existing extraction, backups, image-not-running guard and sync conflict-resolution logic. Nothing is written to the Unraid host by this branch.

## Not yet supported

- Native Webstation exports containing Xbox `TDATA`. RommDeck's current xemu extractor uses `UDATA`; further Xbox HDD work is required to synchronize `TDATA` safely.
- A verified end-to-end test with the user's broker build and production RomM configuration.
- Verified native build/test workflow result.

## Tests

The Python reference converter has five synthetic unit tests:

```powershell
python -m unittest discover -s tests -p "test_xemu_webstation_archive.py" -v
```

They do not exercise the C synchronization engine. The branch adds a GitHub Actions workflow that attempts `make host`, `make unit`, and those reference tests; verify that it has completed successfully before deploying.

## Safe manual test plan (after compilation)

1. Back up the Steam Deck's xemu HDD image and copy the save ZIP from RomM.
2. Use a disposable RomM test installation and a test game, not existing progress.
3. Opt in with `ROMM_XEMU_WEBSTATION_ARCHIVES=1` in the RommDeck service's **test** environment only.
4. Launch xemu, save, close it normally, then sync and confirm a `.saves.zip` upload whose entries begin `saves/UDATA/<title-id>/`.
5. Launch in Webstation and confirm the game reads it; save, exit, sync down, then verify the original data persists on the Deck.
6. Verify a Webstation ZIP with `saves/TDATA/` is safely refused without altering the Xbox HDD.
7. Verify another Xbox game and older `<title-id>.zip` remain readable.

This is a draft PR. No change should be merged until the tests and real round trip pass.
