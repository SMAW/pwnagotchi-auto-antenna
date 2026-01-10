import logging
import os
import subprocess
import time
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
from flask import render_template_string, jsonify

MAC_FILE = "/etc/pwnagotchi/internal_wifi_mac"


class AutoAntenna(plugins.Plugin):
    __author__ = 'SMAW / Terminatoror'
    __version__ = '2.0.0'
    __license__ = 'MIT'
    __description__ = 'Automatically switches between internal and external WiFi adapters'

    def __init__(self):
        self.ready = False
        self.switching = False
        self.switch_count = 0
        self.last_switch_time = None

    def _get_mac(self, iface):
        """Get MAC address of an interface"""
        try:
            with open(f'/sys/class/net/{iface}/address', 'r') as f:
                return f.read().strip().lower()
        except:
            return None

    def _iface_exists(self, iface):
        """Check if interface exists"""
        return os.path.exists(f'/sys/class/net/{iface}')

    def _get_internal_mac(self):
        """Get stored internal MAC, or save current wlan0 MAC if first run"""
        if os.path.exists(MAC_FILE):
            with open(MAC_FILE, 'r') as f:
                return f.read().strip().lower()
        return None

    def _save_internal_mac(self, mac):
        """Save internal MAC to file"""
        try:
            os.makedirs(os.path.dirname(MAC_FILE), exist_ok=True)
            with open(MAC_FILE, 'w') as f:
                f.write(mac)
            logging.info(f"[auto-antenna] Saved internal MAC: {mac}")
        except Exception as e:
            logging.error(f"[auto-antenna] Failed to save MAC: {e}")

    def _is_using_internal(self):
        """Check if wlan0 is the internal adapter"""
        current_mac = self._get_mac("wlan0")
        stored_mac = self._get_internal_mac()

        if not current_mac:
            return True  # Assume internal if can't read

        if not stored_mac:
            # First run - save current MAC as internal if no external present
            if not self._iface_exists("wlan1"):
                self._save_internal_mac(current_mac)
                return True
            return False  # External might be wlan0

        return current_mac == stored_mac

    def _run_switch_script(self, to_external):
        """Execute interface switch in background"""
        script = "/tmp/auto_antenna_switch.sh"

        if to_external:
            commands = """#!/bin/bash
sleep 3
systemctl stop pwnagotchi
iw dev wlan0mon del 2>/dev/null
iw dev mon0 del 2>/dev/null
ip link set wlan0 down 2>/dev/null
ip link set wlan1 down 2>/dev/null
ip link set wlan0 name wlan_temp 2>/dev/null
ip link set wlan1 name wlan0 2>/dev/null
ip link set wlan0 up
ip link set wlan_temp down 2>/dev/null
systemctl start pwnagotchi
rm -- "$0"
"""
        else:
            commands = """#!/bin/bash
sleep 3
systemctl stop pwnagotchi
iw dev wlan0mon del 2>/dev/null
iw dev mon0 del 2>/dev/null
ip link set wlan0 down 2>/dev/null
if ip link show wlan_temp >/dev/null 2>&1; then
    ip link set wlan_temp name wlan0
elif ip link show wlan1 >/dev/null 2>&1; then
    ip link set wlan1 down
    ip link set wlan1 name wlan0
fi
ip link set wlan0 up
systemctl start pwnagotchi
rm -- "$0"
"""

        with open(script, 'w') as f:
            f.write(commands)
        os.chmod(script, 0o755)

        # Run detached from service
        subprocess.Popen(
            ["systemd-run", "--scope", "--unit=auto-antenna", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def on_loaded(self):
        logging.info("[auto-antenna] Plugin loaded")
        self.dry_run = self.options.get('dry_run', False)

        # Determine initial state
        if self._iface_exists("wlan_temp"):
            self.ready = True  # Already switched to external
            logging.info("[auto-antenna] External mode active (wlan_temp exists)")
        elif not self._is_using_internal():
            self.ready = True  # External adapter is on wlan0
            logging.info("[auto-antenna] External adapter detected on wlan0")
        else:
            self.ready = False  # Using internal
            logging.info("[auto-antenna] Internal adapter active")

    def on_ui_setup(self, ui):
        pos = (self.options.get('position_x', 180), self.options.get('position_y', 0))
        ui.add_element('antenna', LabeledValue(
            color=BLACK, label='', value='A:i',
            position=pos, label_font=fonts.Small, text_font=fonts.Small
        ))

    def on_ui_update(self, ui):
        label = self.options.get('label', 'A')
        status = self.options.get('external_text', 'e') if self.ready else self.options.get('internal_text', 'i')
        ui.set('antenna', f"{label}:{status}")

    def on_unload(self, ui):
        logging.info("[auto-antenna] Plugin unloaded")

    def on_epoch(self, agent, epoch, epoch_data):
        if self.switching:
            return

        interval = self.options.get('check_interval', 1)
        if epoch % interval != 0:
            return

        external_available = self._iface_exists("wlan1")
        using_internal = self._is_using_internal()

        # Case 1: Internal active, external plugged in -> switch to external
        if using_internal and external_available and not self.ready:
            logging.info("[auto-antenna] External adapter detected, switching...")
            self.switching = True
            if not self.dry_run:
                self._run_switch_script(to_external=True)
            self.ready = True
            self.switch_count += 1
            self.last_switch_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.switching = False

        # Case 2: External active but adapter removed -> switch to internal
        elif self.ready and not self._iface_exists("wlan0"):
            logging.info("[auto-antenna] External adapter removed, reverting...")
            self.switching = True
            if not self.dry_run:
                self._run_switch_script(to_external=False)
            self.ready = False
            self.switch_count += 1
            self.last_switch_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.switching = False

    def _get_iface_info(self, iface):
        """Get interface info: MAC, driver, device name"""
        info = {'name': iface, 'exists': self._iface_exists(iface), 'mac': None, 'driver': None, 'device': None}
        if not info['exists']:
            return info
        
        info['mac'] = self._get_mac(iface)
        
        # Get driver
        try:
            driver_path = f'/sys/class/net/{iface}/device/driver'
            if os.path.exists(driver_path):
                info['driver'] = os.path.basename(os.readlink(driver_path))
        except:
            pass
        
        # Get device name from uevent
        try:
            uevent_path = f'/sys/class/net/{iface}/device/uevent'
            if os.path.exists(uevent_path):
                with open(uevent_path, 'r') as f:
                    for line in f:
                        if line.startswith('PRODUCT=') or line.startswith('PCI_ID='):
                            info['device'] = line.split('=')[1].strip()
                            break
        except:
            pass
        
        return info

    def on_webhook(self, path, request):
        # Gather interface info
        interfaces = []
        for iface in ['wlan0', 'wlan1', 'wlan_temp', 'wlan0mon']:
            info = self._get_iface_info(iface)
            if info['exists']:
                interfaces.append(info)
        
        if path == "api" or path == "/api":
            return jsonify({
                'antenna': 'external' if self.ready else 'internal',
                'interfaces': interfaces,
                'switch_count': self.switch_count,
                'last_switch': self.last_switch_time or 'Never'
            })

        return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Auto Antenna</title>
    <style>
        body { font-family: monospace; background: #1a1a1a; color: #0f0; padding: 20px; }
        .box { background: #2a2a2a; padding: 15px; margin: 10px 0; border-left: 3px solid #0f0; }
        .iface { border-left-color: #0af; }
        .external { color: #fa0; }
        .internal { color: #0f0; }
        h1 { color: #0f0; }
        h2 { color: #0af; margin-top: 20px; }
        table { width: 100%; border-collapse: collapse; }
        td { padding: 5px 10px; }
        td:first-child { color: #888; width: 80px; }
    </style>
</head>
<body>
    <h1>📡 Auto Antenna</h1>
    <div class="box">
        <b>Status:</b> <span class="{{ 'external' if ready else 'internal' }}">{{ 'EXTERNAL' if ready else 'INTERNAL' }}</span>
    </div>
    <div class="box"><b>Switches:</b> {{ count }} | <b>Last:</b> {{ last }}</div>
    
    <h2>🔌 Interfaces</h2>
    {% for iface in interfaces %}
    <div class="box iface">
        <table>
            <tr><td>Name:</td><td><b>{{ iface.name }}</b></td></tr>
            <tr><td>MAC:</td><td>{{ iface.mac or 'N/A' }}</td></tr>
            <tr><td>Driver:</td><td>{{ iface.driver or 'N/A' }}</td></tr>
            <tr><td>Device:</td><td>{{ iface.device or 'N/A' }}</td></tr>
        </table>
    </div>
    {% endfor %}
    
    <p style="color:#666; margin-top:20px; font-size:12px;">Refresh page to update</p>
</body>
</html>
        """, ready=self.ready, interfaces=interfaces, count=self.switch_count, 
            last=self.last_switch_time or 'Never')
