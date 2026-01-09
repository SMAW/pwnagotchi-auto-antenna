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

        self.dry_run = self.options.get('dry_run', False)
        if self.dry_run:
            logging.info("[auto-antenna] DRY RUN MODE ENABLED - No changes will be made")

        # Check if we are already in external mode (wlan_temp exists)
        if self._interface_exists("wlan_temp"):
             self.current_antenna = "external"
             logging.info("[auto-antenna] Detected existing external adapter configuration (wlan_temp exists)")

        # Get initial device info and state
        self._update_device_info()

        # MAC Address Verification Logic
        mac_file = "/etc/pwnagotchi/internal_wifi_mac"
        current_mac = self.device_info.get('mac', '')

        if not current_mac:
            logging.warning("[auto-antenna] Could not retrieve current MAC address. Skipping MAC verification.")
        else:
            if os.path.exists(mac_file):
                with open(mac_file, 'r') as f:
                    stored_mac = f.read().strip()

                if current_mac.lower() != stored_mac.lower():
                    logging.info(f"[auto-antenna] MAC mismatch! Current: {current_mac}, Stored Internal: {stored_mac}")
                    logging.info("[auto-antenna] Assuming EXTERNAL adapter is active due to MAC mismatch.")
                    self.current_antenna = "external"
                else:
                    logging.info(f"[auto-antenna] MAC match ({current_mac}). Confirmed INTERNAL adapter.")
                    if self.current_antenna == "external" and not self._interface_exists("wlan_temp"):
                         # This handles edge case where verified internal is active but state was confused
                         self.current_antenna = "internal"

            else:
                # File doesn't exist. We need to determine if we should save this MAC.
                # Use generic bus-info (not driver name) to guess if this is internal.
                # Internal is usually 'mmc' or 'platform'. External is 'usb'.
                bus_info = self.device_info.get('name', '').lower() # We stored bus-info in 'name'

                # Also check if we are already in 'external' mode detected by wlan_temp existence
                if self.current_antenna == "external":
                    logging.info("[auto-antenna] Plugin verified external mode. NOT saving this MAC as internal.")
                elif 'usb' in bus_info:
                    logging.info(f"[auto-antenna] Detected USB bus ({bus_info}). Assuming EXTERNAL adapter. NOT saving MAC.")
                    self.current_antenna = "external"
                else:
                    logging.info(f"[auto-antenna] No stored MAC. Detected internal-like bus ({bus_info}). Saving {current_mac} as INTERNAL MAC.")
                    try:
                        with open(mac_file, 'w') as f:
                            f.write(current_mac)
                    except Exception as e:
                        logging.error(f"[auto-antenna] Failed to save internal MAC: {e}")

        self.check_and_switch()

    def on_ui_setup(self, ui):
        # Get position and display config from options
        pos_x = self.options.get('position_x', 180)
        pos_y = self.options.get('position_y', 0)
        label_text = self.options.get('label', 'A')

        # Initial status text
        status_text = f"{label_text}:i" if label_text else 'i'

        # Add antenna status to the UI
        # Using empty label and combining text into value to keep them tight together
        ui.add_element('antenna', LabeledValue(
            color=BLACK,
            label='',
            value=status_text,
            position=(pos_x, pos_y),
            label_font=fonts.Small,
            text_font=fonts.Small))

    def on_ui_update(self, ui):
        # Get display values from config
        int_text = self.options.get('internal_text', 'i')
        ext_text = self.options.get('external_text', 'e')
        label_text = self.options.get('label', 'A')

        prefix = f"{label_text}:" if label_text else ""

        # Update the antenna display
        if self.current_antenna == "external":
            ui.set('antenna', f"{prefix}{ext_text}")
        else:
            ui.set('antenna', f"{prefix}{int_text}")

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

            # If we think we are using internal, but wlan1 is plugged in -> switch to external
            if wlan1_exists and self.current_antenna != "external":
                logging.info("[auto-antenna] External WiFi detected, switching...")
                self._switch_to_external()

            # If we think we are using external, but wlan1 is gone -> revert to internal
            # PROBLEM: When using external, we renamed wlan1 -> wlan0.
            # So "wlan1" will NOT exist in the system, but we are technically using the external adapter (now called wlan0).
            # We must detect if the card was physically removed.

            # If we are in "external" mode, the physical wlan1 is now wlan0.
            # The physical internal wlan0 is now wlan_temp.
            # So we check if wlan0 (the external card) still exists.

            elif self.current_antenna == "external":
                # In external mode, wlan0 IS the external adapter.
                # If wlan0 disappears, it means the stick was pulled.
                # HOWEVER, wlan0 might just be down or resetting.
                # A better check: does the system see the USB device?

                # If wlan_temp exists (internal card parked), but wlan1 shows up again (maybe renamed back by OS?)
                if wlan1_exists:
                     # This shouldn't happen if we renamed it wlan0, unless a SECOND external card appeared?
                     pass

                # Real check: If we are in external mode, we expect wlan_temp (internal) to exist.
                # If wlan1 does NOT exist (because it's named wlan0), that is normal.
                # We revert ONLY if the external device (wlan0) is gone.

                # Check if wlan0 (external) is still present
                if not self._interface_exists("wlan0"):
                     logging.info("[auto-antenna] Current external adapter (wlan0) vanished, reverting...")
                     self._switch_to_internal()

            # Original logic was: elif not wlan1_exists and self.current_antenna == "external": switch_to_internal()
            # This causes the loop because:
            # 1. Switch enables external. External is now `wlan0`. `wlan1` is GONE.
            # 2. Next check: `wlan1_exists` is False. `current_antenna` is "external".
            # 3. Logic triggers: "External removed (wlan1 missing), revert!"
            # 4. Reverts. External becomes `wlan1` again.
            # 5. Next check: `wlan1_exists` is True. `current_antenna` is "internal".
            # 6. Logic triggers: "External detected, switch!" -> Loop.

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

            if self.dry_run:
                logging.info("[auto-antenna] [DRY RUN] Would stop pwnagotchi service")
                logging.info("[auto-antenna] [DRY RUN] Would bring down wlan0 and wlan1")
                logging.info("[auto-antenna] [DRY RUN] Would rename wlan0 to wlan_temp")
                logging.info("[auto-antenna] [DRY RUN] Would rename wlan1 to wlan0 and bring up")
                logging.info("[auto-antenna] [DRY RUN] Would keep wlan_temp down")
                logging.info("[auto-antenna] [DRY RUN] Would update device info")
                logging.info("[auto-antenna] [DRY RUN] Would start pwnagotchi service")
                self.current_antenna = "external" # Simulate switch for display/logic
                self.switch_count += 1
                self.last_switch_time = time.strftime("%Y-%m-%d %H:%M:%S")
                logging.info("[auto-antenna] [DRY RUN] Simulated switch to EXTERNAL completd")
                return

            # Execute switch in a detached background process to avoid deadlock
            # when stopping the pwnagotchi service from within itself.
            logging.info("[auto-antenna] Spawning detached switch process...")

            # Create a temporary script for the switch operation
            script_path = "/tmp/switch_to_external.sh"
            with open(script_path, "w") as f:
                f.write("#!/bin/bash\n")
                f.write("sleep 5\n")
                f.write("systemctl stop pwnagotchi\n")
                # Clean up monitor interfaces if they exist
                f.write("iw dev wlan0mon del 2> /dev/null\n")
                f.write("iw dev mon0 del 2> /dev/null\n")
                f.write("ip link set wlan0 down\n")
                f.write("ip link set wlan1 down\n")
                f.write("ip link set wlan0 name wlan_temp\n")
                f.write("ip link set wlan1 name wlan0\n")
                f.write("ip link set wlan0 up\n")
                f.write("ip link set wlan_temp down\n")
                f.write("systemctl start pwnagotchi\n")
                f.write("rm -- \"$0\"\n") # Self-delete

            os.chmod(script_path, 0o755)

            # Use data-independent execution to survive service restart
            # If systemd-run is available, use it to create a transient scope
            if os.path.exists("/bin/systemd-run") or os.path.exists("/usr/bin/systemd-run"):
                 subprocess.run(["systemd-run", "--unit=auto-antenna-switch", "--scope", script_path], check=False)
            else:
                 # Fallback to nohup if systemd-run is missing
                 subprocess.Popen(f"nohup {script_path} > /dev/null 2>&1 &", shell=True)

            self.current_antenna = "external"
            self.switch_count += 1
            self.last_switch_time = time.strftime("%Y-%m-%d %H:%M:%S")

            logging.info("[auto-antenna] ✓ Initiated switch to EXTERNAL WiFi (service will restart)")

        except Exception as e:
            logging.error(f"[auto-antenna] ✗ Error initiating switch to external: {e}")
        finally:
            self.switching = False

    def _switch_to_internal(self):
        """Switch back to internal WiFi adapter"""
        try:
            self.switching = True

            logging.info("[auto-antenna] === SWITCHING TO INTERNAL ADAPTER ===")

            if self.dry_run:
                logging.info("[auto-antenna] [DRY RUN] Would stop pwnagotchi service")
                logging.info("[auto-antenna] [DRY RUN] Would bring down wlan0")
                logging.info("[auto-antenna] [DRY RUN] Would rename wlan_temp to wlan0 and bring up")
                logging.info("[auto-antenna] [DRY RUN] Would update device info")
                logging.info("[auto-antenna] [DRY RUN] Would start pwnagotchi service")
                self.current_antenna = "internal" # Simulate switch for display/logic
                self.switch_count += 1
                self.last_switch_time = time.strftime("%Y-%m-%d %H:%M:%S")
                logging.info("[auto-antenna] [DRY RUN] Simulated switch to INTERNAL completed")
                return

            # Execute switch in a detached background process to avoid deadlock
            logging.info("[auto-antenna] Spawning detached switch process...")

            # Create a temporary script for the switch operation
            script_path = "/tmp/switch_to_internal.sh"
            with open(script_path, "w") as f:
                f.write("#!/bin/bash\n")
                f.write("sleep 5\n")
                f.write("systemctl stop pwnagotchi\n")
                # Clean up monitor interfaces if they exist
                f.write("iw dev wlan0mon del 2> /dev/null\n")
                f.write("iw dev mon0 del 2> /dev/null\n")
                f.write("ip link set wlan0 down\n")
                f.write("if ip link show wlan_temp > /dev/null 2>&1; then\n")
                f.write("  ip link set wlan_temp name wlan0\n")
                f.write("  ip link set wlan0 up\n")
                f.write("elif ip link show wlan1 > /dev/null 2>&1; then\n")
                f.write("  ip link set wlan1 name wlan0\n")
                f.write("  ip link set wlan0 up\n")
                f.write("fi\n")
                f.write("systemctl start pwnagotchi\n")
                f.write("rm -- \"$0\"\n") # Self-delete

            os.chmod(script_path, 0o755)

             # Use data-independent execution to survive service restart
            if os.path.exists("/bin/systemd-run") or os.path.exists("/usr/bin/systemd-run"):
                 subprocess.run(["systemd-run", "--unit=auto-antenna-internal", "--scope", script_path], check=False)
            else:
                 subprocess.Popen(f"nohup {script_path} > /dev/null 2>&1 &", shell=True)

            self.current_antenna = "internal"
            self.switch_count += 1
            self.last_switch_time = time.strftime("%Y-%m-%d %H:%M:%S")

            logging.info("[auto-antenna] ✓ Initiated revert to INTERNAL WiFi (service will restart)")

        except Exception as e:
            logging.error(f"[auto-antenna] ✗ Error initiating switch to internal: {e}")
        finally:
            self.switching = False
            self.switching = False