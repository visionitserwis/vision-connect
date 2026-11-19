# Vision Connect

Remote desktop for the customers of **Vision IT Serwis** (https://visionitserwis.pl).

Vision Connect is a **modified version of [RustDesk](https://github.com/rustdesk/rustdesk)**
(Copyright © Purslane Tech Pte. Ltd.), modified by Vision IT Serwis (Albert Jabłoński) since 13 November 2026.
It is distributed under the same licence as RustDesk, **AGPL-3.0** (see `LICENCE` in the repository root).
This repository contains the complete corresponding source of every release, including the build scripts.

You may use, copy, modify and redistribute this program under the terms of the AGPL-3.0. Nothing in our
service agreements limits these rights.

## What is changed compared to RustDesk

All changes live in the `vision/` folder and are applied to the RustDesk source at build time:

- `brand.py` – program name, icons, colours, the "About" page, and the built-in address and public key
  of the Vision Connect server (13–14.11.2026);
- `assets/` – Vision Connect icons and logos (© Vision IT Serwis; the name and logo are not covered by the AGPL);
- `patches/10_colors.py` – colours (14.11.2026);
- `patches/20_licencja.py` and `patches/vision_license.rs` – **service subscription key** (16.11.2026, wording 19.11.2026):
  unattended access with a permanent password through the Vision IT Serwis server is part of a paid service
  subscription; the program checks an RSA-signed subscription key (or a 14-day trial). The one-time password always works.
  The key concerns our service (server, installation, support), not the right to use the program;
- `patches/30_bez_konta.py` – hides the account / address book pages, the server has no accounts (18.11.2026);
- `patches/40_polityka.py` – privacy links point to https://visionitserwis.pl/vision-connect-prywatnosc/ (18.11.2026);
- `patches/50_nowa_wersja.py` – release number and a "new release available" notice read from
  https://visionitserwis.pl/vision-connect-wersja/ (nothing is downloaded automatically) (19.11.2026);
- `make_workflow.py` – generates `.github/workflows/vision-connect.yml` (Windows x64 build only)
  from the upstream `flutter-build.yml`.

## How to build

1. Fork or clone this repository (it already contains the RustDesk source and the `vision/` folder).
2. GitHub → Actions → "Vision Connect - Windows" → Run workflow (about 40 minutes).
   The workflow runs `python vision/brand.py` (which applies every `vision/patches/NN_*.py` in order)
   and then the standard RustDesk Windows build.
3. The result is the artifact `VisionConnect-windows-x86_64` (one portable .exe in a ZIP).

To build without GitHub, run `python vision/brand.py` in the repository root and follow the RustDesk
build instructions for Windows (https://rustdesk.com/docs/en/dev/build/windows/).

## Releases

| Release | Date | Commit | SHA-256 of VisionConnect-1.5.3-x86_64.exe |
|---|---|---|---|
| 9 | 2026-11-19 | `4dd0be5` | `9b2c5c46c98a83189597f05066cae7ed8b85680b1cdf2dc06145562ca109f449` |
| 10 | 2026-11-19 | `a22ee97` | `f962fdd0950df68ba8b1de1e364674da6383d1cc85c0374a1388de67395be06f` |

The release number is shown in the program: Settings → About ("Wydanie N").

## Server

The rendezvous / relay server is the unmodified RustDesk Server (hbbs / hbbr 1.1.16, AGPL-3.0,
https://github.com/rustdesk/rustdesk-server), installed from the official packages.

Contact: Vision IT Serwis, tel. +48 600 800 642, visionitserwis@gmail.com
