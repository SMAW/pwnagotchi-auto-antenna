# 📶 Pwnagotchi Auto Antenna Plugin  

This plugin **automatically switches between internal and external WiFi adapters** on your **Pwnagotchi**, depending on whether a USB WiFi adapter is plugged in. No more reboots required!  

It runs as a Pwnagotchi plugin and detects WiFi adapter changes in real time, restarting the Pwnagotchi service with the correct WiFi interface. It includes a web interface for monitoring and detailed device information logging.

## 🔧 Features  
✅ **Hot-swappable** – Detects WiFi adapter changes on the go  
✅ **Automatic switching** – Enables/disables external WiFi as needed  
✅ **Web Interface** – Monitor status and device info via browser  
✅ **JSON API** – Programmatic access to antenna status  
✅ **Device Info Logging** – Logs MAC, driver, chipset info on every switch  
✅ **Minimal UI footprint** – Shows just `A:i` or `A:e` on screen  
✅ **No reboots needed** – Keeps your Pwnagotchi running smoothly  

## 🛠️ Installation  

### As a Pwnagotchi Plugin (Recommended)

1. **Copy the plugin file** to your Pwnagotchi plugins directory:
   ```bash
   sudo cp auto_antenna.py /usr/local/share/pwnagotchi/custom-plugins/
   ```

2. **Edit your Pwnagotchi configuration** (`/etc/pwnagotchi/config.toml`):
   ```toml
   main.plugins.auto_antenna.enabled = true
   main.plugins.auto_antenna.check_interval = 1
   main.plugins.auto_antenna.position_x = 180
   main.plugins.auto_antenna.position_y = 0
   main.plugins.auto_antenna.label = "A"
   main.plugins.auto_antenna.internal_text = "i"
   main.plugins.auto_antenna.external_text = "e"
   ```

3. **Restart Pwnagotchi**:
   ```bash
   sudo systemctl restart pwnagotchi
   ```

### Legacy Installation (Bash Script)

For users who prefer the standalone bash script without the plugin features:  

1. **Copy the script** (`switch_wifi_smart.sh`) to `/` and make it executable:  
   ```bash
   sudo cp switch_wifi_smart.sh /
   sudo chmod +x /switch_wifi_smart.sh
   ```

2. **Create the service file** at `/etc/systemd/system/switch_wifi_smart.service`:  

   ```ini
   [Unit]
   Description=Wifi Switch Script
   After=network.target

   [Service]
   Type=simple
   ExecStart=/bin/bash /switch_wifi_smart.sh
   Restart=always
   RestartSec=5
   User=root
   Group=root

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start the service**:  
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable switch_wifi_smart.service
   sudo systemctl start switch_wifi_smart.service
   ```

4. **Check if the service is running properly**:  
   ```bash
   sudo systemctl status switch_wifi_smart.service
   ```

## 🌐 Web Interface

The plugin provides a web interface for monitoring antenna status and device information.

### Accessing the Web Interface

Once the plugin is enabled, access the web interface at:
```
http://<pwnagotchi-ip>:8080/plugins/auto_antenna
```

For example:
- `http://10.0.0.2:8080/plugins/auto_antenna` (USB connection)
- `http://192.168.1.100:8080/plugins/auto_antenna` (WiFi connection)

### Web Interface Features

The web interface displays:
- **Current Antenna Status** – Shows whether internal or external adapter is active
- **Device Name** – Bus info and device identifier
- **MAC Address** – Hardware address of current WiFi adapter
- **Driver Name** – Kernel driver in use
- **Chipset Information** – Wireless chipset details
- **Total Switch Count** – Number of times adapters have been switched
- **Last Switch Timestamp** – When the last switch occurred

The page features:
- 🎨 **Dark theme** with green monospace font (classic terminal look)
- 🔄 **Auto-refresh** every 5 seconds
- 🖱️ **Manual refresh button** for immediate updates

## 📡 API Endpoint

The plugin provides a JSON API endpoint for programmatic access.

### API Usage

Access the API at:
```
http://<pwnagotchi-ip>:8080/plugins/auto_antenna/api
```

### API Response Format

```json
{
  "antenna": "internal",
  "device_name": "0000:01:00.0",
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "driver": "brcmfmac",
  "chipset": "phy0",
  "switch_count": 5,
  "last_switch": "2026-01-09 15:30:45",
  "switching": false
}
```

### API Fields

- `antenna` – Current antenna mode (`"internal"` or `"external"`)
- `device_name` – Device bus information
- `mac_address` – Hardware MAC address
- `driver` – Kernel driver name
- `chipset` – Wireless chipset identifier
- `switch_count` – Total number of switches performed
- `last_switch` – ISO timestamp of last switch (or `"Never"`)
- `switching` – Boolean indicating if a switch is in progress

## ⚙️ Configuration Options

Add these options to your `/etc/pwnagotchi/config.toml`:

```toml
# Enable the plugin
main.plugins.auto_antenna.enabled = true

# How often to check for adapter changes (in epochs, default: 1)
main.plugins.auto_antenna.check_interval = 1

# Screen position for the antenna indicator
main.plugins.auto_antenna.position_x = 180
main.plugins.auto_antenna.position_y = 0

# Label displayed before the antenna status (default: "A")
main.plugins.auto_antenna.label = "A"

# Text shown for internal antenna (default: "i")
main.plugins.auto_antenna.internal_text = "i"

# Text shown for external antenna (default: "e")
main.plugins.auto_antenna.external_text = "e"
```

### Configuration Examples

**Minimal display (just icon):**
```toml
main.plugins.auto_antenna.label = ""
main.plugins.auto_antenna.internal_text = "📶"
main.plugins.auto_antenna.external_text = "📡"
```

**Verbose display:**
```toml
main.plugins.auto_antenna.label = "Antenna"
main.plugins.auto_antenna.internal_text = "internal"
main.plugins.auto_antenna.external_text = "external"
main.plugins.auto_antenna.position_x = 10
main.plugins.auto_antenna.position_y = 90
```

**Check less frequently:**
```toml
main.plugins.auto_antenna.check_interval = 5  # Check every 5 epochs
```

## 📝 Logging

The plugin logs detailed device information to help with troubleshooting:

### Device Information Logged

Every time the adapter is switched, the following information is logged:
- **MAC Address** – Hardware address of the WiFi adapter
- **Driver Name** – Kernel driver in use (e.g., `brcmfmac`, `rtl8xxxu`)
- **Chipset Info** – Wireless chipset identifier (e.g., `phy0`)
- **Device Name** – Bus info (e.g., `0000:01:00.0`)

### Example Log Output

```
[auto-antenna] Plugin loaded
[auto-antenna] Device MAC: aa:bb:cc:dd:ee:ff
[auto-antenna] Device Driver: brcmfmac
[auto-antenna] Device Name: 0000:01:00.0
[auto-antenna] Device Chipset: phy0
[auto-antenna] External WiFi detected, switching...
[auto-antenna] === SWITCHING TO EXTERNAL ADAPTER ===
[auto-antenna] Stopping pwnagotchi service...
[auto-antenna] Device MAC: 11:22:33:44:55:66
[auto-antenna] Device Driver: rt2800usb
[auto-antenna] Device Name: 0001:02:00.0
[auto-antenna] Device Chipset: phy1
[auto-antenna] Starting pwnagotchi service...
[auto-antenna] ✓ Switched to EXTERNAL WiFi successfully
```

### Viewing Logs

Check the Pwnagotchi logs to see antenna switching activity:
```bash
sudo journalctl -u pwnagotchi -f | grep auto-antenna
```

## 🔧 Troubleshooting

### Web Interface Not Accessible

**Problem:** Cannot access the web interface at `http://<ip>:8080/plugins/auto_antenna`

**Solutions:**
1. **Check if Pwnagotchi is running:**
   ```bash
   sudo systemctl status pwnagotchi
   ```

2. **Verify the plugin is enabled:**
   ```bash
   grep -A2 "auto_antenna" /etc/pwnagotchi/config.toml
   ```

3. **Check if web interface is enabled:**
   ```bash
   grep "ui.web.enabled" /etc/pwnagotchi/config.toml
   ```
   Should show `main.ui.web.enabled = true`

4. **Verify you're using the correct IP and port:**
   - USB connection: Usually `10.0.0.2:8080`
   - WiFi connection: Check `ip addr` for the actual IP

5. **Check logs for errors:**
   ```bash
   sudo journalctl -u pwnagotchi -n 100 | grep -i error
   ```

### Antenna Not Switching

**Problem:** Adapter doesn't switch when USB WiFi is plugged in

**Solutions:**
1. **Verify wlan1 is detected:**
   ```bash
   ip link show wlan1
   ```

2. **Check plugin logs:**
   ```bash
   sudo journalctl -u pwnagotchi -f | grep auto-antenna
   ```

3. **Ensure proper permissions:**
   The plugin needs root access to switch adapters. Pwnagotchi should run as root.

4. **Check if external adapter is supported:**
   Some WiFi adapters may not be compatible or require additional drivers.

### Device Info Shows "Unknown"

**Problem:** Web interface shows "Unknown" for device information

**Solutions:**
1. **Install required tools:**
   ```bash
   sudo apt-get install ethtool iw
   ```

2. **Check if wlan0 exists:**
   ```bash
   ip link show wlan0
   ```

3. **Manually test device info commands:**
   ```bash
   cat /sys/class/net/wlan0/address
   ethtool -i wlan0
   iw wlan0 info
   ```

## 📋 Legacy Bash Script

The repository includes `switch_wifi_smart.sh` for users who prefer a standalone service without the plugin features. This script provides basic adapter switching functionality but lacks the web interface, API, and device info logging features available in the plugin.

The bash script is maintained for backward compatibility but we recommend using the Pwnagotchi plugin for the best experience.

## 📝 Notes  
- Ensure your script (`/switch_wifi_smart.sh`) properly detects the presence of a USB WiFi adapter and restarts Pwnagotchi accordingly.  
- You can modify `RestartSec=5` to change the polling interval for adapter detection.  

Now your Pwnagotchi will **automatically switch WiFi adapters without requiring a reboot!** 🚀
