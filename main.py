#!/usr/bin/env python3
"""
main.py - Entry point Android Used-Phone Audit Tool

Cara pakai:
    python3 main.py                    # audit interaktif, simpan txt+json
    python3 main.py --pdf              # sekalian export PDF
    python3 main.py -s <serial>        # pilih device tertentu (jika lebih dari 1 terhubung)
    python3 main.py --no-color         # matikan warna terminal
    python3 main.py -v                 # verbose/debug mode (tampilkan raw adb output)
    python3 main.py -o ./laporan       # ganti folder output

Requirement:
    - Android Platform Tools (adb) terinstall & ada di PATH
    - USB debugging aktif di HP yang mau dicek
    - Python 3.8+
"""

import argparse
import os
import platform
import re
import sys
from datetime import datetime

from adb_utils import AdbSession, AdbNotFoundError, NoDeviceError
import checks
import scoring
import report

# Windows cmd.exe lama (code page default cp1252/cp437) bisa crash saat print
# karakter unicode (✓, •, ↳). Paksa stdout ke UTF-8 dengan fallback aman
# supaya tool tetap jalan di Linux, macOS, maupun Windows tanpa perubahan kode.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def parse_args():
    p = argparse.ArgumentParser(description="Audit kelayakan HP Android bekas via ADB")
    p.add_argument("-s", "--serial", help="Serial number device tertentu (kalau lebih dari 1 device connect)")
    p.add_argument("-o", "--output-dir", default="output", help="Folder untuk simpan laporan (default: ./output)")
    p.add_argument("--pdf", action="store_true", help="Sekalian export laporan ke PDF (butuh: pip install fpdf2)")
    p.add_argument("--no-color", action="store_true", help="Matikan warna di output terminal")
    p.add_argument("--no-save", action="store_true", help="Jangan simpan file, tampilkan di terminal saja")
    p.add_argument("-v", "--verbose", action="store_true", help="Mode verbose, tampilkan raw output adb")
    p.add_argument("--timeout", type=int, default=10, help="Timeout per perintah adb dalam detik (default: 10)")
    return p.parse_args()


def build_sections(adb: AdbSession):
    """Menjalankan semua modul check dan menyusun jadi sections untuk report."""
    sections = []
    all_rows_flat = []

    def add_section(title, rows):
        sections.append({"title": title, "rows": rows})
        all_rows_flat.extend(rows)

    print("[*] Mengambil identitas perangkat...")
    add_section("IDENTITAS PERANGKAT & REGION", checks.check_identity(adb))

    print("[*] Mengecek IMEI & konektivitas...")
    add_section("IMEI & KONEKTIVITAS", checks.check_connectivity(adb))

    print("[*] Membaca spesifikasi CPU & RAM...")
    add_section("SPESIFIKASI PROSESOR & MEMORI (RAM)", checks.check_cpu_ram(adb))

    print("[*] Mengecek kapasitas storage...")
    add_section("KAPASITAS PENYIMPANAN (STORAGE)", checks.check_storage(adb))

    print("[*] Mengecek layar...")
    add_section("SPESIFIKASI & INTEGRITAS LAYAR", checks.check_display(adb))

    print("[*] Mengaudit baterai...")
    batt_rows, batt_extra = checks.check_battery(adb)
    add_section("AUDIT BATERAI & DAYA", batt_rows)

    print("[*] Mengecek beban thermal...")
    thermal_rows, thermal_extra = checks.check_thermal(adb, batt_extra)
    add_section("BEBAN THERMAL & DETEKSI PENGGUNAAN EKSTREM", thermal_rows)

    print("[*] Mengecek mesin & sensor...")
    add_section("AUDIT MESIN & SENSOR", checks.check_hardware_sensors(adb))

    brand = adb.getprop("ro.product.brand") or ""
    print("[*] Mengecek integritas sistem (bootloader/root/knox)...")
    add_section("INTEGRITAS SISTEM & GARANSI (ROOT/BOOTLOADER)", checks.check_system_integrity(adb, brand))

    print("[*] Menganalisis indikasi originalitas komponen...")
    add_section("INDIKASI ORIGINALITAS KOMPONEN", checks.check_originality(adb, batt_extra))

    return sections, all_rows_flat


def main():
    args = parse_args()

    print("=" * 62)
    print("   ANDROID USED-PHONE AUDIT TOOL - Menghubungkan device...")
    print("=" * 62)

    try:
        adb = AdbSession(serial=args.serial, timeout=args.timeout, verbose=args.verbose)
    except AdbNotFoundError as e:
        print(f"\n[!] {e}")
        sys.exit(1)
    except NoDeviceError as e:
        print(f"\n[!] {e}")
        sys.exit(1)

    print(f"[✓] Terhubung ke device: {adb.serial}\n")

    sections, all_rows_flat = build_sections(adb)
    score, grade, desc, summary = scoring.compute_score(all_rows_flat)

    use_color = (not args.no_color) and sys.stdout.isatty()
    if platform.system() == "Windows" and not report.COLORAMA_AVAILABLE:
        # cmd.exe klasik tanpa colorama tidak selalu render ANSI dengan benar.
        # Windows Terminal/PowerShell modern biasanya sudah support (WT_SESSION ada).
        if "WT_SESSION" not in os.environ and "ANSICON" not in os.environ:
            use_color = False
    plain_text = report.render_terminal(sections, summary, use_color=use_color)

    if not args.no_save:
        os.makedirs(args.output_dir, exist_ok=True)
        model = re.sub(r"[^A-Za-z0-9_-]+", "_", adb.getprop("ro.product.model") or "device")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"audit_{model}_{timestamp}"

        txt_path = report.save_txt(plain_text, args.output_dir, filename_base)
        print(f"\n[✓] Laporan teks disimpan: {txt_path}")

        device_meta = {
            "brand": adb.getprop("ro.product.brand"),
            "model": adb.getprop("ro.product.model"),
            "serial": adb.serial,
            "android_version": adb.getprop("ro.build.version.release"),
        }
        json_path = report.save_json(sections, summary, device_meta, args.output_dir, filename_base)
        print(f"[✓] Laporan JSON disimpan: {json_path}")

        if args.pdf:
            pdf_path = report.save_pdf(sections, summary, device_meta, args.output_dir, filename_base)
            if pdf_path:
                print(f"[✓] Laporan PDF disimpan: {pdf_path}")


if __name__ == "__main__":
    main()
