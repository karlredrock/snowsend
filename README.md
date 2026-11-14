# SnowSend — LocalSend for Mac OS X 10.6 Snow Leopard

A **LocalSend protocol v2** client written in Python 2.6/2.7 using only the
Snow Leopard system standard library, packaged as a native, double-clickable
**`SnowSend.app`**.

**IMPORTANT NOTE: This project used AI assisted coding as I personally couldn't manage to get the protocol working, however keep in mind I reviewed and tested it severely on my computers, as always I strongly suggest you only use this for personal usage in a secure network, if you have any improvements or suggestions I'll gladly review them, if you have any issues with AI projects I suggest you check another thing, however if you just care for something that just works, check it out**

**SnowSend** is an independent project: it implements the LocalSend protocol
from scratch so a Mac running Snow Leopard can exchange files with modern
phones and computers that run the official app. It is not affiliated with,
sponsored by or endorsed by the LocalSend project.

```
┌─────────────────────────────┐     plain HTTP :53317      ┌──────────────────────────────┐
│  Mac Snow Leopard (10.6)    │  ◄───────────────────────►  │  Phone / modern computer     │
│  SnowSend.app               │   multicast UDP 224.0.0.167  │  Official LocalSend app      │
│  /usr/bin/python (2.6/2.7)  │   discovery + file transfer  │  Encryption: OFF             │
│  Tkinter + BaseHTTPServer   │                              │  (see §3, required)          │
└─────────────────────────────┘                              └──────────────────────────────┘
```

> **Why plain HTTP:** Snow Leopard cannot reliably negotiate modern TLS
> 1.2/1.3, nor the self-signed certificate with *fingerprint pinning* that
> LocalSend uses by default (HTTPS). SnowSend therefore speaks **unencrypted
> HTTP on port 53317**. Use it only on your own trusted local network.

**Version:** 1.7 (`2.0.7-10.6`) · **License:** MIT (see §10) ·
**Status:** personal project, built with AI assistance (§9) ·
**Languages:** English, Español, Français, Deutsch, Português (§5)

*Documentación en español: [`README.es.md`](README.es.md).*

---

## 1. What's in this project

| File | Purpose |
|---|---|
| `snowsend.py` | Complete source (Tkinter GUI + HTTP server + multicast discovery + send client + 5-language UI). Works on Python 2.6/2.7 and Python 3. |
| `build_app.sh` | Builds `SnowSend.app` (Info.plist, launcher, icon). |
| `LICENSE` | MIT license. Also copied inside the bundle as `Contents/Resources/LICENSE.txt`. |
| `README.es.md` | Spanish version of this document. |

The package layout is the classic Mac OS X 10.6 one:

```
SnowSend.app/
└── Contents/
    ├── Info.plist          CFBundleExecutable=launcher, LSMinimumSystemVersion=10.6
    ├── PkgInfo             APPL????
    ├── MacOS/
    │   └── launcher        executable /bin/sh script (chmod +x)
    └── Resources/
        ├── snowsend.py
        ├── LICENSE.txt     MIT license
        └── AppIcon.icns    icon (512×512 max)
```

The `launcher` resolves its own path with `dirname "$0"`, redirects
`stdout`/`stderr` to `~/Library/Logs/SnowSend.log` (so double-clicking does
**not** open a Terminal window) and runs:

```sh
exec /usr/bin/python "$RESOURCES_DIR/snowsend.py"
```

No external dependencies: no `pip`, no `requests`, no `flask`, no
`PyInstaller`, no `py2app`. Only `Tkinter`, `socket`, `struct`, `json`,
`threading`, `BaseHTTPServer`, `httplib`, `hashlib`, `uuid`, `mimetypes`,
`os` and `sys`, all of which ship with Snow Leopard.

---

## 2. Getting `SnowSend.app` onto the Snow Leopard Mac

`SnowSend.app` is really a **folder** (a Finder bundle). Some copy methods
flatten it or drop the executable bit on the `launcher`. The safe way is to
carry it as a **ZIP**. Which you can find on the Releases Page.

### Option A — ZIP on a USB drive (recommended)

1. Download `SnowSend.zip` (from the Releases page, or build it yourself with
   `./build_app.sh && zip -qr SnowSend.zip SnowSend.app`).
2. Copy it to the Mac with Snow Leopard.
3. Double-click the ZIP to expand it, then drag `SnowSend.app` to
   `/Applications` (or anywhere you like).
4. If you copied the folder without a ZIP and the app refuses to open, fix the
   permissions once from Terminal:

   ```sh
   chmod +x /Applications/SnowSend.app/Contents/MacOS/launcher
   ```

### Option B — Local network (SMB / FTP / SSH)

The other machine can serve the ZIP (macOS File Sharing, `python -m
SimpleHTTPServer` in the folder, AirDrop from an older Mac, etc.). Always
transfer the **ZIP**, not the bare folder or .app for proper transfer.

### Option C — You are already on the Snow Leopard Mac

```sh
git clone https://github.com/karlredrock/snowsend.git
cd snowsend
chmod +x build_app.sh && ./build_app.sh
```

The first launch may show the usual “downloaded from the Internet” warning;
right-click → **Open** once.

---

## 3. ⚠️ Required on the phone / modern computer or device: turn encryption off

The official LocalSend app encrypts by default (HTTPS with TLS 1.2+ and a
self-signed certificate). **Snow Leopard cannot do that** (or at least for proper function and stability on V1.x we don't support encryption, however we plan on implement it later), so the other device
must talk plain HTTP:

### On the phone (Android / iPhone)

1. Open **LocalSend**.
2. Tap the **gear / Settings** icon.
3. Set **Encryption → OFF**.
4. Close and reopen LocalSend so the setting takes effect.

### On the modern computer (Windows / macOS / Linux)

1. Open LocalSend → **Settings**.
2. Set **Encryption → OFF**.
3. Restart the app.

If you skip this step, transfers will fail and SnowSend's log will tell you
exactly that (`>>> The device does NOT accept plain HTTP on port 53317`).

---

## 4. Daily use

### The window

```
┌──────────────────────────────────────────────────────────────┐
│ SnowSend        LocalSend protocol v2 - Mac OS X 10.6   ● HTTP :53317 │
├──────────────────────────────────────────────────────────────┤
│ Name: [ Mac de Ana            ]  [Apply]                      │
│ Save to: /Users/ana/Downloads                 [Change…]       │
├──────────────────────────────────────────────────────────────┤
│ Devices on this network                                       │
│ ┌──────────────────┬───────────────┬────────────────────────┐ │
│ │ Name             │ Model         │ Address                │ │
│ │ iPhone de Ana    │ iPhone 13     │ http://192.168.1.76:53317 │ │
│ └──────────────────┴───────────────┴────────────────────────┘ │
│ [Announce / Refresh] [Scan network]              [Clear log]   │
├──────────────────────────────────────────────────────────────┤
│ Files to send                    3                                │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ photo.jpg  (2.4 MB)                                      │ │
│ │ report.pdf (310 kB)                                      │ │
│ │ clipboard-20261113-2227.txt (48 kB)                      │ │
│ └──────────────────────────────────────────────────────────┘ │
│ [Add File…] [Paste Clipboard] [Remove] [Clear List]  [Cancel Transfer] [Send to Device] │
├──────────────────────────────────────────────────────────────┤
│ Activity                                                      │
│ [22:27:19] HTTP 192.168.1.76 - "POST /register" 200 -         │
├──────────────────────────────────────────────────────────────┤
│ Language: (English)(Español)(Français)(Deutsch)(Português)    │
├──────────────────────────────────────────────────────────────┤
│ Plain HTTP on port :53317 - turn Encryption OFF…   Ready | 1 device(s) │
└──────────────────────────────────────────────────────────────┘
```

Everything lives inside the window — there is **no menu bar** as it's a Python App:

- **Language buttons** at the bottom, switch the interface language instantly.
- **Double-click a device** in the table to send files to it.
- The Mac's name and the download folder are edited right in the window and
  saved to `~/.snowsend_config.json` when you press *Apply* or pick a folder.

### Receiving files

Nothing to do: the HTTP server listens on **53317** and **accepts incoming
requests automatically** (this lightweight version has no accept/reject
dialog). Every file is written to the download folder and its **SHA-256 is
verified**; if the checksum does not match, the file is discarded and the
error is logged. Name clashes are resolved as `name (1).ext`, `name (2).ext`…

### Sending files

SnowSend works like the official app: **you build a list of files first, and
it stays there until you remove it.**

1. Press **Add File…** (you can select several at once) or **Paste
   Clipboard**. Every file is added to **Files to send**; nothing is sent yet.
2. Repeat as many times as you want, either to send everything to one device
   later or to send the same batch to several devices one after another.
3. Select the target device in the table and press **Send to Device**.
4. Accept the prompt on the other device within 60 seconds (see the Activity
   pane).
5. Changed your mind mid-transfer? **Cancel Transfer** aborts it: SnowSend
   stops sending, closes the connection (the receiver discards the incomplete
   file) and sends `POST /api/localsend/v2/cancel` so the session is cleaned
   up on the other side.
6. The list is **not** cleared after sending — send it to another device, or
   use **Remove** (multiple selection works) / **Clear List** when you are done.

Notes:

- **Paste Clipboard** takes the text on the clipboard and adds it as
  `clipboard-YYYYMMDD-HHMMSS.txt` (UTF-8) in your temporary folder, exactly
  like the text feature of the official app. Images are not supported yet.
- Files are read from disk in 256 KB chunks, so cancelling works even in the
  middle of a large file, and huge files are not loaded into memory.
- The queue lives only while the app is open; it is not saved to disk.

### Small screens (11" MacBook Air, 1366 × 768, or lower)

The window **sizes itself to your screen** instead of assuming a big display.
On start-up SnowSend measures the screen, and if the natural size does not fit
it first shrinks the activity log, then the device table, then the file list —
the **language buttons and the status line are packed against the bottom edge**
(Tk `side=bottom`) *before* anything else, so they are always visible and are
never the part that gets cut. The window is also centred horizontally and kept
inside the usable area (menu bar and title bar taken into account), and it is
re-fitted whenever you switch language, because labels change width.

Measured defaults: 1366 × 768 screen → about **700 × 658** window; a 1024 × 600
screen → **700 × 490** with a 3-line log. Nothing is hidden and nothing needs a
scroll area.

### Quitting

Close the window (or ⌘Q). If the app fails to start, check:

```
~/Library/Logs/SnowSend.log
```

---

## 5. Languages

The whole interface — window, menus, buttons, dialogs, status bar **and every
log message** — is translated into five languages:

| Code | Language | Notes |
|---|---|---|
| `en` | English | default fallback |
| `es` | Español | |
| `fr` | Français | |
| `de` | Deutsch | |
| `pt` | Português | |

- On first launch SnowSend reads the system language (`AppleLocale`,
  `LANG`, `LC_ALL`) and picks a match; anything unsupported falls back to
  English.
- Change it on the fly with the **five buttons at the bottom of the window**
  (`English | Español | Français | Deutsch | Português`). The whole interface
  — window texts, table headers, status bar and every new log line — switches
  immediately, and the choice is remembered in `~/.snowsend_config.json`.
- From the command line: `python snowsend.py --lang de`.

Translations live in a single `STRINGS` dictionary at the top of
`snowsend.py`, with one entry per key. Adding a language is a matter of
copying a column and translating it — a test (`tests/test_i18n.py`) fails the
build if a key is missing in any language or if a translation loses its `%s`
placeholders.

---

## 6. Implemented protocol (LocalSend v2)

Reference: <https://github.com/localsend/protocol> (v2.2)

| Element | Implementation |
|---|---|
| Multicast discovery | UDP `224.0.0.167:53317`, announcement JSON with `alias`, `version`, `deviceModel`, `deviceType`, `fingerprint`, `port`, `protocol`, `download`, `announce` |
| `POST /api/localsend/v2/register` | Sends our info; over HTTP first (Snow Leopard cannot do TLS), then the announced protocol |
| `POST /api/localsend/v2/prepare-upload` | Receives `{info, files:{id:{fileName,size,fileType,sha256}}}` → replies `{sessionId, files:{id:token}}` |
| `POST /api/localsend/v2/upload` | Raw binary body; verifies size and SHA-256, replies `200` or `422` |
| `POST /api/localsend/v2/cancel` | Cancels a session |
| `GET /api/localsend/v2/info` | Returns this device's info |
| HTTP fallback discovery | `scan_subnet()` probes every address of the local `/24` |

Robustness details that matter in the real world:

- **`Transfer-Encoding: chunked`** request bodies are decoded chunk by chunk
  (that is how iOS sends them), streamed to disk with SHA-256 computed on the
  fly.
- **`Expect: 100-continue`** is answered explicitly (`HTTP/1.1` + `100
  Continue`), otherwise some clients deadlock.
- **`gzip`/`deflate` responses**, responses with no `Content-Length` and
  connection-closed bodies are all handled when sending.
- **macOS/BSD multicast quirk:** the socket binds to `INADDR_ANY` and sets
  `IP_MULTICAST_IF` to the real local IP; binding to the multicast address
  fails with `[Errno 49]` on macOS.

---

## 7. Troubleshooting

| Symptom | What to check |
|---|---|
| The Snow Leopard Mac doesn't appear on the phone | Encryption OFF on the phone (§3)? Same Wi-Fi? Port 53317 free? Press *Announce / Refresh* and *Scan network*. |
| The phone doesn't appear on the Snow Leopard Mac | Encryption OFF? Some routers/APs block multicast: use **Scan network**. |
| “Error in prepare-upload” when sending | The destination is probably still on HTTPS. Turn Encryption off there and retry; check both logs. |
| Log says “The device does NOT accept plain HTTP on port 53317” | Encryption is **ON** on the phone: its server only speaks HTTPS and Snow Leopard cannot do modern TLS. Turn it off (§3), restart LocalSend there, press *Announce / Refresh*. |
| Stuck on “Waiting for acceptance on …” | You must tap **Accept** on the other device within 60 s. If no prompt appears, encryption is on or the devices are on different networks. |
| “Response is not JSON (status …)” with a raw body | That is the exact body the other device returned; include it in a bug report. It should not happen with encryption off. |
| App won't open on double-click | Check `~/Library/Logs/SnowSend.log`. If you copied the folder without a ZIP, re-apply `chmod +x …/Contents/MacOS/launcher` (§2). |
| Port 53317 already in use | Quit other LocalSend copies, or use `--port` in headless mode (§8). |
| Firewall | On the modern Mac allow LocalSend through the firewall; on Snow Leopard, *System Preferences → Security → Firewall* must allow incoming connections for `python`. |
| Files arrive but checksum is wrong | Shouldn't happen (SHA-256 is verified). Check the log; the corrupt file is deleted. |

---

## 8. For developers / testing

Check the syntax (valid on Python 2.7 **and** Python 3):

```sh
python3 -m py_compile snowsend.py          # modern Mac
/usr/bin/python -m py_compile snowsend.py  # Snow Leopard
```

Headless mode (no GUI — handy for testing or for an old Mac without a screen):

```sh
python snowsend.py --headless --alias MyMac --port 53317 \
       --download-dir ~/Downloads --lang en
```

Rebuild the bundle (optionally with your own icon: drop an `icon.png` up to
512×512 next to `build_app.sh` before building; on a Mac it is converted with
`sips`/`iconutil`, otherwise a placeholder icon is generated so the build
never fails):

```sh
chmod +x build_app.sh
./build_app.sh
```

Before publishing a version, check the bundle is complete: `Info.plist` with
`CFBundleName=SnowSend`, an executable `Contents/MacOS/launcher`, and
`Contents/Resources/` containing `snowsend.py`, `LICENSE.txt` and
`AppIcon.icns`.

Automated tests live in `tests/` and run on any machine with Python 3 (no Mac
and no phone needed):

```sh
python3 tests/test_server_regression.py     # /info, /register, chunked,
                                            # Content-Length, 100-continue,
                                            # 422 on bad SHA, multicast
python3 tests/test_send_fake_iphone.py      # send to a fake iPhone (normal)
MODE=chunked python3 tests/test_send_fake_iphone.py   # chunked/gzip/close replies
python3 tests/test_register_and_diagnose.py # HTTP-first register + diagnosis
python3 tests/test_i18n.py                  # translation completeness (5 langs)
python3 tests/test_gui_stub.py              # GUI, file queue and clipboard in
                                            # all 5 languages (fake Tk, no display)
python3 tests/test_cancel.py                # cancelling a transfer mid-file and
                                            # between files, /cancel request
```

---

## 9. Security

- This client speaks **unencrypted HTTP** out of necessity for 10.6. Use it
  **only on your own trusted LAN**.
- It accepts files automatically: check your download folder periodically and
  never run it on a network you don't trust.
- SHA-256 is verified on receipt, but without TLS there is no sender
  authentication: any machine on your network could send you a file. This is
  the same trust model the official LocalSend uses with encryption off.
- No telemetry, no external servers: only UDP 53317 (discovery) and TCP 53317
  (HTTP) on your local network.

---

## 10. Project built with AI assistance

This project was developed **in collaboration with an AI assistant**
(Arena.ai agent), in an iterative loop of writing, testing and fixing: the
code, the packaging and this documentation were produced and reviewed with
that help, starting from the author's instructions, tests on real hardware (a
Snow Leopard Mac and an iPhone) and the author's corrections.

What that means in practice:

- **Review the code before trusting it.** It has been tested (real receive and
  send, regression tests in the repository), but no software is bug-free and
  this one has had no formal security audit.
- **It is provided “as is”, without warranty** (see the license, §11).
- **It does not replace the official app.** SnowSend exists because the
  official app no longer runs on Snow Leopard; it is not meant as a
  replacement on modern systems.
- Design decisions, the license choice and responsibility for what is
  published belong to the project author.

---

## 11. License and legal notes

### License: MIT

This project is released under the **MIT license** ([`LICENSE`](LICENSE), also
bundled as `SnowSend.app/Contents/Resources/LICENSE.txt`).

MIT lets anyone use, copy, modify, merge, publish, distribute, sublicense and
sell the software, with two conditions:

1. Keep the copyright notice and the license in copies or substantial
   portions of the software.
2. No warranty: the software is provided “AS IS”.

**Why MIT and not something else:**

| License | When it fits | SnowSend |
|---|---|---|
| **MIT** (chosen) | You want anyone to use, modify and redistribute with minimal friction, including in closed-source or commercial products. | Best fit: a utility port for old hardware, with no interest in forcing derivatives open. |
| Apache-2.0 | Like MIT but with an explicit **patent grant** and a trademark clause; it is what the official LocalSend app uses. | Valid alternative if patents or ecosystem alignment matter. Changing it is one file. |
| GPL-3.0 | You want every modified version to stay free and open. | **Not recommended here**: it blocks mixing with incompatible licenses and adds source-distribution obligations for anyone shipping the `.app`. |

### Legal points reviewed

1. **No LocalSend code was copied.** All of `snowsend.py` is original code
   written for this project; no Dart code from LocalSend or any third party was
   translated or ported. Therefore it does **not** inherit the official app's
   Apache-2.0 license and can be licensed freely (MIT).
2. **The protocol repository (`localsend/protocol`) declares no license** (no
   `LICENSE` file; GitHub reports “no license”). Its text is therefore **not
   reproduced** here: it is used only as a functional reference for
   interoperability, and endpoints, JSON fields and ports were rewritten in
   our own words. Interoperability itself (speaking the same protocol on the
   network) is not restricted by copyright.
3. **The official app is Apache-2.0.** Its code was not reused, so there are
   no `NOTICE` or attribution obligations; it is still credited in §12 out of
   courtesy and honesty.
4. **GPL-3.0 projects** (e.g. `theanazerka/unlocalsend`): only **public
   behavioural observations** were consulted (that iOS sends bodies
   `chunked`), never their code. Copying GPL-3.0 code would have forced
   SnowSend to be GPL-3.0; **that was not done**.
5. **Trademarks.** “LocalSend”, its logo and the project name belong to their
   authors. That is why this app is called **SnowSend**: it avoids any
   confusion or misuse of the mark. Mentions such as “LocalSend-compatible”
   are descriptive/nominative use (stating what it is compatible with), not a
   claim to the mark. **SnowSend is not affiliated with or endorsed by
   LocalSend.**
6. **Apple.** macOS, Mac OS X, Snow Leopard, Aqua, Finder and `iconutil` are
   trademarks of Apple Inc. SnowSend is not affiliated with Apple.
7. **Python and Tk.** The bundle **does not redistribute** Python: it uses the
   `/usr/bin/python` that ships with the system. Python is Python Software
   Foundation software (PSF license) and Tk/Tcl has its own permissive
   license; since no binaries are included in the ZIP, no redistribution
   obligations are added.
8. **Bundle contents** include the copyright notice and license
   (`Contents/Resources/LICENSE.txt`), which is what MIT requires when you
   distribute the binary.
9. **No telemetry, no external network.** SnowSend sends no data to any server
   and collects no user information. Note that plain HTTP transports files
   **unencrypted** over your local network (§9).
10. **Disclaimer.** A utility, without warranty, intended for trusted local
    networks and personal use. If you redistribute it, keep `LICENSE` and the
    copyright notice.

> **To change the copyright holder**, edit the line
> `Copyright (c) 2026 SnowSend contributors` in `LICENSE` (and in
> `Contents/Resources/LICENSE.txt` after rebuilding with `./build_app.sh`).
> To switch to Apache-2.0, replace `LICENSE` with the official Apache License
> 2.0 text and add a `NOTICE` file.

---

## 12. Acknowledgements

Without these projects, SnowSend would not exist. Thanks to:

- **[LocalSend](https://github.com/localsend/localsend)** (Tien Nam Do and
  contributors, Apache-2.0) — the open-source app that inspired all of this
  and that SnowSend is compatible with.
- **[LocalSend Protocol v2.2](https://github.com/localsend/protocol)**
  (LocalSend organisation) — the specification for multicast discovery,
  `register`, `prepare-upload`, `upload`, `cancel` and `info` that was
  implemented here. Functional reference, no text copied.
- **[hermes-localsend](https://github.com/tylerbrevard/hermes-localsend)**
  (tylerbrevard, MIT) — a stdlib-only Python implementation of protocol v2.2;
  its public notes about iOS using `Transfer-Encoding: chunked` were key to
  fixing file reception from the iPhone.
- **[unlocalsend](https://github.com/theanazerka/unlocalsend)** (theanazerka,
  GPL-3.0) — a LocalSend client for old iOS, useful for understanding
  behaviour on the iOS side. Only behavioural ideas were taken; **no code was
  copied**.
- **The Python project** and its standard library (`Tkinter`,
  `BaseHTTPServer`, `httplib`, `socket`, `json`, `hashlib`, `threading`),
  maintained by the Python Software Foundation and the community.
- **Tcl/Tk** — the toolkit behind the interface, included in Mac OS X.
- **Apple** — for Mac OS X 10.6 Snow Leopard and its preinstalled Python
  interpreter, which keep these Macs useful.
- **The project author**, for testing on real hardware, reporting exact
  failures (multicast `Errno 49`, `422` checksum, `prepare-upload` returning
  non-JSON) and validating every version.
- **Arena.ai's AI assistant** — for writing, debugging and documenting
  alongside the author; see §10.

---

## 13. Changelog

### v1.7 (2.0.7-10.6) — Window fits 11" screens

1. **The bottom bar (language buttons + status text) no longer disappears on
   small screens.** The window was a fixed 800 × 740; an 11" MacBook Air is
   1366 × 768, so after the menu bar and the title bar there is only ~658 px and
   the footer was off-screen. The footer is now packed with `side=bottom`
   **first**, so Tk reserves its space and any shortage is taken from the
   activity log instead.
2. **`fit_to_screen()`**: on start-up (and after every language change) the
   window measures `winfo_screenwidth/height`, and if the natural size does not
   fit it shrinks the log, then the device table, then the file list — down to a
   floor of 3 lines each — before capping the window to the usable area. It is
   centred horizontally and never larger than the screen; `minsize` is derived
   from the same numbers, so the window can never be forced off-screen.
3. **Compact layout**: window 800 × 740 → ~700 × 658, container padding
   14/12 → 12/10, device table 7 → 5 rows, log 8 → 5 lines, file list 5 → 4
   rows. Same information, ~90 px less height.
4. **The long "turn Encryption OFF" sentence no longer duplicates and overflow
   the footer**: it now has a single short version (`HTTP :53317 - Encryption
   OFF on the other device`) with a `wraplength` that follows the window width.
5. **New checks** in `tests/test_gui_stub.py` (78 total now): the fake Tk models
   `winfo_screenwidth/height`, `winfo_reqheight`, `geometry` and `minsize`, so
   the tests assert that the window fits 1366 × 768 **and** 1024 × 600, that the
   footer is packed bottom-first, that the log shrinks to 3 lines and no further,
   and that the short footer text exists in all 5 languages.
6. Version 1.7 (`2.0.7-10.6`).

### v1.6 (2.0.6-10.6) — File queue, clipboard paste and cancel

1. **The `\u2026` garbage on some buttons is fixed.** Those labels were written
   as plain (byte) string literals with `\uXXXX` escapes; **Python 2 does not
   decode those escapes in byte strings**, so on Snow Leopard buttons literally
   showed `\u2026`. Every entry of the translation catalog is now a `u"…"`
   unicode literal (478 of them), so accents and ellipses render properly on
   Python 2.6/2.7.
2. **Files are queued instead of being sent immediately**, like the real
   LocalSend: *Add File…* (multi-selection) and *Paste Clipboard* fill the
   **Files to send** list, which is **not** cleared after a transfer, so the
   same batch can be sent to another device or repeated after a failure.
   *Remove* (multi-selection) and *Clear List* are the only things that empty
   it.
3. **Cancel an ongoing transfer**: the new *Cancel Transfer* button stops the
   upload, closes the socket (the receiver drops the incomplete file) and sends
   `POST /api/localsend/v2/cancel` to clean up the session.
4. **Uploads are streamed in 256 KB chunks** (`http_post_file`) instead of
   reading the whole file into memory: large files are no longer a memory
   problem, and cancellation can interrupt a transfer mid-file.
5. **Paste Clipboard** sends the clipboard text as a
   `clipboard-YYYYMMDD-HHMMSS.txt` file, like the official app's text feature.
6. **New tests:** `tests/test_cancel.py` (10 checks: cancel before starting,
   cancel mid-file, cancel between files, `/cancel` request, normal transfer
   completes) and `tests/test_gui_stub.py` grew to 61 checks (file queue,
   duplicated files, remove/clear, clipboard paste with UTF-8 content, empty
   clipboard warning).
7. Version 1.6 (`2.0.6-10.6`).

### v1.5 (2.0.5-10.6) — Language switching fixed, menu bar removed

1. **The menu bar is gone.** On Snow Leopard's Tk 8.5/Aqua the global menu bar
   could not be re-labelled safely: re-labelling entries by index shifted them
   (Tk adds its own application menu) and produced **duplicated menus and a
   garbled entry**. Everything is back inside the window, as before.
2. **Language switching now actually works**, with a visible control instead of
   a menu: five radio-style buttons at the bottom of the window. Pressing one
   calls `change_language()` directly, which retranslates every widget, the
   table headers, the status bar and the footer, logs the change, updates the
   device list without losing it and saves the choice to
   `~/.snowsend_config.json`.
3. **The Preferences and About dialogs were removed** (their controls — name,
   language, download folder — are all in the main window), which removes the
   last places where a stale translation could hide.
4. **16 dead translation keys removed** from the catalog (menu and dialog
   entries that no longer exist); the language catalog is now 97 keys × 5
   languages and stays fully verified by `tests/test_i18n.py`.
5. **`tests/test_gui_stub.py` grew to 47 checks**: it now presses each of the
   five language buttons and asserts that the button texts, the table headers,
   the status bar and the saved configuration really change — the exact
   regression that was reported.
6. Version 1.5 (`2.0.5-10.6`).

### v1.4 (2.0.4-10.6) — Five languages, Mac-style interface, English docs

1. **The interface speaks five languages**: English, Spanish, French, German
   and Portuguese. Not just the window: menus, buttons, dialogs, status bar
   and **every log message** go through a single `STRINGS` catalog and the
   `T()` function. The language is detected from the system on first launch,
   can be changed at runtime from the **Language** menu or
   **Preferences → Language**, is remembered in `~/.snowsend_config.json`, and
   can be forced with `--lang en|es|fr|de|pt`.
2. **Redesigned as a proper Mac OS X app**: global menu bar (About,
   Preferences… ⌘,, Quit, Device, Window, Language), a header with the app
   name and server status, a **device table** (name / model / address)
   instead of a plain list, a monospaced activity pane with colour for errors
   and hints, and a status bar with ready state, device count and language.
   Double-click a device to send. It uses `ttk` (native Aqua theme) when
   available and falls back to classic Tk widgets otherwise.
3. **Preferences window** to change the Mac's name, the language and the
   download folder, all persisted between launches.
4. **README rewritten in English** as the main document; the Spanish version
   is kept as `README.es.md`.
5. **New tests:** `tests/test_i18n.py` (17 checks: completeness of the five
   languages, `%s` placeholder parity, `T()`, system-language detection,
   config persistence) and `tests/test_gui_stub.py` (35 checks: the window is
   built in all five languages without a display, device table, warnings,
   Preferences/About, quitting).
6. Version 1.4 (`2.0.4-10.6`) in `Info.plist`, `VERSION` and `APP_VERSION`.

### v1.3 (2.0.3-10.6) — Renamed to SnowSend, license and credits

1. The app is now **`SnowSend.app`** (was `LocalSend.app`): bundle name,
   window title, `CFBundleName`/`CFBundleIdentifier` (`org.snowsend.SnowSend`)
   and source file (`snowsend.py`).
2. New log at **`~/Library/Logs/SnowSend.log`**.
3. **Fingerprint preserved**: stored in `~/.snowsend_fingerprint`, migrated
   automatically from the old `~/.localsend_10_6_fingerprint` so the Mac stays
   the same device in the phone's list.
4. **MIT license** (`LICENSE`, also inside the bundle) plus §10 with the
   legal analysis.
5. §9 declares the project as AI-assisted and §12 credits LocalSend, the
   protocol, hermes-localsend, unlocalsend, Python, Tcl/Tk and Apple.

### v1.2 (2.0.2-10.6) — Mac → iPhone sending (prepare-upload)

**Symptom:** sending from the Mac logged `Preparando envio a …
(https://192.168.1.76:53317)`, then `…SSL23_GET_SERVER_HELLO:unknown
protocol…, reintentando con http plano…` and ended with
`Error en prepare-upload: No JSON object could be decoded`.

1. **No TLS attempt first.** Sending always starts with **plain HTTP**
   (`http://IP:53317`); the announced protocol is only a fallback.
2. **HTTP client rewritten on top of `httplib`/`http.client`.** Python 2.6's
   `urllib2` could not interpret `chunked`, `gzip`, empty or
   connection-closed bodies. Status, headers and the raw body are read, and
   JSON is extracted with several strategies (gzip/deflate, manual chunked
   decoding, UTF-8 BOM, first `{...}` object); if everything fails, the log
   shows the raw body and headers.
3. **60 s wait** for the acceptance prompt on the phone (was 15 s).
4. **Automatic diagnosis of the peer**: if sending fails, `GET /info` over
   plain HTTP tells you whether the device accepts plain HTTP at all (i.e.
   whether encryption is still on).
5. **Register over HTTP first**, so the Mac shows up on the phone without TLS
   errors.
6. Binary bytes in error messages are escaped (`\x15\x03…`) and never break
   the interface.

### v1.1 (2.0.1-10.6) — iPhone reception + macOS fixes found in real use

1. **Reception from iPhone failed with `422 checksum SHA256 mismatch`** (4-byte
   file: `prepare-upload` 200 but `upload` 422). Cause: iOS LocalSend sends
   both bodies with `Transfer-Encoding: chunked` and **no** `Content-Length`,
   and the receiver only read `Content-Length`. Fix: full chunked decoding
   (hex sizes, trailers, streaming to disk with live SHA-256) plus explicit
   `Expect: 100-continue` handling.
2. **`[Errno 49] Can't assign requested address` on multicast announce**
   (empty device list on the Mac). Cause: on macOS/BSD binding the UDP socket
   to `224.0.0.167` or `127.0.0.1` makes `sendto()` fail. Fix: bind to
   `INADDR_ANY`, set `IP_MULTICAST_IF` to the real local IP, join the group
   with `(224.0.0.167, local IP)`, and retry with a temporary socket if needed.
3. **`SSL routines:SSL23_GET_SERVER_HELLO:unknown protocol` when registering**
   with the iPhone (it announces `protocol:https` even with encryption off).
   Fix: fallback loop `http` → announced protocol → `https`, updating the
   stored protocol of the device.

### v1.0 (2.0-10.6) — First working version

Protocol v2 client and server, Tkinter GUI, multicast discovery, subnet
scanning, `SnowSend.app` bundle and build script.

---

*SnowSend is an independent, unofficial project, not related to LocalSend,
Apple Inc. or the authors of the credited projects. “LocalSend” is a name of
the LocalSend project; “macOS”, “Mac OS X” and “Snow Leopard” are trademarks of
Apple Inc.*
