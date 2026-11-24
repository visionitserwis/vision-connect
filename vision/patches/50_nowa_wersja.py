# Vision Connect: notice about a new version (18.11.2026).
# The program has its own release number (VC_BUILD). Once per start it reads the page
# VERSION_PAGE on the Vision IT Serwis website and looks for the text "VC-WERSJA:<number>".
# A higher number than VC_BUILD shows a "Nowa wersja" card on the home page.
# Nothing is downloaded or installed automatically. The About page shows the release number.
# Runs after 20_licencja.py (it extends the code added there). Single-line patterns only.

VC_BUILD = 11
VERSION_PAGE = WEBSITE + "/vision-connect-wersja/"

_p = os.path.join(ROOT, "flutter/lib/common/widgets/dialog.dart")
with io.open(_p, "r", encoding="utf-8", newline="") as _f:
    _s = _f.read()
if "vcCheckUpdate" in _s:
    sys.exit("50_nowa_wersja.py: dialog.dart already contains vcCheckUpdate")
_s += r'''

// ---- Vision Connect: new-version notice (vision/patches/50_nowa_wersja.py) ----
const int vcBuild = __BUILD__;
int vcNewVersion = 0;
bool _vcUpdateChecked = false;

Future<void> vcCheckUpdate(Function() onNew) async {
  if (_vcUpdateChecked) return;
  _vcUpdateChecked = true;
  try {
    final r = await http.get(Uri.parse('__PAGE__'));
    if (r.statusCode != 200) return;
    final m = RegExp(r'VC-WERSJA:\s*(\d+)').firstMatch(r.body);
    final n = int.tryParse(m?.group(1) ?? '') ?? 0;
    if (n > vcBuild) {
      vcNewVersion = n;
      onNew();
    }
  } catch (_) {}
}
'''.replace("__BUILD__", str(VC_BUILD)).replace("__PAGE__", VERSION_PAGE)
with io.open(_p, "w", encoding="utf-8", newline="") as _f:
    _f.write(_s)
print("patched flutter/lib/common/widgets/dialog.dart (appended)")

edit("flutter/lib/desktop/pages/desktop_home_page.dart", [
    (" show vcLicenseDialog, vcLicenseInfo;",
     " show vcLicenseDialog, vcLicenseInfo, vcCheckUpdate, vcNewVersion, vcBuild;"),
    ("    final rest = buildHelpCardsRustDesk(updateUrl);",
     "    vcCheckUpdate(() {\n"
     "      if (mounted) setState(() {});\n"
     "    });\n"
     "    final rest0 = buildHelpCardsRustDesk(updateUrl);\n"
     "    final Widget rest = vcNewVersion > 0\n"
     "        ? Column(mainAxisSize: MainAxisSize.min, children: [\n"
     "            buildInstallCard(\n"
     "                'Nowa wersja',\n"
     "                'Jest nowa wersja Vision Connect (wydanie $vcNewVersion, na tym komputerze: $vcBuild). Zadzwoń: Vision IT Serwis, tel. 600 800 642.',\n"
     "                'Strona Vision IT', () {\n"
     "              launchUrl(Uri.parse('%s'));\n"
     "            }),\n"
     "            rest0\n"
     "          ])\n"
     "        : rest0;" % WEBSITE),
])

edit("flutter/lib/desktop/pages/desktop_setting_page.dart", [
    ("child: Text('Abonament: ${", "child: Text('Wydanie $vcBuild · Abonament: ${"),
])
print("Vision Connect: new-version notice, release", VC_BUILD)
