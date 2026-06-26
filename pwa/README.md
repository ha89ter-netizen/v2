# AutoBot PWA Launcher

Static launcher for the Telegram bot:

- deep link: `tg://resolve?domain=AutoSupportingBot`
- fallback link: `https://t.me/AutoSupportingBot`

## Local test

Open `pwa/index.html` in a browser or serve the repository with any static server.

## GitHub Pages

Publish the `pwa/` folder with GitHub Pages. Then open the page on iPhone/Android
and add it to the home screen.

On tap, the launcher tries to open Telegram directly. If the OS blocks the deep
link, the user can tap the fallback button.

Public launcher:

https://ha89ter-netizen.github.io/v2/pwa/

User installation guide:

- iPhone: Safari -> Share -> Add to Home Screen.
- Android: Chrome -> menu -> Install app or Add to Home screen.

Full user-facing instructions are in `pwa/INSTALL.md`.
