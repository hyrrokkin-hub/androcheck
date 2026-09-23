# Android Used-Phone Audit Tool

*[Baca dalam Bahasa Indonesia](README.id.md)*

A Python CLI tool to help audit the condition of a used Android phone
before you buy it, using ADB (Android Debug Bridge). Runs on Linux,
Windows, and macOS, and is generic across brands (Samsung, Xiaomi, Oppo,
Vivo, Realme, Pixel, etc.) with automatic fallback for vendor-specific
properties.

> **Note:** This tool was built for the Indonesian used-phone market, so
> **all CLI output, report labels, and code comments are in Indonesian**
> (e.g. "Siklus Pengisian" = charge cycles, "Kode Region/CSC" checks the
> Indonesian SEIN/legal-import registration). This README is in English
> for discoverability, but the tool itself is not currently
> internationalized. Contributions adding an `--lang en` option are
> welcome.

> **Also note:** screen, camera, and other physical conditions still need
> to be checked manually. This tool focuses on data retrievable via ADB:
> device identity, IMEI, CPU/RAM, storage, battery, thermal behavior,
> system integrity (root/bootloader/Knox), and component-originality
> indicators based on system-data consistency.

## Features

- **10 audit categories**: device identity, IMEI & connectivity, CPU/RAM,
  storage, display, battery (including estimated wear% from
  charge_full vs charge_full_design), thermal & throttling, sensors,
  system integrity (root/bootloader/Knox), and component-originality
  indicators.
- **Automatic A–D condition score/grade** at the end of the report, with a
  list of red flags worth asking the seller about.
- **Generic across brands** — each indicator tries several
  command/path fallbacks so it doesn't fail when one vendor doesn't
  expose a given property.
- **Output**: colored terminal, `.txt` file, `.json` file, and optional
  `.pdf` export.
- **Multi-device support**: if more than one phone is connected, the tool
  will prompt you to pick one.
- No external dependencies for core features (pure Python standard
  library).

## Installation

The core tool only uses the Python standard library, so it runs on
**Linux, Windows, and macOS** without any code changes — the only
difference is how you install `adb` and the USB driver.

### Linux (Pop!_OS/Ubuntu/Debian)

```bash
git clone <repo-url>
cd android-audit-tool

sudo apt install android-tools-adb
pip install -r requirements.txt --break-system-packages   # optional, for PDF export
```

### Windows

```powershell
git clone <repo-url>
cd android-audit-tool

pip install -r requirements.txt   # optional: fpdf2 (PDF) + colorama (colors in cmd.exe)
```

For `adb` on Windows:
1. Download **SDK Platform-Tools for Windows** from
   https://developer.android.com/tools/releases/platform-tools
2. Extract it anywhere, e.g. `C:\platform-tools`
3. Add that folder to your **PATH** (Settings > System > About > Advanced
   system settings > Environment Variables > Path > New)
4. Open a new Command Prompt/PowerShell and verify with `adb version`
5. Install the USB driver for your phone if Windows doesn't recognize the
   device when connected (usually the vendor's official driver, or the
   generic [Universal ADB Driver](https://adb.clockworkmod.com/)) — this
   step is **not needed on Linux**, since the driver is already built
   into the kernel.

Install Python itself from https://python.org (check "Add Python to
PATH" during setup), then run commands with `python` (not `python3`,
since that's the default alias on Windows).

### macOS

```bash
git clone <repo-url>
cd android-audit-tool

brew install android-platform-tools
pip3 install -r requirements.txt   # optional, for PDF export
```

## Preparing the phone to be audited

1. Enable **Developer Options**: Settings > About Phone > tap "Build
   Number" 7 times.
2. Go to Developer Options > enable **USB Debugging**.
3. Connect the phone to your computer via USB cable.
4. When the "Allow USB debugging?" popup appears on the phone, tap
   **Allow** (check "Always allow from this computer" so it doesn't
   prompt again).
5. Verify the connection: `adb devices` → should show status `device`
   (not `unauthorized` or `offline`).

## Usage

> On Windows, replace `python3` with `python` in every example below.

```bash
python3 main.py                 # standard audit, saves .txt + .json to ./output
python3 main.py --pdf           # also export .pdf
python3 main.py -s <serial>     # target a specific device (see `adb devices`)
python3 main.py -o ./report     # change the output folder
python3 main.py --no-color      # disable terminal colors (e.g. when redirecting to a file)
python3 main.py --no-save       # print to terminal only, don't save files
python3 main.py -v              # verbose mode (prints raw adb command output)
```

### Try it without a physical phone (mock mode)

To see sample output without a phone connected (e.g. for a demo or
screenshot):

```bash
python3 test_mock.py
```

This script runs the entire audit logic against fake (mocked) ADB
responses. It's also useful for verifying your installation works.

## Project Structure

```
android-audit-tool/
├── main.py           # entry point & CLI orchestration
├── adb_utils.py       # ADB connection/execution wrapper (multi-device, caching)
├── checks.py           # all indicator/check logic (10 categories)
├── scoring.py           # condition score & grade calculation
├── report.py             # terminal rendering + txt/json/pdf export
├── test_mock.py            # audit simulation without a physical device
├── requirements.txt
└── output/                 # generated reports folder (auto-created)
```

## About the Originality Indicators

The "Component Originality Indicators" section is **not a forensic
tool**. It only cross-references a handful of system properties (brand
vs. build fingerprint, charge-cycle count vs. battery wear ratio, etc.)
to look for inconsistencies that *commonly* appear on rebadged/cloned
units or aftermarket components. Results are always a preliminary
indicator — you should still do a physical inspection (seals, part
quality, matching the official IMEI via `*#06#` against the box/invoice)
before making a final decision.

## Limitations

- Some properties (battery cycle count, wear%, some sensors) aren't
  always readable via ADB without root, depending on OEM policy — the
  tool will show `N/A` with a note instead of erroring/crashing.
- Reading the second IMEI slot (dual SIM) and some modem info has been
  restricted by Google since Android 10+ for shell access without
  system-level privileges — manual verification via `*#06#` is
  recommended.
- The condition score is a simple weighted aggregate to help with quick
  decisions, not a rigorous or scientific measurement.

## License

MIT — feel free to modify as needed.
