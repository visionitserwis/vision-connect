# Vision Connect: no "Install" card in the portable program (23.11.2026, release 11).
# The program run without installation (e.g. on an employee's laptop that only connects OUT)
# showed the upstream card "... click the button below to install ..." on the home page. A user who
# clicks it installs the program as a Windows service on a private computer - not wanted.
# Unattended access is set up only by the Vision IT Serwis installer ("--silent-install"), which
# does not use this card. The "lower version, click to upgrade" card of an installed program stays.
# Single-line pattern only (the Windows checkout has CRLF line ends).

edit("flutter/lib/desktop/pages/desktop_home_page.dart", [
    ("      if (!bind.mainIsInstalled()) {",
     "      if (!bind.mainIsInstalled()) {\n"
     "        // Vision Connect: the portable program shows no \"Install\" card (vision/patches/60_bez_instalacji.py)\n"
     "        return Container();"),
])
print("Vision Connect: install card hidden in the portable program.")
