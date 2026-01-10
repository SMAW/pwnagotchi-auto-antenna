import logging
import os
import subprocess
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
from flask import render_template_string, jsonify

# Raspberry Pi Foundation MAC address prefixes (OUI)
RPI_MAC_PREFIXES = (
    'b8:27:eb',  # RPi older models
    'dc:a6:32',  # RPi 4
    'e4:5f:01',  # RPi 4
    'd8:3a:dd',  # RPi newer
    '2c:cf:67',  # RPi 5
)


class AutoAntenna(plugins.Plugin):
    __author__ = 'SMAW / Terminatoror'
    __version__ = '0.3.0'
    __license__ = 'MIT'
    __description__ = 'Detects and displays which WiFi antenna is in use via iw dev'

    def __init__(self):
        self.is_external = False
        self.current_phy = None
        self.monitor_iface = None

    def _is_rpi_mac(self, mac):
        """Check if MAC address belongs to Raspberry Pi"""
        if not mac:
            return False
        return mac.lower().startswith(RPI_MAC_PREFIXES)

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

    def _get_driver(self, iface):
        """Get driver name for interface"""
        try:
            driver_path = f'/sys/class/net/{iface}/device/driver'
            if os.path.exists(driver_path):
                return os.path.basename(os.readlink(driver_path))
        except:
            pass
        return None

    def _parse_iw_dev(self):
        """Parse iw dev output to get interface to phy mapping"""
        try:
            result = subprocess.run(['iw', 'dev'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return {}

            iface_to_phy = {}
            current_phy = None

            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('phy#'):
                    current_phy = line
                elif line.startswith('Interface ') and current_phy:
                    iface_name = line.split()[1]
                    iface_to_phy[iface_name] = current_phy

            return iface_to_phy
        except Exception as e:
            logging.error(f"[auto-antenna] Failed to parse iw dev: {e}")
            return {}

    def _detect_antenna(self):
        """Detect antenna using iw dev to check which phy the monitor interface uses"""
        # Get interface to phy mapping
        iface_to_phy = self._parse_iw_dev()

        # Find monitor interface
        monitor_iface = None
        for iface in ['wlan0mon', 'wlan1mon', 'wlan2mon']:
            if iface in iface_to_phy:
                monitor_iface = iface
                break

        if not monitor_iface:
            logging.warning("[auto-antenna] No monitor interface found")
            return False

        self.monitor_iface = monitor_iface
        monitor_phy = iface_to_phy[monitor_iface]
        self.current_phy = monitor_phy

        # Check all managed interfaces to find which one shares the same phy
        same_phy_ifaces = []
        for iface, phy in iface_to_phy.items():
            if phy == monitor_phy and 'mon' not in iface:
                same_phy_ifaces.append(iface)

        if not same_phy_ifaces:
            logging.warning(f"[auto-antenna] No managed interface found for {monitor_phy}")
            return False

        # Get MAC of the managed interface that shares the phy
        managed_iface = same_phy_ifaces[0]  # Take first one
        mac = self._get_mac(managed_iface)

        # Check if it's RPi internal MAC
        self.is_external = not self._is_rpi_mac(mac)

        antenna_type = "EXTERNAL" if self.is_external else "INTERNAL"
        logging.info(f"[auto-antenna] Monitor {monitor_iface} ({monitor_phy}) -> {managed_iface} (MAC: {mac}) -> {antenna_type}")

        return True

    def _get_band(self):
        """Get current frequency band (2.4/5/6 GHz)"""
        try:
            if not self.monitor_iface:
                return '?'

            result = subprocess.run(
                ['iw', self.monitor_iface, 'info'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'channel' in line.lower() and 'mhz' in line.lower():
                        # Extract frequency
                        parts = line.split()
                        for i, p in enumerate(parts):
                            if 'MHz' in p or (p.isdigit() and int(p) > 2000):
                                try:
                                    freq = int(parts[i-1]) if 'MHz' in p else int(p)
                                    if freq < 3000:
                                        return '2.4'
                                    elif freq < 6000:
                                        return '5'
                                    else:
                                        return '6'
                                except:
                                    pass
        except:
            pass
        return '?'

    def on_loaded(self):
        logging.info("[auto-antenna] Plugin loaded (v0.3.0)")
        self._detect_antenna()
        status = "EXTERNAL" if self.is_external else "INTERNAL"
        logging.info(f"[auto-antenna] Using: {status} adapter")

    def on_ui_setup(self, ui):
        pos = (self.options.get('position_x', 180), self.options.get('position_y', 0))
        ui.add_element('antenna', LabeledValue(
            color=BLACK, label='', value='A:i',
            position=pos, label_font=fonts.Small, text_font=fonts.Small
        ))

    def on_ui_update(self, ui):
        label = self.options.get('label', 'A')
        band = self._get_band()

        if self.is_external:
            status = self.options.get('external_text', 'e')
        else:
            status = self.options.get('internal_text', 'i')

        ui.set('antenna', f"{label}:{status}{band}")

    def on_unload(self, ui):
        logging.info("[auto-antenna] Plugin unloaded")

    def on_epoch(self, agent, epoch, epoch_data):
        # Refresh detection periodically
        interval = self.options.get('check_interval', 5)
        if epoch % interval == 0:
            self._detect_antenna()

    def on_webhook(self, path, request):
        iface_to_phy = self._parse_iw_dev()

        info = {
            'antenna': 'external' if self.is_external else 'internal',
            'monitor_interface': self.monitor_iface,
            'phy': self.current_phy,
            'band': self._get_band(),
            'interfaces': iface_to_phy
        }

        if path == "api" or path == "/api":
            return jsonify(info)

        return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Auto Antenna</title>
    <style>
        body { font-family: monospace; background: #1a1a1a; color: #0f0; padding: 20px; }
        .box { background: #2a2a2a; padding: 15px; margin: 10px 0; border-left: 3px solid #0f0; }
        .external { color: #fa0; }
        .internal { color: #0f0; }
        h1 { color: #0f0; }
        b { color: #888; }
        pre { background: #111; padding: 10px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>📡 Auto Antenna v0.3</h1>
    <div class="box">
        <b>Antenna:</b> <span class="{{ 'external' if is_external else 'internal' }}">{{ 'EXTERNAL' if is_external else 'INTERNAL' }}</span>
    </div>
    <div class="box"><b>Monitor Interface:</b> {{ monitor_iface or 'N/A' }}</div>
    <div class="box"><b>PHY:</b> {{ phy or 'N/A' }}</div>
    <div class="box"><b>Band:</b> {{ band }} GHz</div>

    <div class="box">
        <b>Interface Mapping:</b>
        <pre>{% for iface, phy in interfaces.items() %}{{ iface }} → {{ phy }}
{% endfor %}</pre>
    </div>
</body>
</html>
        """, is_external=self.is_external,
            monitor_iface=self.monitor_iface,
            phy=self.current_phy,
            band=info['band'],
            interfaces=info['interfaces'])
