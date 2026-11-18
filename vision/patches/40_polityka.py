# Vision Connect: the "Privacy Statement" links open the privacy policy page (18.11.2026).
# Runs after brand.py and 20_licencja.py, which pointed these links at the home page.

PRIVACY = WEBSITE + "/vision-connect-prywatnosc/"

edit("flutter/lib/desktop/pages/desktop_setting_page.dart", [
    (r"launchUrlString\('%s'\);(\s*\},\s*child: Text\(\s*translate\('Privacy Statement'\))" % re.escape(WEBSITE),
     lambda m: "launchUrlString('%s');" % PRIVACY + m.group(1)),
], regex=True)

edit("flutter/lib/desktop/pages/install_page.dart", [
    ("'%s'" % WEBSITE, "'%s'" % PRIVACY),
])
print("Vision Connect: privacy links ->", PRIVACY)
