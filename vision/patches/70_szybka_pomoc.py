# Vision Connect: "szybka pomoc" - one-off help without installation (24.11.2026, release 11).
# When the program file name contains "pomoc" (e.g. VisionConnect-pomoc.exe), the program starts in the
# upstream "incoming only" mode: a small window with the ID, the one-time password, the connection
# status and a Quit button. The person being helped cannot connect out and is not offered installation.
# The same build under any other name is the full program - one build, two uses.
# The file name comes from the portable launcher (RUSTDESK_APPNAME) or, if absent, from the running exe.
# Nothing else changes: the one-time password, the server and the subscription key rules stay as they are.
# Single-line pattern only (the Windows checkout has CRLF line ends).

edit("src/common.rs", [
    ("pub fn load_custom_client() {",
     "pub fn load_custom_client() {\n"
     "    // Vision Connect: \"szybka pomoc\" - incoming-only window when the file name contains \"pomoc\" (vision/patches/70_szybka_pomoc.py)\n"
     "    {\n"
     "        let vc_name = std::env::var(PORTABLE_APPNAME_RUNTIME_ENV_KEY)\n"
     "            .ok()\n"
     "            .or_else(|| {\n"
     "                std::env::current_exe()\n"
     "                    .ok()\n"
     "                    .and_then(|p| p.file_name().map(|n| n.to_string_lossy().to_string()))\n"
     "            })\n"
     "            .unwrap_or_default()\n"
     "            .to_lowercase();\n"
     "        if vc_name.contains(\"pomoc\") {\n"
     "            config::HARD_SETTINGS\n"
     "                .write()\n"
     "                .unwrap()\n"
     "                .insert(\"conn-type\".to_owned(), \"incoming\".to_owned());\n"
     "        }\n"
     "    }"),
])
print("Vision Connect: quick-help (incoming only) mode by file name added.")
