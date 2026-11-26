#!/usr/bin/env bash
set -euo pipefail
DEST="${XDG_DATA_HOME:-$HOME/.local/share}/rommdeck"
BIN="$DEST/romm-sync"
BACKUP="$DEST/xemu-webstation-test-backup/romm-sync.original"
OVERRIDE="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/romm-sync.service.d/99-xemu-webstation-test.conf"
MARKER="# Managed by RommDeck xemu Webstation test installer"
trap 'if [[ -t 0 ]]; then read -r -p "Press Enter to close..." _ || :; fi' EXIT
[[ -f "$BACKUP" ]] || { echo "No original RommDeck backup found at $BACKUP"; exit 1; }
if pgrep -x xemu >/dev/null 2>&1; then
    echo "Close xemu before restoring the service."
    exit 1
fi
read -r -p "Restore original RommDeck sync service and disable test mode? [y/N] " ok
[[ "$ok" == [yY] || "$ok" == [yY][eE][sS] ]] || exit 0
if [[ -e "$OVERRIDE" ]] && ! grep -Fqx "$MARKER" "$OVERRIDE"; then
    echo "Unrecognized systemd override. Refusing to modify it."
    exit 1
fi
systemctl --user stop romm-sync.service
cp -p "$BACKUP" "$BIN.new"
mv -f "$BIN.new" "$BIN"
[[ ! -e "$OVERRIDE" ]] || rm -f "$OVERRIDE"
systemctl --user daemon-reload
systemctl --user start romm-sync.service
systemctl --user is-active --quiet romm-sync.service
echo "Original RommDeck service restored. Pairing and settings preserved."
