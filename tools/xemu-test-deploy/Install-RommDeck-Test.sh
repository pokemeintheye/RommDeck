#!/usr/bin/env bash
# Experimental RommDeck xemu/Webstation test installer. Run as Deck user.
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEST="${XDG_DATA_HOME:-$HOME/.local/share}/rommdeck"
BIN="$DEST/romm-sync"
SOURCE="$HERE/romm-sync"
BACKUP="$DEST/xemu-webstation-test-backup"
DROPIN="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/romm-sync.service.d"
OVERRIDE="$DROPIN/99-xemu-webstation-test.conf"
MARKER="# Managed by RommDeck xemu Webstation test installer"
UNIT="romm-sync.service"
msg() { printf '%s\n' "$*"; }
fail() { msg "ERROR: $*" >&2; exit 1; }
pause() { if [[ -t 0 ]]; then read -r -p "Press Enter to close..." _ || :; fi; }
trap pause EXIT
[[ "$(uname -m)" == "x86_64" ]] || fail "This binary requires an x86_64 Steam Deck."
command -v systemctl >/dev/null || fail "systemctl is required."
command -v sha256sum >/dev/null || fail "sha256sum is required."
[[ -f "$SOURCE" ]] || fail "The test romm-sync executable must be beside this installer."
[[ -f "$BIN" ]] || fail "RommDeck service is not installed at $BIN."
[[ -f "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/$UNIT" ]] ||
    fail "RommDeck user service is missing. Install regular RommDeck first."
[[ ! -e "$OVERRIDE" ]] || grep -Fqx "$MARKER" "$OVERRIDE" ||
    fail "An unrelated override exists at $OVERRIDE; not overwriting it."
if pgrep -x xemu >/dev/null 2>&1; then
    fail "xemu is running. Close it completely before deploying."
fi
if [[ -f "$HERE/romm-sync.sha256" ]]; then
    (cd "$HERE" && sha256sum -c romm-sync.sha256) || fail "Binary checksum verification failed."
fi
msg "RommDeck xemu/Webstation EXPERIMENTAL test installer"
msg "This replaces ONLY the RommDeck background sync binary, not the GUI."
msg "Existing games may synchronize as soon as the service restarts."
msg "Your Xbox disk image backups must already exist and be stored safely."
msg "The original binary will be kept in: $BACKUP"
read -r -p "Install experimental service and enable xemu broker sync? [y/N] " ok
[[ "$ok" == [yY] || "$ok" == [yY][eE][sS] ]] || { msg "Cancelled."; exit 0; }
mkdir -p "$BACKUP" "$DROPIN"
if [[ ! -f "$BACKUP/romm-sync.original" ]]; then
    cp -p "$BIN" "$BACKUP/romm-sync.original"
fi
if [[ -f "$OVERRIDE" ]]; then
    grep -Fqx "$MARKER" "$OVERRIDE" ||
        fail "The existing override has changed; refusing to overwrite it."
fi
was_active=0
systemctl --user is-active --quiet "$UNIT" && was_active=1 || :
restore_on_failure() {
    msg "Deployment failed; restoring original RommDeck binary and settings..."
    systemctl --user stop "$UNIT" || :
    cp -p "$BACKUP/romm-sync.original" "$BIN" || :
    if [[ -f "$OVERRIDE" ]] && grep -Fqx "$MARKER" "$OVERRIDE"; then
        rm -f "$OVERRIDE"
    fi
    systemctl --user daemon-reload || :
    if ((was_active)); then systemctl --user start "$UNIT" || :; fi
}
trap restore_on_failure ERR
systemctl --user stop "$UNIT"
install -m 755 "$SOURCE" "$BIN.new"
mv -f "$BIN.new" "$BIN"
printf '%s\n[Service]\nEnvironment=ROMM_XEMU_WEBSTATION_ARCHIVES=1\n' "$MARKER" > "$OVERRIDE"
systemctl --user daemon-reload
systemctl --user start "$UNIT"
systemctl --user is-active --quiet "$UNIT"
trap - ERR
msg ""
msg "SUCCESS: experimental RommDeck sync service is active."
msg "Leave xemu closed until ready to perform the disposable-save test."
msg "Use Restore-Original-RommDeck.sh from this folder to roll back."
