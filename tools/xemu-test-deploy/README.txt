RommDeck experimental Xbox / Webstation Steam Deck installer

1. On your Steam Deck in Desktop Mode, extract the downloaded GitHub
   Actions ZIP into a folder.
2. Right-click "Install-RommDeck-Test.desktop" and select "Run" /
   "Execute" (approve the launch if KDE asks). It opens a terminal
   and asks for confirmation. Close xemu and RommDeck first.
3. Test only with a disposable Xbox save. Existing saves may sync as
   soon as the service starts.
4. To revert, execute "Restore-Original-RommDeck.desktop" the same way.

If KDE won't launch a desktop shortcut, open Konsole in the extracted
folder and run:
    bash ./Install-RommDeck-Test.sh

To restore:
    bash ./Restore-Original-RommDeck.sh

The installer backs up the existing RommDeck sync binary once, under
~/.local/share/rommdeck/xemu-webstation-test-backup, and adds only a
systemd user-service environment override. It does NOT back up your
xemu HDD image or guarantee live Webstation interoperability.
Your xemu HDD images on Steam Deck and Unraid should be backed up
separately before the first test.

Do not run the normal RommDeck AppImage during the test: its own
service installation/update may replace this experimental binary.
