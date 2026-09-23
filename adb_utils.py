#!/usr/bin/env python3
"""
adb_utils.py
Wrapper tipis di atas ADB CLI: deteksi perangkat, eksekusi shell command
dengan cache, dan penanganan multi-device.

Didesain portable: hanya bergantung pada binary `adb` yang ada di PATH
(Android Platform Tools), tidak butuh root di HP target untuk sebagian
besar command (beberapa command sensor/sysfs mungkin butuh akses yang
tidak selalu tersedia tergantung OEM/versi Android -> ditangani graceful).
"""

import shutil
import subprocess
import sys
from typing import Dict, List, Optional


class AdbNotFoundError(Exception):
    pass


class NoDeviceError(Exception):
    pass


class AdbSession:
    """Merepresentasikan satu sesi audit ke satu perangkat Android."""

    def __init__(self, serial: Optional[str] = None, timeout: int = 10, verbose: bool = False):
        self.timeout = timeout
        self.verbose = verbose
        self._cache: Dict[str, str] = {}
        self.adb_path = self._find_adb()
        self.serial = serial or self._auto_select_device()

    # ------------------------------------------------------------
    @staticmethod
    def _find_adb() -> str:
        adb_path = shutil.which("adb")
        if not adb_path:
            raise AdbNotFoundError(
                "Binary 'adb' tidak ditemukan di PATH.\n"
                "Install Android Platform Tools terlebih dahulu, contoh (Linux):\n"
                "  sudo apt install android-tools-adb\n"
                "atau download manual dari https://developer.android.com/tools/releases/platform-tools"
            )
        return adb_path

    def list_devices(self) -> List[str]:
        """Mengembalikan list serial number perangkat yang berstatus 'device' (siap dipakai)."""
        result = subprocess.run(
            [self.adb_path, "devices"],
            capture_output=True, text=True, timeout=self.timeout
        )
        devices = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices"):
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
        return devices

    def _auto_select_device(self) -> str:
        devices = self.list_devices()
        if not devices:
            raise NoDeviceError(
                "Perangkat tidak ditemukan / belum authorized!\n"
                "  1. Pastikan kabel USB terhubung dengan baik.\n"
                "  2. Aktifkan 'USB Debugging' di Settings > Developer Options.\n"
                "  3. Cek layar HP, tekan 'Allow/Izinkan' pada pop-up USB Debugging (centang 'Always allow').\n"
                "  4. Jalankan 'adb devices' manual untuk memastikan status 'device' (bukan 'unauthorized')."
            )
        if len(devices) == 1:
            return devices[0]
        # Multi-device -> minta user pilih
        print(f"\n[!] Ditemukan {len(devices)} perangkat terhubung:")
        for i, d in enumerate(devices, 1):
            print(f"    {i}. {d}")
        while True:
            choice = input(f"Pilih perangkat yang akan diaudit (1-{len(devices)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(devices):
                return devices[int(choice) - 1]
            print("Input tidak valid, coba lagi.")

    # ------------------------------------------------------------
    def shell(self, command: str, use_cache: bool = True) -> str:
        """Menjalankan `adb -s <serial> shell <command>` dan mengembalikan stdout (stripped)."""
        if use_cache and command in self._cache:
            return self._cache[command]
        try:
            result = subprocess.run(
                [self.adb_path, "-s", self.serial, "shell", command],
                capture_output=True, text=True, timeout=self.timeout
            )
            output = result.stdout.strip()
            if self.verbose:
                print(f"    [debug] $ {command}\n    [debug] -> {output[:200]!r}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            output = ""
        except Exception:
            output = ""
        if use_cache:
            self._cache[command] = output
        return output

    def shell_first_match(self, commands: List[str]) -> str:
        """Mencoba beberapa command berurutan (untuk fallback multi-vendor),
        mengembalikan output non-kosong pertama yang ditemukan."""
        for cmd in commands:
            out = self.shell(cmd)
            if out:
                return out
        return ""

    def getprop(self, key: str) -> str:
        return self.shell(f"getprop {key}")
