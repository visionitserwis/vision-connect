#!/usr/bin/env python3
# Vision Connect - branding applied on top of the unmodified RustDesk sources at build time.
# Vision IT Serwis (https://visionitserwis.pl). Based on RustDesk, AGPL-3.0.
# Usage (from the repository root, after checkout with submodules):  python3 vision/brand.py
# Every replacement is asserted: if upstream code changes, the build stops here instead of
# silently producing a half-branded program.
import io, os, re, shutil, sys

APP_NAME = "VisionConnect"            # no spaces: used as Windows service name and exe name
DISPLAY = "Vision Connect"
COMPANY = "Vision IT Serwis"
SERVER = "albertinowroclaw.synology.me"
PUBKEY = "bPf6spCnFkOsPpJMfkktowSfBErAzCDECewL6YTjpmw="   # public key of the Vision Connect server
WEBSITE = "https://visionitserwis.pl"
SOURCE = "https://github.com/visionitserwis/vision-connect"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "vision")


def edit(path, pairs, regex=False):
    p = os.path.join(ROOT, path)
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        s = f.read()
    for old, new in pairs:
        if regex:
            s2, n = re.subn(old, new, s)
        else:
            n = s.count(old)
            s2 = s.replace(old, new)
        if n < 1:
            sys.exit("brand.py: pattern not found in %s: %r" % (path, old))
        s = s2
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)
    print("patched", path)


def copy(src, dst):
    shutil.copyfile(os.path.join(V, "assets", src), os.path.join(ROOT, dst))
    print("copied ", dst)


# 1. name, server, key
edit("libs/hbb_common/src/config.rs", [
    ('APP_NAME: RwLock<String> = RwLock::new("RustDesk".to_owned());',
     'APP_NAME: RwLock<String> = RwLock::new("%s".to_owned());' % APP_NAME),
    ('pub const RENDEZVOUS_SERVERS: &[&str] = &["rs-ny.rustdesk.com"];',
     'pub const RENDEZVOUS_SERVERS: &[&str] = &["%s"];' % SERVER),
])
edit("libs/hbb_common/src/config.rs", [
    (r'pub const RS_PUB_KEY: &str = "[^"]*";', 'pub const RS_PUB_KEY: &str = "%s";' % PUBKEY),
], regex=True)

# 2. Windows version information (file properties)
LEGAL = "(c) %s. Based on RustDesk (c) Purslane Tech Pte. Ltd., AGPL-3.0" % COMPANY
for toml in ("Cargo.toml", "libs/portable/Cargo.toml"):
    edit(toml, [
        (r'LegalCopyright = "[^"]*"', 'LegalCopyright = "%s"' % LEGAL),
        (r'ProductName = "RustDesk"', 'ProductName = "%s"' % DISPLAY),
        (r'FileDescription = "RustDesk Remote Desktop"', 'FileDescription = "%s"' % DISPLAY),
    ], regex=True)
edit("flutter/windows/runner/Runner.rc", [
    (r'VALUE "CompanyName", "[^"]*"', 'VALUE "CompanyName", "%s"' % COMPANY),
    (r'VALUE "FileDescription", "[^"]*"', 'VALUE "FileDescription", "%s"' % DISPLAY),
    (r'VALUE "LegalCopyright", "[^"]*"', 'VALUE "LegalCopyright", "%s"' % LEGAL),
    (r'VALUE "ProductName", "[^"]*"', 'VALUE "ProductName", "%s"' % DISPLAY),
], regex=True)

# 3. icons and logos
copy("icon.ico", "res/icon.ico")
copy("tray-icon.ico", "res/tray-icon.ico")
copy("icon.ico", "flutter/windows/runner/resources/app_icon.ico")
copy("icon.ico", "flutter/assets/icon.ico")
copy("icon-1024.png", "res/icon.png")
copy("icon-256.png", "flutter/assets/icon.png")
copy("icon.svg", "flutter/assets/icon.svg")
copy("icon.svg", "res/logo.svg")
copy("icon-32.png", "res/32x32.png")
copy("icon-64.png", "res/64x64.png")
copy("icon-128.png", "res/128x128.png")
copy("icon-256.png", "res/128x128@2x.png")
copy("logo_light.png", "flutter/assets/logo_light.png")
copy("logo_dark.png", "flutter/assets/logo_dark.png")

# 4. colours (Vision IT blue)
edit("flutter/lib/common.dart", [
    ("static const Color accent = Color(0xFF0071FF);", "static const Color accent = Color(0xFF1668D6);"),
    ("static const Color accent50 = Color(0x770071FF);", "static const Color accent50 = Color(0x771668D6);"),
    ("static const Color accent80 = Color(0xAA0071FF);", "static const Color accent80 = Color(0xAA1668D6);"),
    ("static const Color button = Color(0xFF2C8CFF);", "static const Color button = Color(0xFF1F8BF0);"),
])

# 5. "About" page: our contact + the notices required by the AGPL (origin, licence, source code)
edit("flutter/lib/desktop/pages/desktop_setting_page.dart", [
    ("launchUrlString('https://rustdesk.com/privacy.html');", "launchUrlString('%s');" % WEBSITE),
    ("launchUrlString('https://rustdesk.com');", "launchUrlString('%s');" % WEBSITE),
    ("decoration: const BoxDecoration(color: Color(0xFF2c8cff)),", "decoration: const BoxDecoration(color: Color(0xFF1668D6)),"),
    ("'Copyright © ${DateTime.now().toString().substring(0, 4)} Purslane Tech Pte. Ltd.\\n$license',",
     "'%s © ${DateTime.now().toString().substring(0, 4)} %s\\n'\n"
     "                            'Based on RustDesk, Copyright © Purslane Tech Pte. Ltd. Licence: AGPL-3.0.\\n'\n"
     "                            'Source code: %s\\n$license'," % (DISPLAY, COMPANY, SOURCE)),
    ("translate('Slogan_tip'),", "'%s · tel. 600 800 642 · %s'," % (COMPANY, WEBSITE.replace("https://", ""))),
])
print("Vision Connect branding applied.")

# ---- second round (13.11.2026) ----
# 6. texts: show the name with a space ("Vision Connect") wherever RustDesk's own name was shown
edit("src/lang.rs", [
    ("let app_name = crate::get_app_name();", 'let app_name = "%s".to_owned();' % DISPLAY),
])

# 7. hide the "Powered by RustDesk" line above the logo (the notice stays on the About page)
#    and the "set up your own server" hint (the Vision Connect server is already built in)
edit("flutter/lib/common.dart", [
    ('if (bind.mainGetBuildinOption(key: "hide-powered-by-me") == \'Y\') {', "if (true) {"),
])
edit("flutter/lib/desktop/pages/connection_page.dart", [
    ("offstage: !(!_svcStopped.value &&", "offstage: true || !(!_svcStopped.value &&"),
])

# 8. the packed program file gets its own name: process VisionConnect.exe instead of rustdesk.exe,
#    unpacked to %LOCALAPPDATA%\visionconnect (not shared with a portable RustDesk)
edit("libs/portable/generate.py", [
    ("    exe: str = os.path.abspath(options.executable)\n",
     "    exe: str = os.path.abspath(options.executable)\n"
     "    if os.path.basename(exe).lower() == 'rustdesk.exe':\n"
     "        _vc = os.path.join(os.path.dirname(exe), '%s.exe')\n"
     "        os.replace(exe, _vc)\n"
     "        exe = _vc\n" % APP_NAME),
])
print("Vision Connect branding, second round applied.")
