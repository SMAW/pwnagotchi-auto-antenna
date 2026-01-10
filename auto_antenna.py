import logging
import os
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
from flask import render_template_string, jsonify

MAC_FILE = "/etc/pwnagotchi/internal_wifi_mac"

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
    __version__ = '0.1.0'
    __license__ = 'MIT'
    __description__ = 'Shows which WiFi antenna and band is currently in use'

    def __init__(self):
        self.is_external = False
        self.mac_warning = None  # Warning message if stored MAC looks wrong
        self.config_warning = None  # Warning if pwnagotchi config doesn't match

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

    def _get_mon_parent(self, mon_iface):
        """Get the parent interface of a monitor interface by matching MAC"""
        mon_mac = self._get_mac(mon_iface)
        if not mon_mac:
            return None

        # Check common interface names
        for iface in ['wlan0', 'wlan1', 'wlan2']:
            if self._iface_exists(iface) and self._get_mac(iface) == mon_mac:
                return iface
        return None

    def _check_pwnagotchi_config(self, agent):
        """Check if pwnagotchi is using the expected interface"""
        try:
            # Get configured interface from agent
            config_iface = agent.config().get('main', {}).get('iface', 'wlan0mon')

            # Check if external adapter exists (wlan1)
            external_exists = self._iface_exists('wlan1')

            # Get parent of the configured monitor interface
            if 'mon' in config_iface:
                parent = self._get_mon_parent(config_iface)
                if parent:
                    parent_mac = self._get_mac(parent)
                    is_parent_rpi = self._is_rpi_mac(parent_mac)

                    # Warn if external exists but we're using internal
                    if external_exists and is_parent_rpi:
                        self.config_warning = "EXT avail,using INT"
                        logging.warning(f"[auto-antenna] External adapter (wlan1) available but using internal ({config_iface})")
                        return

            self.config_warning = None
        except Exception as e:
            logging.debug(f"[auto-antenna] Config check failed: {e}")

    def _get_band(self):
        """Get current frequency band (2.4/5/6 GHz)"""
        try:
            # Check wlan0mon first, then wlan0
            iface = 'wlan0mon' if self._iface_exists('wlan0mon') else 'wlan0'

            # Try to get frequency from iw
            import subprocess
            result = subprocess.run(
                ['iw', iface, 'info'],
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

    def _detect_antenna(self):
        """Detect if using internal or external antenna"""
        # Find the active interface (wlan0 or wlan0mon)
        iface = 'wlan0mon' if self._iface_exists('wlan0mon') else 'wlan0'
        base_iface = iface.replace('mon', '')

        if not self._iface_exists(base_iface):
            return False

        current_mac = self._get_mac(base_iface)

        # Check stored internal MAC
        if os.path.exists(MAC_FILE):
            with open(MAC_FILE, 'r') as f:
                stored_mac = f.read().strip().lower()

            # Validate stored MAC is actually a Raspberry Pi MAC
            if not self._is_rpi_mac(stored_mac):
                self.mac_warning = "WARN:stored MAC not RPi!"
                logging.warning(f"[auto-antenna] Stored MAC {stored_mac} is NOT a Raspberry Pi MAC!")
                logging.warning("[auto-antenna] Delete /etc/pwnagotchi/internal_wifi_mac and restart without external adapter")
            else:
                self.mac_warning = None

            self.is_external = (current_mac != stored_mac)
        else:
            # First run - save current MAC as internal (assuming no external on first boot)
            if current_mac:
                # Check if current MAC is actually a Raspberry Pi MAC
                if not self._is_rpi_mac(current_mac):
                    self.mac_warning = "WARN:ext on 1st boot?"
                    logging.warning(f"[auto-antenna] Current MAC {current_mac} is NOT a Raspberry Pi MAC!")
                    logging.warning("[auto-antenna] External adapter may be connected - remove it and restart")
                else:
                    self.mac_warning = None
                    try:
                        os.makedirs(os.path.dirname(MAC_FILE), exist_ok=True)
                        with open(MAC_FILE, 'w') as f:
                            f.write(current_mac)
                        logging.info(f"[auto-antenna] Saved internal MAC: {current_mac}")
                    except Exception as e:
                        logging.error(f"[auto-antenna] Failed to save MAC: {e}")
            self.is_external = False

        return True

    def on_loaded(self):
        logging.info("[auto-antenna] Plugin loaded")
        self._detect_antenna()
        status = "EXTERNAL" if self.is_external else "INTERNAL"
        logging.info(f"[auto-antenna] Detected: {status} adapter")

    def on_ui_setup(self, ui):
        pos = (self.options.get('position_x', 180), self.options.get('position_y', 0))
        ui.add_element('antenna', LabeledValue(
            color=BLACK, label='', value='A:i',
            position=pos, label_font=fonts.Small, text_font=fonts.Small
        ))

    def on_ui_update(self, ui):
        # Show warning if MAC looks wrong (highest priority)
        if self.mac_warning:
            ui.set('antenna', self.mac_warning)
            return

        # Show config warning if external available but not used
        if self.config_warning:
            ui.set('antenna', self.config_warning)
            return

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
            self._check_pwnagotchi_config(agent)

    def on_webhook(self, path, request):
        iface = 'wlan0mon' if self._iface_exists('wlan0mon') else 'wlan0'
        base_iface = iface.replace('mon', '')

        info = {
            'antenna': 'external' if self.is_external else 'internal',
            'interface': iface,
            'mac': self._get_mac(base_iface),
            'driver': self._get_driver(base_iface),
            'band': self._get_band()
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
    </style>
</head>
<body>
    <h1>📡 Auto Antenna v0.1</h1>
    <div class="box">
        <b>Antenna:</b> <span class="{{ 'external' if is_external else 'internal' }}">{{ 'EXTERNAL' if is_external else 'INTERNAL' }}</span>
    </div>
    <div class="box"><b>Interface:</b> {{ iface }}</div>
    <div class="box"><b>MAC:</b> {{ mac or 'N/A' }}</div>
    <div class="box"><b>Driver:</b> {{ driver or 'N/A' }}</div>
    <div class="box"><b>Band:</b> {{ band }} GHz</div>
</body>
</html>
        """, is_external=self.is_external, iface=iface,
            mac=info['mac'], driver=info['driver'], band=info['band'])
