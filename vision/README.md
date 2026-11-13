# Vision Connect

Remote desktop for the customers of **Vision IT Serwis** (https://visionitserwis.pl).

Vision Connect is built from the source code of [RustDesk](https://github.com/rustdesk/rustdesk)
(Copyright © Purslane Tech Pte. Ltd.) and is distributed under the same licence, **AGPL-3.0**
(see `LICENCE` in the repository root). This repository contains the complete corresponding source.

What is changed compared to RustDesk (everything is in this `vision/` folder and is applied at build time):

- `brand.py` – program name, icons, colours, the "About" page, and the built-in address and public key
  of the Vision Connect server;
- `assets/` – Vision Connect icons and logos (© Vision IT Serwis);
- `make_workflow.py` – generates `.github/workflows/vision-connect.yml` (Windows x64 build only)
  from the upstream `flutter-build.yml`.

Build: GitHub → Actions → "Vision Connect - Windows" → Run workflow.
