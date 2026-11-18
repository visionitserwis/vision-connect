# Vision Connect: no account / address book (18.11.2026).
# The Vision Connect server is the open-source one (no account service), so "Log in",
# the "Account" settings page, the address book tab and the group tab cannot work.
# RustDesk already has a switch for this ("disable-account"); here it is always on.
# One-line pattern on purpose (the Windows checkout has CRLF line ends).

edit("libs/hbb_common/src/config.rs", [
    ('    is_some_hard_opton("disable-account")',
     '    true // Vision Connect: no account server (vision/patches/30_bez_konta.py)'),
])
print("Vision Connect: account and address book hidden.")
