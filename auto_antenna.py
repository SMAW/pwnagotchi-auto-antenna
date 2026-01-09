import logging
import os
import subprocess
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import json


class AutoAntenna(plugins.Plugin):
    __author__ = 'SMAW'
    __version__ = '1.1.0'
    __license__ = 'MIT'
    __description__ = 'Automatically switches between internal and external WiFi adapters and displays current antenna on screen'

    def __init__(self):
        self.current_antenna = "internal"
        self.previous_state = None
        self.switching = False
        self.device_info = {}
        self.check_counter = 0

    def on_loaded(self):
        logging.info("[auto-antenna] Plugin loaded")
        # Check initial state and log device info
        self.check_and_switch()

    def on_ui_setup(self, ui):
        # Get config with defaults for 2.13" screen
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
        # Get custom text from config
        int_text = self.options.get('text_internal', 'i')
        ext_text = self.options.get('text_external', 'e')
        
        # Update the antenna display
        if self.current_antenna == "external":
            ui.set('antenna', ext_text)
        else:
            ui.set('antenna', int_text)

    def on_unload(self, ui):
        logging.info("[auto-antenna] Plugin unloaded")

    def on_webhook(self, path, request):
        """Web interface for antenna status"""
        # Return JSON with antenna status and device info
        response = {
            'current_antenna': self.current_antenna,
            'device_info': self.device_info,
            'switching': self.switching
        }
        return json.dumps(response, indent=2)

    def on_epoch(self, agent, epoch, epoch_data):
        # Check based on configured interval (default every 5 epochs)
        check_interval = self.options.get('check_interval', 5)
        self.check_counter += 1
        
        if self.check_counter >= check_interval:
            self.check_counter = 0
            if not self.switching:
                self.check_and_switch()

    def check_and_switch(self):
        """Check if wlan1 exists and switch if needed"""
        try:
            # Check if wlan1 (external adapter) exists
            wlan1_exists = self._interface_exists("wlan1")
            
            # Determine current state
            if wlan1_exists and self.current_antenna != "external":
                logging.info("[auto-antenna] External WiFi detected, switching...")
                # Get device info before switching
                self._log_device_info("wlan1")
                self._switch_to_external()
                self.current_antenna = "external"
                
            elif not wlan1_exists and self.current_antenna == "external":
                logging.info("[auto-antenna] External WiFi removed, reverting to internal...")
                # Log internal device info
                self._log_device_info("wlan0")
                self._switch_to_internal()
                self.current_antenna = "internal"
                
        except Exception as e:
            logging.error(f"[auto-antenna] Error checking/switching: {e}")

    def _log_device_info(self, interface):
        """Log detailed device information"""
        try:
            info = {}
            
            # Get MAC address
            result = subprocess.run(
                ['cat', f'/sys/class/net/{interface}/address'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                info['mac'] = result.stdout.strip()
                logging.info(f"[auto-antenna] Device {interface} MAC: {info['mac']}")
            
            # Get device name/driver
            result = subprocess.run(
                ['ethtool', '-i', interface],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'driver:' in line:
                        info['driver'] = line.split(':')[1].strip()
                        logging.info(f"[auto-antenna] Device {interface} driver: {info['driver']}")
                    elif 'bus-info:' in line:
                        info['bus'] = line.split(':')[1].strip()
            
            # Get chipset info from lsusb if it's USB
            if 'usb' in info.get('bus', ''):
                result = subprocess.run(
                    ['lsusb'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    # Parse lsusb output for WiFi adapters
                    for line in result.stdout.split('\n'):
                        if any(keyword in line.lower() for keyword in ['wifi', 'wireless', '802.11', 'wlan', 'network']):
                            info['chipset'] = line
                            logging.info(f"[auto-antenna] Device {interface} chipset: {line.strip()}")
                            break
            
            # Get interface info
            result = subprocess.run(
                ['iw', 'dev', interface, 'info'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'type' in line:
                        info['type'] = line.split()[1]
                    elif 'wiphy' in line:
                        info['wiphy'] = line.split()[1]
                        
                logging.info(f"[auto-antenna] Device {interface} type: {info.get('type', 'unknown')}")
            
            # Store device info
            self.device_info[interface] = info
            logging.info(f"[auto-antenna] Full device info for {interface}: {json.dumps(info, indent=2)}")
            
        except Exception as e:
            logging.error(f"[auto-antenna] Error logging device info for {interface}: {e}")

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
            
            # Start pwnagotchi service
            logging.info("[auto-antenna] Starting pwnagotchi service...")
            subprocess.run(['systemctl', 'start', 'pwnagotchi'], check=True, timeout=10)
            
            logging.info("[auto-antenna] Switched to external WiFi successfully")
            
        except Exception as e:
            logging.error(f"[auto-antenna] Error switching to external: {e}")
            # Try to rollback
            try:
                if self._interface_exists("wlan_temp"):
                    subprocess.run(['ip', 'link', 'set', 'wlan_temp', 'name', 'wlan0'], timeout=5)
                    subprocess.run(['ip', 'link', 'set', 'wlan0', 'up'], timeout=5)
                subprocess.run(['systemctl', 'start', 'pwnagotchi'], timeout=10)
            except:
                pass
        finally:
            self.switching = False

    def _switch_to_internal(self):
        """Switch back to internal WiFi adapter"""
        try:
            self.switching = True
            
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
            
            # Start pwnagotchi service
            logging.info("[auto-antenna] Starting pwnagotchi service...")
            subprocess.run(['systemctl', 'start', 'pwnagotchi'], check=True, timeout=10)
            
            logging.info("[auto-antenna] Reverted to internal WiFi successfully")
            
        except Exception as e:
            logging.error(f"[auto-antenna] Error switching to internal: {e}")
            # Try to start service anyway
            try:
                subprocess.run(['systemctl', 'start', 'pwnagotchi'], timeout=10)
            except:
                pass
        finally:
            self.switching = False
