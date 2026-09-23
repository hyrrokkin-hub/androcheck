#!/usr/bin/env python3
"""
report.py
Render hasil audit ke terminal (berwarna, ANSI - aman untuk Linux terminal),
serta menyimpan ke file .txt, .json, dan opsional .pdf.
"""

import json
import os
from datetime import datetime
from typing import Dict, List

# colorama menerjemahkan kode ANSI jadi panggilan Win32 Console API, jadi
# warna tetap tampil benar di cmd.exe lama Windows. Di Linux/macOS opsional
# (ANSI sudah native didukung terminal), jadi tidak mengganggu kalau tidak ada.
try:
    import colorama
    colorama.init(autoreset=False)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

ANSI = {
    "GOOD": "\033[92m",     # hijau
    "WARNING": "\033[93m",  # kuning
    "BAD": "\033[91m",      # merah
    "INFO": "\033[96m",     # cyan
    "BOLD": "\033[1m",
    "RESET": "\033[0m",
}


def _colorize(text: str, status: str, use_color: bool) -> str:
    if not use_color:
        return text
    color = ANSI.get(status, "")
    return f"{color}{text}{ANSI['RESET']}"


def render_terminal(sections: List[Dict], summary: Dict, use_color: bool = True) -> str:
    """sections: list of {"title": str, "rows": [...]}. Mengembalikan string lengkap
    (sekaligus di-print) supaya bisa dipakai ulang untuk file .txt."""
    lines = []
    lines.append("=" * 62)
    lines.append("      ULTIMATE AUDIT TOOL - CEK KELAYAKAN HP ANDROID BEKAS")
    lines.append("=" * 62)

    for i, section in enumerate(sections, 1):
        lines.append(f"\n[{i}] {section['title']}")
        for row in section["rows"]:
            tag = f"[{row['status']}]"
            line = f"  • {row['label']:<32}: {row['value']} {tag}"
            lines.append(_colorize(line, row["status"], use_color))
            if row.get("note"):
                lines.append(f"      ↳ {row['note']}")

    lines.append("\n" + "=" * 62)
    lines.append("  RINGKASAN & SKOR KELAYAKAN")
    lines.append("=" * 62)
    grade_line = f"  Skor: {summary['score']}/100  |  Grade: {summary['grade']}"
    lines.append(_colorize(grade_line, "GOOD" if summary["grade"] in ("A", "B") else "WARNING" if summary["grade"] == "C" else "BAD", use_color))
    lines.append(f"  {summary['description']}")
    if summary["bad_flags"]:
        lines.append(f"\n  Red flags (BAD): {', '.join(summary['bad_flags'])}")
    if summary["warning_flags"]:
        lines.append(f"  Perlu dikonfirmasi (WARNING): {', '.join(summary['warning_flags'])}")
    lines.append("\n" + "=" * 62)
    lines.append("               AUDIT SELESAI DILAKUKAN")
    lines.append("=" * 62)

    output = "\n".join(lines)
    print(output)
    return output


def strip_ansi(text: str) -> str:
    import re
    return re.sub(r"\033\[[0-9;]*m", "", text)


def save_txt(plain_text: str, output_dir: str, filename_base: str) -> str:
    path = os.path.join(output_dir, f"{filename_base}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(strip_ansi(plain_text))
    return path


def save_json(sections: List[Dict], summary: Dict, device_meta: Dict, output_dir: str, filename_base: str) -> str:
    data = {
        "generated_at": datetime.now().isoformat(),
        "device": device_meta,
        "sections": sections,
        "summary": summary,
    }
    path = os.path.join(output_dir, f"{filename_base}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def save_pdf(sections: List[Dict], summary: Dict, device_meta: Dict, output_dir: str, filename_base: str) -> str:
    """Export ke PDF pakai fpdf2 (pure-python, ringan, tanpa dependency sistem berat).
    Return path file jika sukses, atau None jika library tidak terinstall."""
    try:
        from fpdf import FPDF
    except ImportError:
        print("\n[!] Library 'fpdf2' belum terinstall. Jalankan: pip install fpdf2")
        return None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Laporan Audit Kelayakan HP Android Bekas", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Dibuat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    model = device_meta.get("model", "N/A")
    brand = device_meta.get("brand", "N/A")
    pdf.cell(0, 6, f"Perangkat: {brand} {model}", ln=True)
    pdf.ln(4)

    status_colors = {"GOOD": (0, 140, 0), "WARNING": (200, 140, 0), "BAD": (200, 0, 0), "INFO": (0, 100, 160)}

    for section in sections:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, section["title"], ln=True)
        pdf.set_font("Helvetica", "", 9)
        for row in section["rows"]:
            r, g, b = status_colors.get(row["status"], (0, 0, 0))
            pdf.set_text_color(r, g, b)
            text = f"- {row['label']}: {row['value']} [{row['status']}]"
            pdf.multi_cell(0, 5, text)
            if row.get("note"):
                pdf.set_text_color(90, 90, 90)
                pdf.multi_cell(0, 5, f"    {row['note']}")
        pdf.ln(2)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Ringkasan & Skor Kelayakan", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, f"Skor: {summary['score']}/100  |  Grade: {summary['grade']}\n{summary['description']}")
    if summary["bad_flags"]:
        pdf.set_text_color(200, 0, 0)
        pdf.multi_cell(0, 6, f"Red flags: {', '.join(summary['bad_flags'])}")
    if summary["warning_flags"]:
        pdf.set_text_color(200, 140, 0)
        pdf.multi_cell(0, 6, f"Perlu dikonfirmasi: {', '.join(summary['warning_flags'])}")

    path = os.path.join(output_dir, f"{filename_base}.pdf")
    pdf.output(path)
    return path
