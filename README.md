# 📶 Pwnagotchi Auto Antenna Plugin

**Version 1.1.0**

# 📶 Pwnagotchi Auto Antenna Plugin  

This plugin **automatically switches between internal and external WiFi adapters** on your **Pwnagotchi**, depending on whether a USB WiFi adapter is plugged in. No more reboots required!  

It runs as a Pwnagotchi plugin and detects WiFi adapter changes in real time, restarting the Pwnagotchi service with the correct WiFi interface. It includes a web interface for monitoring and detailed device information logging.

## 🔧 Features  
✅ **Hot-swappable** – Detects WiFi adapter changes on the go  
✅ **Automatic switching** – Enables/disables external WiFi as needed  
✅ **Plugin-based** – Integrates seamlessly with Pwnagotchi  
✅ **Web Interface** – Monitor antenna status via browser at `/plugins/auto_antenna`  
✅ **JSON API** – RESTful API endpoint for automation at `/plugins/auto_antenna/api`  
✅ **Device Info Logging** – Logs MAC, driver, chipset, and device information  
✅ **UI Display** – Shows current antenna status on Pwnagotchi screen  
✅ **Web Interface** – Monitor status and device info via browser  
✅ **JSON API** – Programmatic access to antenna status  
✅ **Device Info Logging** – Logs MAC, driver, chipset info on every switch  
✅ **Minimal UI footprint** – Shows just `A:i` or `A:e` on screen  
✅ **No reboots needed** – Keeps your Pwnagotchi running smoothly  

## 🛠️ Installation  

### Plugin Installation (Recommended)

1. **Copy the plugin** (`auto_antenna.py`) to your Pwnagotchi plugins directory:  
### As a Pwnagotchi Plugin (Recommended)

1. **Copy the plugin file** to your Pwnagotchi plugins directory:
   ```bash
   sudo cp auto_antenna.py /usr/local/share/pwnagotchi/custom-plugins/
   ```

2. **Enable the plugin** in `/etc/pwnagotchi/config.toml`:  
   ```toml
   main.plugins.auto_antenna.enabled = true
   main.plugins.auto_antenna.check_interval = 1  # Check every N epochs
   main.plugins.auto_antenna.position_x = 180    # UI position X
   main.plugins.auto_antenna.position_y = 0      # UI position Y
   main.plugins.auto_antenna.label = "A"         # UI label text
   main.plugins.auto_antenna.internal_text = "i" # Display for internal
   main.plugins.auto_antenna.external_text = "e" # Display for external
   ```

3. **Restart Pwnagotchi**:  
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

### Standalone Script Installation
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

The plugin provides a web interface for monitoring antenna status in real-time.

### Accessing the Web Interface

Navigate to: `http://your-pwnagotchi-ip:8080/plugins/auto_antenna`

The web interface displays:
- **Current Antenna Status** - Internal or External
- **Device Name** - Hardware device identifier
- **MAC Address** - Current WiFi adapter MAC
- **Driver** - Kernel driver name
- **Chipset** - WiFi chipset information
- **Total Switches** - Count of antenna switches
- **Last Switch** - Timestamp of last switch

**Features:**
- 🎨 Dark theme with green/black terminal style
- 🔄 Auto-refreshes every 5 seconds
- 🔘 Manual refresh button

### JSON API Endpoint

For programmatic access, use the JSON API at: `http://your-pwnagotchi-ip:8080/plugins/auto_antenna/api`

**Example Response:**
```json
{
  "antenna": "external",
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
  "last_switch": "2026-01-09 14:32:15",
  "last_switch": "2026-01-09 15:30:45",
  "switching": false
}
```

**Usage Example:**
```bash
# Check current antenna status
curl http://10.0.0.2:8080/plugins/auto_antenna/api | jq .

# Get just the antenna type
curl -s http://10.0.0.2:8080/plugins/auto_antenna/api | jq -r .antenna
```

## 📊 Device Information Logging

The plugin automatically logs detailed device information:

**On Plugin Load:**
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
```

**On Antenna Switch:**
```
[auto-antenna] External WiFi detected, switching...
[auto-antenna] === SWITCHING TO EXTERNAL ADAPTER ===
[auto-antenna] Stopping pwnagotchi service...
[auto-antenna] Device MAC: 11:22:33:44:55:66
[auto-antenna] Device Driver: rt2800usb
[auto-antenna] Device Name: 0000:02:00.0
[auto-antenna] Device Name: 0001:02:00.0
[auto-antenna] Device Chipset: phy1
[auto-antenna] Starting pwnagotchi service...
[auto-antenna] ✓ Switched to EXTERNAL WiFi successfully
```

**View Logs:**
```bash
# Real-time log monitoring
sudo journalctl -u pwnagotchi -f | grep auto-antenna

# Last 50 auto-antenna log entries
sudo journalctl -u pwnagotchi | grep auto-antenna | tail -50
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
- The plugin checks for adapter changes every N epochs (configurable via `check_interval`)

## 🐛 Troubleshooting

### Web Interface Not Accessible

**Problem:** Cannot access web interface at `/plugins/auto_antenna`

**Solutions:**
1. Verify Pwnagotchi web UI is running:
   ```bash
   sudo systemctl status pwnagotchi
   ```

2. Check if plugin is enabled in config:
   ```bash
   grep -A5 "auto_antenna" /etc/pwnagotchi/config.toml
   ```

3. Verify plugin loaded successfully:
   ```bash
   sudo journalctl -u pwnagotchi | grep "auto-antenna.*loaded"
   ```

4. Check web server port (default 8080):
   ```bash
   netstat -tuln | grep 8080
   ```

### Device Information Not Showing

**Problem:** Web interface shows "Unknown" for device info

**Solutions:**
1. Verify `ethtool` is installed:
   ```bash
   sudo apt-get install ethtool
   ```

2. Verify `iw` is installed:
   ```bash
   sudo apt-get install iw
   ```

3. Check if wlan0 interface exists:
   ```bash
   ip link show wlan0
   ```

4. Manually test device info commands:
   ```bash
   cat /sys/class/net/wlan0/address
   basename $(readlink /sys/class/net/wlan0/device/driver)
   ethtool -i wlan0
   iw wlan0 info
   ```

### Antenna Not Switching

**Problem:** External adapter plugged in but not switching

**Solutions:**
1. Check if wlan1 is detected:
   ```bash
   ip link show wlan1
   ```

2. Verify plugin is checking at right interval:
   ```toml
   # Lower interval = more frequent checks
   main.plugins.auto_antenna.check_interval = 1
   ```

3. Check for errors in logs:
   ```bash
   sudo journalctl -u pwnagotchi | grep -i "auto-antenna.*error"
   ```

4. Manually test switching commands:
   ```bash
   sudo systemctl stop pwnagotchi
   sudo ip link set wlan0 down
   sudo ip link set wlan1 down
   sudo ip link set wlan0 name wlan_temp
   sudo ip link set wlan1 name wlan0
   sudo ip link set wlan0 up
   sudo systemctl start pwnagotchi
   ```

### UI Element Not Showing

**Problem:** Antenna status not visible on Pwnagotchi display

**Solutions:**
1. Adjust position in config:
   ```toml
   main.plugins.auto_antenna.position_x = 180
   main.plugins.auto_antenna.position_y = 0
   ```

2. Try different coordinates (depends on your screen):
   ```toml
   # Top right corner
   main.plugins.auto_antenna.position_x = 200
   main.plugins.auto_antenna.position_y = 0
   ```

3. Verify UI elements are not overlapping with other plugins

## 🔐 Security Considerations

- The plugin requires root access to manage network interfaces
- Web interface runs on Pwnagotchi's web server (use VPN or firewall for security)
- API endpoint provides read-only information (no state changes via API)
- Consider restricting web UI access to trusted networks only

## 📦 Requirements

- Python 3.7+
- Pwnagotchi firmware
- `ethtool` package (for device info)
- `iw` package (for chipset info)
- Root/sudo access (for interface management)

## 🤝 Contributing

Feel free to submit issues and pull requests for:
- Bug fixes
- New features
- Documentation improvements
- Testing on different hardware

## 📄 License

MIT License - See repository for details

## 👤 Authors

- **SMAW / Terminatoror** - Original author and maintainer

## 📚 Version History

### v1.1.0 (Current)
- ✨ Added web interface at `/plugins/auto_antenna`
- ✨ Added JSON API endpoint at `/plugins/auto_antenna/api`
- ✨ Added device information logging (MAC, driver, chipset)
- ✨ Added switch counting and timestamp tracking
- ✨ Enhanced error handling and recovery
- 📝 Comprehensive documentation updates

### v1.0.0
- 🎉 Initial release
- ✅ Automatic antenna switching
- ✅ UI display element
- ✅ Configurable options

---

Now your Pwnagotchi will **automatically switch WiFi adapters without requiring a reboot!** 🚀  

Now your Pwnagotchi will **automatically switch WiFi adapters without requiring a reboot!** 🚀
