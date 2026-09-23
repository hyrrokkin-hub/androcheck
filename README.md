# Android Used-Phone Audit Tool

Tool CLI berbasis Python untuk membantu audit kelayakan HP Android bekas
sebelum dibeli, lewat ADB (Android Debug Bridge). Berjalan di Linux,
generik lintas brand (Samsung, Xiaomi, Oppo, Vivo, Realme, Pixel, dll)
dengan fallback otomatis untuk properti yang berbeda-beda per vendor.

> **Catatan penting:** Layar, kamera, dan kondisi fisik lain tetap harus
> dicek manual. Tool ini fokus pada data yang bisa diambil lewat ADB:
> identitas perangkat, IMEI, CPU/RAM, storage, baterai, thermal,
> integritas sistem (root/bootloader/Knox), dan indikasi originalitas
> komponen berbasis konsistensi data sistem.

## Fitur

- **10 kategori audit**: identitas perangkat, IMEI & konektivitas, CPU/RAM,
  storage, layar, baterai (termasuk estimasi wear% dari charge_full vs
  charge_full_design), thermal & throttling, sensor, integritas sistem
  (root/bootloader/Knox), dan indikasi originalitas komponen.
- **Skor & grade kelayakan (A–D)** otomatis di akhir laporan, dengan daftar
  red flag yang perlu ditanyakan ke penjual.
- **Generik multi-brand** — tiap indikator dicoba lewat beberapa
  command/path fallback (tidak error kalau satu vendor tidak menyediakan
  properti tertentu).
- **Output**: terminal berwarna, file `.txt`, `.json`, dan opsional `.pdf`.
- **Multi-device**: kalau lebih dari 1 HP terhubung, tool akan minta pilih.
- Tanpa dependency eksternal untuk fitur inti (pure Python standard library).

## Instalasi

Tool ini murni Python standard library untuk fitur inti, jadi jalan di
**Linux, Windows, maupun macOS** tanpa perubahan kode — yang beda cuma cara
install `adb` dan driver USB-nya.

### Linux (Pop!_OS/Ubuntu/Debian)

```bash
git clone <repo-url>
cd android-audit-tool

sudo apt install android-tools-adb
pip install -r requirements.txt --break-system-packages   # opsional, untuk export PDF
```

### Windows

```powershell
git clone <repo-url>
cd android-audit-tool

pip install -r requirements.txt   # opsional: fpdf2 (PDF) + colorama (warna di cmd.exe)
```

Untuk `adb` di Windows:
1. Download **SDK Platform-Tools for Windows** dari
   https://developer.android.com/tools/releases/platform-tools
2. Extract ke folder mana saja, misal `C:\platform-tools`
3. Tambahkan folder itu ke **PATH** (Settings > System > About > Advanced
   system settings > Environment Variables > Path > New)
4. Buka Command Prompt/PowerShell baru, cek dengan `adb version`
5. Install driver USB HP kamu kalau Windows belum kenal device-nya saat
   disambungkan (biasanya driver resmi vendor, atau pakai
   [Universal ADB Driver](https://adb.clockworkmod.com/) sebagai alternatif
   generik) — ini langkah yang **tidak diperlukan di Linux** karena driver
   sudah built-in di kernel.

Python-nya sendiri tinggal install dari https://python.org (centang "Add
Python to PATH" saat instalasi), lalu jalankan pakai `python` (bukan
`python3`, karena default alias Windows).

### macOS

```bash
git clone <repo-url>
cd android-audit-tool

brew install android-platform-tools
pip3 install -r requirements.txt   # opsional, untuk export PDF
```

## Persiapan HP yang akan diaudit

1. Aktifkan **Developer Options**: Settings > About Phone > tap "Build Number" 7x.
2. Masuk ke Developer Options > aktifkan **USB Debugging**.
3. Sambungkan HP ke laptop via kabel USB.
4. Saat muncul pop-up di HP "Allow USB debugging?", tekan **Allow** (centang
   "Always allow from this computer" biar tidak muncul terus).
5. Verifikasi koneksi: `adb devices` → harus muncul status `device` (bukan
   `unauthorized` atau `offline`).

## Cara Pakai

> Di Windows ganti `python3` jadi `python` pada semua contoh di bawah.

```bash
python3 main.py                 # audit standar, simpan .txt + .json ke ./output
python3 main.py --pdf           # sekalian export .pdf
python3 main.py -s <serial>     # pilih device spesifik (lihat via `adb devices`)
python3 main.py -o ./laporan    # ganti folder output
python3 main.py --no-color      # matikan warna (misal saat redirect ke file)
python3 main.py --no-save       # tampilkan di terminal saja, tanpa simpan file
python3 main.py -v              # mode verbose (debug command adb mentah)
```

### Coba tanpa HP fisik (mode simulasi)

Untuk melihat contoh output tanpa perlu HP terhubung (mis. untuk demo/screenshot):

```bash
python3 test_mock.py
```

Script ini menjalankan seluruh logika audit dengan data ADB palsu (mock),
berguna juga untuk verifikasi instalasi berjalan normal.

## Struktur Proyek

```
android-audit-tool/
├── main.py           # entry point & orkestrasi CLI
├── adb_utils.py       # wrapper koneksi & eksekusi ADB (multi-device, caching)
├── checks.py           # semua logika indikator/pengecekan (10 kategori)
├── scoring.py           # perhitungan skor & grade kelayakan
├── report.py             # render terminal + simpan txt/json/pdf
├── test_mock.py            # simulasi audit tanpa device fisik
├── requirements.txt
└── output/                 # folder hasil laporan (dibuat otomatis)
```

## Tentang Indikasi Originalitas

Bagian "Indikasi Originalitas Komponen" **bukan alat forensik pasti**.
Tool ini hanya menyandingkan beberapa properti sistem (brand vs build
fingerprint, rasio cycle count terhadap wear baterai, dll) untuk mencari
ketidakkonsistenan yang *umumnya* muncul pada unit rebadge/clone atau
komponen aftermarket. Hasilnya selalu berupa indikasi awal — tetap lakukan
pengecekan fisik (segel, kualitas part, IMEI resmi via `*#06#` dicocokkan
dengan dus/invoice) sebelum mengambil keputusan final.

## Keterbatasan

- Sebagian properti (cycle count baterai, wear%, beberapa sensor) tidak
  selalu terbaca via ADB tanpa root tergantung kebijakan masing-masing OEM
  — tool akan menampilkan `N/A` dengan catatan, bukan error/crash.
- Pembacaan IMEI slot 2 (dual SIM) dan sebagian info modem dibatasi Google
  sejak Android 10+ untuk shell tanpa privilese sistem — disarankan cek
  manual via `*#06#`.
- Skor kelayakan adalah agregasi tertimbang sederhana untuk bantu keputusan
  cepat, bukan angka baku/ilmiah.

## Lisensi

MIT — silakan modifikasi sesuai kebutuhan.
