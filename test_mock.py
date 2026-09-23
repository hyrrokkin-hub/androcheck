#!/usr/bin/env python3
"""Simulasi audit dengan data adb palsu (mock) untuk menguji logic tanpa device fisik."""
import sys
sys.path.insert(0, ".")

import checks
import scoring
import report

MOCK_PROPS = {
    "ro.product.brand": "samsung",
    "ro.product.manufacturer": "samsung",
    "ro.product.model": "SM-S911B",
    "ro.product.device": "dm3q",
    "ro.build.version.release": "14",
    "ro.build.version.sdk": "34",
    "ro.build.version.security_patch": "2024-11-01",
    "ro.build.display.id": "UP1A.231005.007.S911BXXS5DXH1",
    "ro.build.type": "user",
    "ro.build.fingerprint": "samsung/dm3qxxx/dm3q:14/UP1A/S911BXXS5DXH1:user/release-keys",
    "ro.boot.serialno": "R5CT12ABCDE",
    "ro.csc.sales_code": "XID",
    "ro.board.platform": "kalama",
    "ro.hardware": "qcom",
    "ro.product.cpu.abi": "arm64-v8a",
    "ro.boot.verifiedbootstate": "green",
    "ro.build.tags": "release-keys",
    "ro.boot.warranty_bit": "0",
    "ro.product.first_api_level": "34",
}

MOCK_SHELL = {
    "service call iphonesubinfo 1 | cut -c 52-66 | tr -d '.[:space:]'": "353456789012345",
    "gsm.version.baseband": "",
    "cat /sys/class/net/wlan0/address": "aa:bb:cc:dd:ee:ff",
    "settings get secure bluetooth_address": "11:22:33:44:55:66",
    "nproc 2>/dev/null || grep -c ^processor /proc/cpuinfo": "8",
    "cat /proc/meminfo": "MemTotal:        8144556 kB\nMemAvailable:    3221000 kB\n",
    "df -k /data | tail -n 1": "/dev/block/dm-8 246218000 102000000 144218000 42% /data",
    "wm size": "Physical size: 1080x2340",
    "wm density": "Physical density: 420",
    "dumpsys display | grep -iE 'refreshRate|peakRefreshRate' | head -n 5": "mRefreshRate=120.0",
    "dumpsys battery": (
        "Current Battery Service state:\n  AC powered: false\n  USB powered: true\n"
        "  present: true\n  level: 87\n  scale: 100\n  voltage: 4123\n  temperature: 312\n"
        "  health: 2\n  technology: Li-ion\n  status: 2\n"
    ),
    "cat /sys/class/power_supply/battery/cycle_count": "142",
    "cat /sys/class/power_supply/battery/charge_full": "4750000",
    "cat /sys/class/power_supply/battery/charge_full_design": "5000000",
    "uptime": "up time: 3 days, 4:12:05",
    "getprop ro.boot.bootreason": "reboot",
    "cat /sys/class/thermal/thermal_zone0/temp": "36500",
    "cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq 2>/dev/null": "3200000",
    "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null": "1900000",
    "cat /sys/devices/system/cpu/online 2>/dev/null": "0-7",
    "dumpsys sensorservice | grep -iE '^\\s*[0-9]+\\)' | head -n 40": "accelerometer gyroscope proximity light magnetic",
    "dumpsys battery | grep -i current": "current now: 350000",
    "which su": "",
    "pm list packages | grep -i magisk": "",
}


class MockAdb:
    serial = "MOCKSERIAL123"

    def getprop(self, key):
        return MOCK_PROPS.get(key, "")

    def shell(self, cmd, use_cache=True):
        return MOCK_SHELL.get(cmd, "")

    def shell_first_match(self, cmds):
        for c in cmds:
            out = self.shell(c)
            if out:
                return out
        return ""


def main():
    adb = MockAdb()
    sections = []
    all_rows = []

    def add(title, rows):
        sections.append({"title": title, "rows": rows})
        all_rows.extend(rows)

    add("IDENTITAS PERANGKAT & REGION", checks.check_identity(adb))
    add("IMEI & KONEKTIVITAS", checks.check_connectivity(adb))
    add("SPESIFIKASI PROSESOR & MEMORI (RAM)", checks.check_cpu_ram(adb))
    add("KAPASITAS PENYIMPANAN (STORAGE)", checks.check_storage(adb))
    add("SPESIFIKASI & INTEGRITAS LAYAR", checks.check_display(adb))

    batt_rows, batt_extra = checks.check_battery(adb)
    add("AUDIT BATERAI & DAYA", batt_rows)

    thermal_rows, thermal_extra = checks.check_thermal(adb, batt_extra)
    add("BEBAN THERMAL & DETEKSI PENGGUNAAN EKSTREM", thermal_rows)

    add("AUDIT MESIN & SENSOR", checks.check_hardware_sensors(adb))
    add("INTEGRITAS SISTEM & GARANSI (ROOT/BOOTLOADER)", checks.check_system_integrity(adb, "samsung"))
    add("INDIKASI ORIGINALITAS KOMPONEN", checks.check_originality(adb, batt_extra))

    score, grade, desc, summary = scoring.compute_score(all_rows)
    text = report.render_terminal(sections, summary, use_color=False)

    # Test save functions
    import os
    os.makedirs("test_output", exist_ok=True)
    txt_path = report.save_txt(text, "test_output", "mock_test")
    json_path = report.save_json(sections, summary, {"brand": "samsung", "model": "SM-S911B"}, "test_output", "mock_test")
    print(f"\n[TEST] Saved: {txt_path}, {json_path}")

    pdf_path = report.save_pdf(sections, summary, {"brand": "samsung", "model": "SM-S911B"}, "test_output", "mock_test")
    print(f"[TEST] PDF: {pdf_path}")


if __name__ == "__main__":
    main()
