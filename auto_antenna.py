import logging
import os
import subprocess
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
from flask import render_template_string, jsonify
import time


class AutoAntenna(plugins.Plugin):
    __author__ = 'SMAW / Terminatoror'
    __version__ = '1.1.0'
    __license__ = 'MIT'
    __description__ = 'Automatically switches between internal and external WiFi adapters with screen display and web interface'

    def __init__(self):
        self.current_antenna = "internal"
        self.previous_state = None
        self.switching = False
        self.device_info = {}
        self.last_switch_time = None
        self.switch_count = 0

    def on_loaded(self):
        logging.info("[auto-antenna] Plugin loaded")

        # Check if we are already in external mode (wlan_temp exists)
        if self._interface_exists("wlan_temp"):
             self.current_antenna = "external"
             logging.info("[auto-antenna] Detected existing external adapter configuration (wlan_temp exists)")

        # Get initial device info and state
        self._update_device_info()
        self.check_and_switch()

    def on_ui_setup(self, ui):
        # Get position and display config from options
        pos_x = self.options.get('position_x', 180)
        pos_y = self.options.get('position_y', 0)
        label_text = self.options.get('label', 'A')

        # Add antenna status to the UI
        ui.add_element('antenna', LabeledValue(
            color=BLACK,
            label=f'{label_text}:' if label_text else '',
            value='i',
            position=(pos_x, pos_y),
            label_font=fonts.Small,
            text_font=fonts.Small))

    def on_ui_update(self, ui):
        # Get display values from config
        int_text = self.options.get('internal_text', 'i')
        ext_text = self.options.get('external_text', 'e')

        # Update the antenna display
        if self.current_antenna == "external":
            ui.set('antenna', ext_text)
        else:
            ui.set('antenna', int_text)

    def on_unload(self, ui):
        logging.info("[auto-antenna] Plugin unloaded")

    def on_epoch(self, agent, epoch, epoch_data):
        # Check and switch adapters periodically
        check_interval = self.options.get('check_interval', 1)

        if epoch % check_interval == 0 and not self.switching:
            self.check_and_switch()

    def on_webhook(self, path, request):
        """Provide web interface for antenna status"""

        if path == "/" or not path:
            # Main status page
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Auto Antenna Status</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {
                        font-family: monospace;
                        margin: 20px;
                        background: #1a1a1a;
                        color: #00ff00;
                    }
                    .container { max-width: 800px; margin: 0 auto; }
                    .status {
                        font-size: 24px;
                        margin: 20px 0;
                        padding: 20px;
                        background: #2a2a2a;
                        border: 2px solid #00ff00;
                        border-radius: 5px;
                    }
                    .info {
                        margin: 10px 0;
                        padding: 15px;
                        background: #2a2a2a;
                        border-left: 3px solid #00ff00;
                    }
                    .label { color: #00aaff; font-weight: bold; }
                    .external { color: #ffaa00; }
                    .internal { color: #00ff00; }
                    h1 { color: #00ff00; }
                    .refresh { margin: 20px 0; }
                    button {
                        background: #00ff00;
                        color: #1a1a1a;
                        border: none;
                        padding: 10px 20px;
                        font-family: monospace;
                        font-size: 14px;
                        cursor: pointer;
                        border-radius: 3px;
                    }
                    button:hover { background: #00aa00; }
                </style>
                <script>
                    function refreshData() {
                        fetch('/plugins/auto_antenna/api')
                            .then(r => r.json())
                            .then(data => {
                                document.getElementById('status').innerHTML =
                                    '<span class="' + data.antenna + '">' +
                                    data.antenna.toUpperCase() + '</span>';
                                document.getElementById('device').textContent = data.device_name;
                                document.getElementById('mac').textContent = data.mac_address;
                                document.getElementById('driver').textContent = data.driver;
                                document.getElementById('chipset').textContent = data.chipset;
                                document.getElementById('switches').textContent = data.switch_count;
                                document.getElementById('last_switch').textContent = data.last_switch;
                            });
                    }
                    setInterval(refreshData, 5000);
                </script>
            </head>
            <body>
                <div class="container">
                    <h1>🔌 Auto Antenna Status</h1>

                    <div class="status">
                        <span class="label">Current Antenna:</span>
                        <span id="status" class="{{ antenna }}">{{ antenna|upper }}</span>
                    </div>

                    <div class="info">
                        <span class="label">Device Name:</span> <span id="device">{{ device_name }}</span>
                    </div>

                    <div class="info">
                        <span class="label">MAC Address:</span> <span id="mac">{{ mac_address }}</span>
                    </div>

                    <div class="info">
                        <span class="label">Driver:</span> <span id="driver">{{ driver }}</span>
                    </div>

                    <div class="info">
                        <span class="label">Chipset:</span> <span id="chipset">{{ chipset }}</span>
                    </div>

                    <div class="info">
                        <span class="label">Total Switches:</span> <span id="switches">{{ switch_count }}</span>
                    </div>

                    <div class="info">
                        <span class="label">Last Switch:</span> <span id="last_switch">{{ last_switch }}</span>
                    </div>

                    <div class="refresh">
                        <button onclick="refreshData()">🔄 Refresh Now</button>
                    </div>

                    <p style="color: #666; font-size: 12px;">Auto-refreshes every 5 seconds</p>
                </div>
            </body>
            </html>
            """

            self._update_device_info()

            return render_template_string(html,
                antenna=self.current_antenna,
                device_name=self.device_info.get('name', 'Unknown'),
                mac_address=self.device_info.get('mac', 'Unknown'),
                driver=self.device_info.get('driver', 'Unknown'),
                chipset=self.device_info.get('chipset', 'Unknown'),
                switch_count=self.switch_count,
                last_switch=self.last_switch_time if self.last_switch_time else 'Never'
            )

        elif path == "api":
            # JSON API endpoint
            self._update_device_info()

            return jsonify({
                'antenna': self.current_antenna,
                'device_name': self.device_info.get('name', 'Unknown'),
                'mac_address': self.device_info.get('mac', 'Unknown'),
                'driver': self.device_info.get('driver', 'Unknown'),
                'chipset': self.device_info.get('chipset', 'Unknown'),
                'switch_count': self.switch_count,
                'last_switch': self.last_switch_time if self.last_switch_time else 'Never',
                'switching': self.switching
            })

    def check_and_switch(self):
        """Check if wlan1 exists and switch if needed"""
        try:
            # Check if wlan1 (external adapter) exists
            wlan1_exists = self._interface_exists("wlan1")

            # Determine current state
            if wlan1_exists and self.current_antenna != "external":
                logging.info("[auto-antenna] External WiFi detected, switching...")
                self._switch_to_external()

            elif not wlan1_exists and self.current_antenna == "external":
                logging.info("[auto-antenna] External WiFi removed, reverting to internal...")
                self._switch_to_internal()

        except Exception as e:
            logging.error(f"[auto-antenna] Error checking/switching: {e}")

    def _update_device_info(self):
        """Get current WiFi device information"""
        try:
            interface = "wlan0"

            # Validate interface name (alphanumeric only for security)
            if not interface.replace('_', '').isalnum():
                logging.error(f"[auto-antenna] Invalid interface name: {interface}")
                return

            # Get MAC address
            mac_result = subprocess.run(
                ['cat', f'/sys/class/net/{interface}/address'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if mac_result.returncode == 0:
                self.device_info['mac'] = mac_result.stdout.strip()
                logging.info(f"[auto-antenna] Device MAC: {self.device_info['mac']}")

            # Get driver info
            try:
                driver_link = os.readlink(f'/sys/class/net/{interface}/device/driver')
                self.device_info['driver'] = os.path.basename(driver_link)
                logging.info(f"[auto-antenna] Device Driver: {self.device_info['driver']}")
            except (OSError, FileNotFoundError) as e:
                self.device_info['driver'] = 'Unknown'
                logging.debug(f"[auto-antenna] Could not get driver info: {e}")

            # Get device name/model using ethtool
            ethtool_result = subprocess.run(
                ['ethtool', '-i', interface],
                capture_output=True,
                text=True,
                timeout=2
            )
            if ethtool_result.returncode == 0:
                for line in ethtool_result.stdout.split('\n'):
                    if 'bus-info' in line:
                        self.device_info['name'] = line.split(':')[-1].strip()
                        logging.info(f"[auto-antenna] Device Name: {self.device_info['name']}")

            # Get chipset info using iw
            iw_result = subprocess.run(
                ['iw', interface, 'info'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if iw_result.returncode == 0:
                for line in iw_result.stdout.split('\n'):
                    if 'wiphy' in line:
                        self.device_info['chipset'] = line.split()[-1]
                        logging.info(f"[auto-antenna] Device Chipset: {self.device_info['chipset']}")

        except Exception as e:
            logging.error(f"[auto-antenna] Error getting device info: {e}")

    def _interface_exists(self, interface):
        """Check if a network interface exists"""
        try:
            result = subprocess.run(
                ['ip', 'link', 'show', interface],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logging.error(f"[auto-antenna] Error checking interface {interface}: {e}")
            return False

    def _switch_to_external(self):
        """Switch to external WiFi adapter (wlan1)"""
        try:
            self.switching = True

            logging.info("[auto-antenna] === SWITCHING TO EXTERNAL ADAPTER ===")

            # Stop pwnagotchi service
            logging.info("[auto-antenna] Stopping pwnagotchi service...")
            subprocess.run(['systemctl', 'stop', 'pwnagotchi'], check=True, timeout=10)

            # Bring down both interfaces
            subprocess.run(['ip', 'link', 'set', 'wlan0', 'down'], timeout=5)
            subprocess.run(['ip', 'link', 'set', 'wlan1', 'down'], timeout=5)

            # Rename onboard wlan0 to wlan_temp
            subprocess.run(['ip', 'link', 'set', 'wlan0', 'name', 'wlan_temp'], check=True, timeout=5)

            # Rename external wlan1 to wlan0
            subprocess.run(['ip', 'link', 'set', 'wlan1', 'name', 'wlan0'], check=True, timeout=5)
            subprocess.run(['ip', 'link', 'set', 'wlan0', 'up'], timeout=5)

            # Keep onboard interface down
            subprocess.run(['ip', 'link', 'set', 'wlan_temp', 'down'], timeout=5)

            # Update device info for new adapter
            self._update_device_info()

            # Start pwnagotchi service
            logging.info("[auto-antenna] Starting pwnagotchi service...")
            subprocess.run(['systemctl', 'start', 'pwnagotchi'], check=True, timeout=10)

            self.current_antenna = "external"
            self.switch_count += 1
            self.last_switch_time = time.strftime("%Y-%m-%d %H:%M:%S")

            logging.info("[auto-antenna] ✓ Switched to EXTERNAL WiFi successfully")

        except Exception as e:
            logging.error(f"[auto-antenna] ✗ Error switching to external: {e}")
            # Try to recover
            try:
                subprocess.run(['systemctl', 'start', 'pwnagotchi'], timeout=10)
            except:
                pass
        finally:
            self.switching = False

    def _switch_to_internal(self):
        """Switch back to internal WiFi adapter"""
        try:
            self.switching = True

            logging.info("[auto-antenna] === SWITCHING TO INTERNAL ADAPTER ===")

            # Stop pwnagotchi service
            logging.info("[auto-antenna] Stopping pwnagotchi service...")
            subprocess.run(['systemctl', 'stop', 'pwnagotchi'], check=True, timeout=10)

            # Bring down wlan0 (external adapter) if it exists
            if self._interface_exists("wlan0"):
                subprocess.run(['ip', 'link', 'set', 'wlan0', 'down'], timeout=5)

            # Rename wlan_temp back to wlan0 if it exists
            if self._interface_exists("wlan_temp"):
                subprocess.run(['ip', 'link', 'set', 'wlan_temp', 'name', 'wlan0'], check=True, timeout=5)
                subprocess.run(['ip', 'link', 'set', 'wlan0', 'up'], timeout=5)

            # Update device info for onboard adapter
            self._update_device_info()

            # Start pwnagotchi service
            logging.info("[auto-antenna] Starting pwnagotchi service...")
            subprocess.run(['systemctl', 'start', 'pwnagotchi'], check=True, timeout=10)

            self.current_antenna = "internal"
            self.switch_count += 1
            self.last_switch_time = time.strftime("%Y-%m-%d %H:%M:%S")

            logging.info("[auto-antenna] ✓ Reverted to INTERNAL WiFi successfully")

        except Exception as e:
            logging.error(f"[auto-antenna] ✗ Error switching to internal: {e}")
            # Try to recover
            try:
                subprocess.run(['systemctl', 'start', 'pwnagotchi'], timeout=10)
            except:
                pass
        finally:
            self.switching = False