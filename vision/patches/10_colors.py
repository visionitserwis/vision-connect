# Vision Connect colours (14.11.2026): the palette of the Vision Connect logo instead of RustDesk's.
# Light theme: bluish-grey panels, blue ID, blue install card. Dark theme: navy instead of neutral black.
edit("flutter/lib/common.dart", [
    ("static const Color grayBg = Color(0xFFEFEFF2);", "static const Color grayBg = Color(0xFFEEF2F8);"),
    ("static const Color idColor = Color(0xFF00B6F0);", "static const Color idColor = Color(0xFF1F8BF0);"),
    ("Color(0xFF18191E)", "Color(0xFF101A2E)"),
    ("Color(0xFF24252B)", "Color(0xFF1B2944)"),
])
edit("flutter/lib/desktop/pages/desktop_home_page.dart", [
    ("Color.fromARGB(255, 226, 66, 188),", "Color.fromARGB(255, 15, 79, 184),"),
    ("Color.fromARGB(255, 244, 114, 124),", "Color.fromARGB(255, 31, 139, 240),"),
])
edit("flutter/lib/desktop/pages/connection_page.dart", [
    ("? Color.fromARGB(255, 50, 190, 166)", "? Color.fromARGB(255, 46, 184, 114)"),
])
