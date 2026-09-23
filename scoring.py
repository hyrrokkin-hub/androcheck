#!/usr/bin/env python3
"""
scoring.py
Menghitung skor & grade kelayakan akhir dari seluruh hasil audit.
Bukan angka ilmiah presisi - hanya agregasi tertimbang untuk membantu
keputusan cepat saat transaksi jual-beli HP bekas.
"""

from typing import Dict, List, Tuple

# Bobot lebih besar untuk indikator yang paling menentukan kelayakan/nilai jual
CRITICAL_LABELS = {
    "Verified Boot State": 3,
    "Bootloader Lock State": 3,
    "Build Tags": 2,
    "Samsung Knox Warranty Bit": 3,
    "Deteksi Root": 2,
    "Estimasi Kesehatan Baterai (wear)": 3,
    "Siklus Pengisian (Cycle Count)": 2,
    "CPU Throttling": 1,
    "Baterai Terdeteksi": 3,
    "Konsistensi Brand vs Fingerprint": 3,
}

GRADE_TABLE = [
    (90, "A", "Sangat Layak - kondisi mendekati baru, minim red flag"),
    (75, "B", "Layak - kondisi wajar untuk HP bekas, ada beberapa catatan minor"),
    (55, "C", "Cukup - ada beberapa indikasi warning yang perlu dikonfirmasi ke penjual"),
    (0, "D", "Kurang Layak - ditemukan red flag signifikan, pertimbangkan ulang atau nego harga"),
]


def compute_score(all_rows: List[Dict]) -> Tuple[int, str, str, Dict]:
    total_weight = 0
    earned_weight = 0
    bad_flags = []
    warning_flags = []

    for row in all_rows:
        weight = CRITICAL_LABELS.get(row["label"], 1)
        total_weight += weight
        if row["status"] == "GOOD":
            earned_weight += weight
        elif row["status"] == "WARNING":
            earned_weight += weight * 0.5
            warning_flags.append(row["label"])
        elif row["status"] == "BAD":
            bad_flags.append(row["label"])
        else:  # INFO tidak mempengaruhi skor - keluarkan dari total_weight
            total_weight -= weight

    score = round((earned_weight / total_weight) * 100) if total_weight > 0 else 0
    score = max(0, min(100, score))

    grade, desc = "D", GRADE_TABLE[-1][2]
    for threshold, g, d in GRADE_TABLE:
        if score >= threshold:
            grade, desc = g, d
            break

    summary = {
        "score": score,
        "grade": grade,
        "description": desc,
        "bad_flags": bad_flags,
        "warning_flags": warning_flags,
    }
    return score, grade, desc, summary
