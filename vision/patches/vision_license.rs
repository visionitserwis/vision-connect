// Vision Connect - licence check (Vision IT Serwis, https://visionitserwis.pl).
// Lives in vision/patches/; copied to src/vision_license.rs at build time by 20_licencja.py.
//
// A licence key ("VC1-<data>.<signature>", base64url) is a small JSON document
// {"Nr","Klient","Do","Komp","Wyd"} signed with RSA 2048 / SHA-256 / PKCS#1 v1.5.
// The same key and the same folder are used by the licence guard of the unattended-access
// installer (PowerShell), so one key file serves both.
//
// What the licence controls: the PERMANENT password (unattended access). Without a valid
// licence (after the trial period) only the one-time password and "accept by click" work,
// so on-demand help is never blocked.
//
// No extra dependencies: base64 and RSA verification are implemented here; sha2 and
// serde_json are already used by the program.

use sha2::{Digest, Sha256};
use std::path::PathBuf;
use std::sync::Mutex;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

// Public key of Vision IT Serwis (modulus, exponent is 65537). Public by design.
const MODULUS_B64: &str = "td4OB9SqIQdKDh+Dx+X2WrDqQXnP6/0Xbw9e/BBfcTCC07pPDs69KZncLPwH5rpG2T8Ct0w/C8oQf70ikDC5TLugTO52BsJmiYkbMK0SMI/j37qsSdPvjCPNHORZQv5hz/lh/DKndEVSzXd/tbUOYVucaxx1WqwkLEK7XG0V5cfZhPLjbbj1s6U1uHd84JcOSPsYbHv85YWup9tjmg3oqcfzxjuAzD3U+34v7p6LfBsgAp3dcZdjVb4j24VQJzYlSk0l5PCFb83kVHLRpBsP64QtJ+u0aKXjgPVSNn+aoAVlqCow8VJFFWSqWXmboCT8aXehyPvgcBJ6aWBQviGx9Q==";

const TRIAL_DAYS: i64 = 14;
const GRACE_DAYS: i64 = 7;
const WARN_DAYS: i64 = 30;
const CONTACT: &str = "Vision IT Serwis, tel. 600 800 642";
const KEY_BYTES: usize = 256;
const LIMBS: usize = KEY_BYTES / 4 + 1;
const CACHE_TIME: Duration = Duration::from_secs(30);

#[derive(Clone, Debug)]
pub struct Status {
    /// OK | KONCZY | ZAPAS | PROBNA | BLOKADA
    pub stan: &'static str,
    pub dni: i64,
    pub opis: String,
    pub krotko: String,
}

#[derive(Clone, Debug)]
struct Licence {
    nr: String,
    klient: String,
    do_txt: String,
    do_days: i64,
}

static CACHE: Mutex<Option<(Instant, Status)>> = Mutex::new(None);

// ---------- small helpers ----------

fn b64_decode(s: &str) -> Option<Vec<u8>> {
    // accepts both the standard and the URL-safe alphabet, padding optional
    let mut out = Vec::with_capacity(s.len() * 3 / 4);
    let mut acc: u32 = 0;
    let mut bits = 0;
    for c in s.bytes() {
        let v = match c {
            b'A'..=b'Z' => c - b'A',
            b'a'..=b'z' => c - b'a' + 26,
            b'0'..=b'9' => c - b'0' + 52,
            b'+' | b'-' => 62,
            b'/' | b'_' => 63,
            b'=' => continue,
            _ => return None,
        };
        acc = (acc << 6) | v as u32;
        bits += 6;
        if bits >= 8 {
            bits -= 8;
            out.push((acc >> bits) as u8);
            acc &= (1 << bits) - 1;
        }
    }
    Some(out)
}

fn days_from_civil(y: i64, m: i64, d: i64) -> i64 {
    // days since 1970-01-01 (proleptic Gregorian calendar)
    let y = if m <= 2 { y - 1 } else { y };
    let era = if y >= 0 { y } else { y - 399 } / 400;
    let yoe = y - era * 400;
    let doy = (153 * (if m > 2 { m - 3 } else { m + 9 }) + 2) / 5 + d - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    era * 146097 + doe - 719468
}

fn civil_from_days(z: i64) -> (i64, i64, i64) {
    let z = z + 719468;
    let era = if z >= 0 { z } else { z - 146096 } / 146097;
    let doe = z - era * 146097;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    (if m <= 2 { y + 1 } else { y }, m, d)
}

fn parse_date(s: &str) -> Option<i64> {
    // "yyyy-MM-dd" -> days since 1970-01-01
    let s = s.trim();
    let p: Vec<&str> = s.split('-').collect();
    if p.len() != 3 || p[0].len() != 4 {
        return None;
    }
    let y: i64 = p[0].parse().ok()?;
    let m: i64 = p[1].parse().ok()?;
    let d: i64 = p[2].parse().ok()?;
    if !(1..=12).contains(&m) || !(1..=31).contains(&d) {
        return None;
    }
    Some(days_from_civil(y, m, d))
}

fn format_date(days: i64) -> String {
    let (y, m, d) = civil_from_days(days);
    format!("{:04}-{:02}-{:02}", y, m, d)
}

fn today() -> i64 {
    // test hook, debug builds only
    #[cfg(debug_assertions)]
    if let Some(d) = std::env::var("VIT_LIC_TODAY").ok().and_then(|t| parse_date(&t)) {
        return d;
    }
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0);
    secs / 86400
}

// ---------- RSA signature check (PKCS#1 v1.5, SHA-256, e = 65537) ----------

fn to_limbs(be: &[u8]) -> Option<Vec<u32>> {
    // big-endian bytes -> little-endian 32-bit limbs
    let be: &[u8] = {
        let mut b = be;
        while b.len() > KEY_BYTES && b[0] == 0 {
            b = &b[1..];
        }
        b
    };
    if be.len() > KEY_BYTES {
        return None;
    }
    let mut v = vec![0u32; LIMBS];
    for (i, byte) in be.iter().rev().enumerate() {
        v[i / 4] |= (*byte as u32) << (8 * (i % 4));
    }
    Some(v)
}

fn ge(a: &[u32], b: &[u32]) -> bool {
    for i in (0..a.len()).rev() {
        if a[i] != b[i] {
            return a[i] > b[i];
        }
    }
    true
}

fn sub(a: &mut [u32], b: &[u32]) {
    let mut borrow = 0u64;
    for i in 0..a.len() {
        let x = a[i] as u64;
        let y = b[i] as u64 + borrow;
        if x >= y {
            a[i] = (x - y) as u32;
            borrow = 0;
        } else {
            a[i] = (x + (1u64 << 32) - y) as u32;
            borrow = 1;
        }
    }
}

fn add(a: &mut [u32], b: &[u32]) {
    let mut carry = 0u64;
    for i in 0..a.len() {
        let v = a[i] as u64 + b[i] as u64 + carry;
        a[i] = v as u32;
        carry = v >> 32;
    }
}

fn shl1(a: &mut [u32]) {
    let mut carry = 0u32;
    for x in a.iter_mut() {
        let next = *x >> 31;
        *x = (*x << 1) | carry;
        carry = next;
    }
}

fn mulmod(a: &[u32], b: &[u32], m: &[u32]) -> Vec<u32> {
    // a, b < m; m < 2^(32*(LIMBS-1)), so one spare limb is enough for the doubling
    let mut r = vec![0u32; LIMBS];
    for i in (0..(LIMBS - 1) * 32).rev() {
        shl1(&mut r);
        if ge(&r, m) {
            sub(&mut r, m);
        }
        if (b[i / 32] >> (i % 32)) & 1 == 1 {
            add(&mut r, a);
            if ge(&r, m) {
                sub(&mut r, m);
            }
        }
    }
    r
}

fn rsa_verify(data: &[u8], signature: &[u8]) -> bool {
    let modulus = match b64_decode(MODULUS_B64).and_then(|b| to_limbs(&b)) {
        Some(m) => m,
        None => return false,
    };
    if signature.len() != KEY_BYTES {
        return false;
    }
    let s = match to_limbs(signature) {
        Some(s) => s,
        None => return false,
    };
    if ge(&s, &modulus) {
        return false;
    }
    // s^65537 mod n
    let mut r = s.clone();
    for _ in 0..16 {
        r = mulmod(&r, &r, &modulus);
    }
    r = mulmod(&r, &s, &modulus);
    let mut em = vec![0u8; KEY_BYTES];
    for i in 0..KEY_BYTES {
        em[KEY_BYTES - 1 - i] = (r[i / 4] >> (8 * (i % 4))) as u8;
    }
    // expected: 00 01 FF..FF 00 <DigestInfo SHA-256> <hash>
    const DIGEST_INFO: [u8; 19] = [
        0x30, 0x31, 0x30, 0x0d, 0x06, 0x09, 0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01,
        0x05, 0x00, 0x04, 0x20,
    ];
    let hash = Sha256::digest(data);
    let mut expected = vec![0xffu8; KEY_BYTES];
    expected[0] = 0;
    expected[1] = 1;
    let t = DIGEST_INFO.len() + hash.len();
    expected[KEY_BYTES - t - 1] = 0;
    expected[KEY_BYTES - t..KEY_BYTES - hash.len()].copy_from_slice(&DIGEST_INFO);
    expected[KEY_BYTES - hash.len()..].copy_from_slice(&hash);
    // not secret data, a plain comparison is fine
    em == expected
}

// ---------- licence key ----------

fn computer_name() -> String {
    std::env::var("COMPUTERNAME").unwrap_or_default()
}

fn check_key(key: &str) -> Result<Licence, String> {
    let k: String = key.chars().filter(|c| !c.is_whitespace()).collect();
    let body = k
        .strip_prefix("VC1-")
        .ok_or_else(|| "zły format klucza (klucz zaczyna się od VC1-)".to_owned())?;
    let mut parts = body.split('.');
    let (d, s) = match (parts.next(), parts.next(), parts.next()) {
        (Some(d), Some(s), None) if !d.is_empty() && !s.is_empty() => (d, s),
        _ => return Err("zły format klucza".to_owned()),
    };
    let data = b64_decode(d).ok_or_else(|| "zły format klucza".to_owned())?;
    let sig = b64_decode(s).ok_or_else(|| "zły format klucza".to_owned())?;
    if !rsa_verify(&data, &sig) {
        return Err(
            "zły podpis klucza (klucz nie pochodzi od Vision IT Serwis albo jest uszkodzony)"
                .to_owned(),
        );
    }
    let j: serde_json::Value = serde_json::from_slice(&data)
        .map_err(|_| "nie można odczytać danych klucza".to_owned())?;
    let field = |name: &str| j.get(name).and_then(|v| v.as_str()).unwrap_or("").to_owned();
    let do_txt = field("Do");
    let do_days =
        parse_date(&do_txt).ok_or_else(|| "nie można odczytać daty w kluczu".to_owned())?;
    let komp = field("Komp");
    if !komp.is_empty() && komp != "*" {
        let me = computer_name().to_lowercase();
        let allowed = komp
            .split(|c: char| c == ',' || c == ';' || c == ' ')
            .filter(|x| !x.is_empty())
            .any(|x| x.to_lowercase() == me);
        if !allowed {
            return Err(format!(
                "klucz jest dla innego komputera ({}), a ten to {}",
                komp,
                computer_name()
            ));
        }
    }
    Ok(Licence {
        nr: field("Nr"),
        klient: field("Klient"),
        do_txt,
        do_days,
    })
}

// ---------- files ----------

fn dir() -> PathBuf {
    // test hook, debug builds only
    #[cfg(debug_assertions)]
    if let Ok(d) = std::env::var("VIT_LIC_DIR") {
        if !d.is_empty() {
            return PathBuf::from(d);
        }
    }
    let base = std::env::var("ProgramData").unwrap_or_else(|_| "C:\\ProgramData".to_owned());
    PathBuf::from(base).join("VisionIT").join("VisionConnect")
}

fn read_text(path: &PathBuf) -> Option<String> {
    let b = std::fs::read(path).ok()?;
    let s = String::from_utf8_lossy(&b).to_string();
    Some(s.trim_start_matches('\u{feff}').trim().to_owned())
}

/// Best valid licence from every "licencja*.txt" in the folder (latest end date wins),
/// or the reason why there is none.
fn find_licence() -> Result<Licence, String> {
    let mut best: Option<Licence> = None;
    let mut reason = "brak klucza abonamentu".to_owned();
    if let Ok(entries) = std::fs::read_dir(dir()) {
        for e in entries.flatten() {
            let name = e.file_name().to_string_lossy().to_lowercase();
            if !name.starts_with("licencja") || !name.ends_with(".txt") {
                continue;
            }
            let Some(text) = read_text(&e.path()) else {
                continue;
            };
            if text.is_empty() {
                continue;
            }
            match check_key(&text) {
                Ok(l) => {
                    if best.as_ref().map(|b| l.do_days > b.do_days).unwrap_or(true) {
                        best = Some(l);
                    }
                }
                Err(r) => reason = r,
            }
        }
    }
    best.ok_or(reason)
}

/// First day the program (or the licence guard) was seen on this computer.
fn trial_start(today: i64) -> i64 {
    let d = dir();
    let mut start: Option<i64> = None;
    // the licence guard of the unattended-access installer keeps its own date
    if let Some(t) = read_text(&d.join("stan.json")) {
        if let Ok(j) = serde_json::from_str::<serde_json::Value>(&t) {
            start = j.get("Instalacja").and_then(|v| v.as_str()).and_then(parse_date);
        }
    }
    let mine = d.join("program-start.txt");
    match read_text(&mine).and_then(|t| parse_date(&t)) {
        Some(x) => start = Some(start.map(|s| s.min(x)).unwrap_or(x)),
        None => {
            let _ = std::fs::create_dir_all(&d);
            let _ = std::fs::write(&mine, format_date(today));
        }
    }
    start.unwrap_or(today).min(today)
}

// ---------- state ----------

fn evaluate() -> Status {
    let today = today();
    match find_licence() {
        Ok(l) => {
            let dni = l.do_days - today;
            let kto = format!("Abonament {} ({})", l.nr, l.klient);
            if dni > WARN_DAYS {
                Status {
                    stan: "OK",
                    dni,
                    opis: format!("{} ważny do {} (jeszcze {} dni).", kto, l.do_txt, dni),
                    krotko: format!("{}, {} - ważny do {}", l.nr, l.klient, l.do_txt),
                }
            } else if dni >= 0 {
                Status {
                    stan: "KONCZY",
                    dni,
                    opis: format!(
                        "{} wygasa {} - zostało {} dni. Zamów nowy klucz: {}.",
                        kto, l.do_txt, dni, CONTACT
                    ),
                    krotko: format!("{}, {} - wygasa {}", l.nr, l.klient, l.do_txt),
                }
            } else if dni >= -GRACE_DAYS {
                Status {
                    stan: "ZAPAS",
                    dni,
                    opis: format!(
                        "{} WYGASŁ {}. Stałe hasło (stały dostęp) zostanie wyłączone za {} dni. Nowy klucz: {}.",
                        kto,
                        l.do_txt,
                        GRACE_DAYS + dni,
                        CONTACT
                    ),
                    krotko: format!("{}, {} - WYGASŁ {}", l.nr, l.klient, l.do_txt),
                }
            } else {
                Status {
                    stan: "BLOKADA",
                    dni,
                    opis: format!(
                        "{} wygasł {}. Stałe hasło (stały dostęp) jest WYŁĄCZONE; pomoc na hasło jednorazowe działa. Nowy klucz: {}.",
                        kto, l.do_txt, CONTACT
                    ),
                    krotko: format!("{}, {} - wygasł {}", l.nr, l.klient, l.do_txt),
                }
            }
        }
        Err(powod) => {
            let left = TRIAL_DAYS - (today - trial_start(today));
            if left >= 0 {
                Status {
                    stan: "PROBNA",
                    dni: left,
                    opis: format!(
                        "Stałe hasło (stały dostęp) bez abonamentu - okres próbny, zostało {} dni. Klucz abonamentu: {}.",
                        left, CONTACT
                    ),
                    krotko: format!("{} - okres próbny, zostało {} dni", powod, left),
                }
            } else {
                Status {
                    stan: "BLOKADA",
                    dni: left,
                    opis: format!(
                        "Brak ważnego abonamentu ({}) - okres próbny minął. Stałe hasło (stały dostęp) jest WYŁĄCZONE; pomoc na hasło jednorazowe działa. Klucz abonamentu: {}.",
                        powod, CONTACT
                    ),
                    krotko: format!("{} - okres próbny minął", powod),
                }
            }
        }
    }
}

pub fn status() -> Status {
    if let Ok(mut c) = CACHE.lock() {
        if let Some((t, s)) = c.as_ref() {
            if t.elapsed() < CACHE_TIME {
                return s.clone();
            }
        }
        let s = evaluate();
        *c = Some((Instant::now(), s.clone()));
        return s;
    }
    evaluate()
}

/// May a connection be authorised with the permanent password?
pub fn permanent_allowed() -> bool {
    status().stan != "BLOKADA"
}

fn uses_unattended_access() -> bool {
    if hbb_common::config::Config::has_permanent_password() {
        return true;
    }
    #[cfg(target_os = "windows")]
    {
        if crate::platform::is_installed() {
            return true;
        }
    }
    false
}

/// For the user interface (FFI key "vc-license").
pub fn status_json() -> String {
    let s = status();
    let pokaz = s.stan != "OK" && uses_unattended_access();
    serde_json::json!({
        "stan": s.stan,
        "dni": s.dni,
        "opis": s.opis,
        "krotko": s.krotko,
        "pokaz": pokaz,
    })
    .to_string()
}

/// Checks and stores a key typed in the program window (FFI key "vc-license-set:<key>").
pub fn set_key(key: &str) -> String {
    let k: String = key.chars().filter(|c| !c.is_whitespace()).collect();
    let lic = match check_key(&k) {
        Ok(l) => l,
        Err(e) => return serde_json::json!({ "ok": false, "blad": format!("Klucz odrzucony: {}.", e) }).to_string(),
    };
    let d = dir();
    let _ = std::fs::create_dir_all(&d);
    // "licencja.txt" is the file of the licence guard; if it belongs to the administrator
    // and cannot be replaced, the key is stored next to it (every licencja*.txt is read)
    let mut saved = false;
    for name in ["licencja.txt", "licencja-nowa.txt", "licencja-nowa-2.txt"] {
        if std::fs::write(d.join(name), format!("{}\r\n", k)).is_ok() {
            saved = true;
            break;
        }
    }
    if let Ok(mut c) = CACHE.lock() {
        *c = None;
    }
    if !saved {
        return serde_json::json!({
            "ok": false,
            "blad": format!("Klucz jest poprawny, ale nie udało się go zapisać w folderze {}. Uruchom program jako administrator albo użyj pliku \"ABONAMENT - wpisz klucz\".", d.display()),
        })
        .to_string();
    }
    serde_json::json!({
        "ok": true,
        "opis": format!("Abonament {} ({}) ważny do {}.", lic.nr, lic.klient, lic.do_txt),
    })
    .to_string()
}
