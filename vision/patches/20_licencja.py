# Vision Connect licence in the program itself (16.11.2026, "WERSJA 6").
# - vision/patches/vision_license.rs (copied to src/vision_license.rs): checks the licence key (RSA signature, end date, trial period);
# - the PERMANENT password (unattended access) is accepted only with a valid licence or during
#   the trial period; the one-time password and "accept by click" always work;
# - home page: a card with the licence state and a "Wpisz klucz" button (shown only when the
#   permanent password / installed service is in use and the licence is not simply valid);
# - About page: a "Licencja: ..." line that opens the same dialog;
# - install page: the privacy link points to Vision IT Serwis instead of rustdesk.com.
# No new FFI functions (the bridge is generated before branding): the existing main_get_common
# is used with the keys "vc-license" and "vc-license-set:<key>".
# Patterns are single-line on purpose (the Windows checkout has CRLF line ends).

shutil.copyfile(os.path.join(V, "patches", "vision_license.rs"), os.path.join(ROOT, "src", "vision_license.rs"))
print("copied  src/vision_license.rs")

edit("src/lib.rs", [
    ("mod custom_server;", "mod custom_server;\nmod vision_license;"),
])

edit("src/server/connection.rs", [
    ("        if password::permanent_enabled() || allow_permanent_password {",
     "        if (password::permanent_enabled() || allow_permanent_password) && crate::vision_license::permanent_allowed() {"),
])

edit("src/flutter_ffi.rs", [
    ("pub fn main_get_common(key: String) -> String {",
     "pub fn main_get_common(key: String) -> String {\n"
     "    if key == \"vc-license\" {\n"
     "        return crate::vision_license::status_json();\n"
     "    }\n"
     "    if let Some(k) = key.strip_prefix(\"vc-license-set:\") {\n"
     "        return crate::vision_license::set_key(k);\n"
     "    }"),
])

# ---- user interface (Flutter) ----
_p = os.path.join(ROOT, "flutter/lib/common/widgets/dialog.dart")
with io.open(_p, "r", encoding="utf-8", newline="") as _f:
    _s = _f.read()
if "vcLicenseDialog" in _s:
    sys.exit("20_licencja.py: dialog.dart already contains vcLicenseDialog")
_s += r'''

// ---- Vision Connect: licence (vision/patches/20_licencja.py) ----
Map<String, dynamic> vcLicenseInfo() {
  try {
    final v = jsonDecode(bind.mainGetCommonSync(key: 'vc-license'));
    if (v is Map<String, dynamic>) return v;
  } catch (_) {}
  return <String, dynamic>{};
}

void vcLicenseDialog({Function()? callback}) {
  final controller = TextEditingController();
  var msg = '';
  gFFI.dialogManager.show((setState, close, context) {
    final opis = (vcLicenseInfo()['opis'] ?? '').toString();
    return CustomAlertDialog(
      title: Text('Licencja Vision Connect'),
      content: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(opis),
          const SizedBox(height: 12.0),
          Text('Wklej klucz licencji (zaczyna się od VC1-):'),
          const SizedBox(height: 8.0),
          Row(
            children: [
              Expanded(
                child: TextField(
                  minLines: 3,
                  maxLines: 6,
                  decoration: InputDecoration(
                    errorText: msg.isEmpty ? null : msg,
                    errorMaxLines: 5,
                  ),
                  controller: controller,
                  autofocus: true,
                ),
              ),
            ],
          ),
        ],
      ),
      actions: [
        dialogButton('Cancel', onPressed: close, isOutline: true),
        dialogButton('OK', onPressed: () {
          final k = controller.text.replaceAll(RegExp(r'\s+'), '');
          if (k.isEmpty) {
            setState(() {
              msg = 'Wklej klucz licencji.';
            });
            return;
          }
          var res = <String, dynamic>{};
          try {
            final v =
                jsonDecode(bind.mainGetCommonSync(key: 'vc-license-set:$k'));
            if (v is Map<String, dynamic>) res = v;
          } catch (_) {}
          if (res['ok'] == true) {
            callback?.call();
            close();
            showToast((res['opis'] ?? 'Klucz licencji zapisany.').toString());
          } else {
            setState(() {
              msg = (res['blad'] ?? 'Nie udało się zapisać klucza.').toString();
            });
          }
        }),
      ],
      onCancel: close,
    );
  });
}
'''
with io.open(_p, "w", encoding="utf-8", newline="") as _f:
    _f.write(_s)
print("patched flutter/lib/common/widgets/dialog.dart (appended)")

edit("flutter/lib/desktop/pages/desktop_home_page.dart", [
    ("import '../widgets/button.dart';",
     "import '../widgets/button.dart';\n"
     "import '../../common/widgets/dialog.dart' show vcLicenseDialog, vcLicenseInfo;"),
    ("  Widget buildHelpCards(String updateUrl) {",
     "  Widget buildHelpCards(String updateUrl) {\n"
     "    final rest = buildHelpCardsRustDesk(updateUrl);\n"
     "    final info = vcLicenseInfo();\n"
     "    if (info['pokaz'] != true) return rest;\n"
     "    final card = buildInstallCard(\n"
     "        'Licencja', (info['opis'] ?? '').toString(), 'Wpisz klucz', () {\n"
     "      vcLicenseDialog(callback: () => setState(() {}));\n"
     "    });\n"
     "    return Column(mainAxisSize: MainAxisSize.min, children: [card, rest]);\n"
     "  }\n"
     "\n"
     "  Widget buildHelpCardsRustDesk(String updateUrl) {"),
])

edit("flutter/lib/desktop/pages/desktop_setting_page.dart", [
    (r"( *)(SelectionArea\(\s*child: Text\('\$\{translate\('Version'\)\}: \$version'\))",
     lambda m: m.group(1) + "InkWell(\n"
     + m.group(1) + "    onTap: () => vcLicenseDialog(callback: () => setState(() {})),\n"
     + m.group(1) + "    child: Text('Licencja: ${(vcLicenseInfo()['krotko'] ?? '').toString()}',\n"
     + m.group(1) + "            style: const TextStyle(decoration: TextDecoration.underline))\n"
     + m.group(1) + "        .marginSymmetric(vertical: 4.0)),\n"
     + m.group(1) + m.group(2)),
], regex=True)

edit("flutter/lib/desktop/pages/install_page.dart", [
    ("https://rustdesk.com/privacy.html", WEBSITE),
])
print("Vision Connect licence patch applied.")
