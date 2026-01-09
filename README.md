# 📶 Pwnagotchi Auto Antenna Plugin

**Version 1.1.0**

This plugin **automatically switches between internal and external WiFi adapters** on your **Pwnagotchi**, depending on whether a USB WiFi adapter is plugged in. No more reboots required!  

It runs in the background and detects WiFi adapter changes in real time, restarting the Pwnagotchi service with the correct WiFi interface.  

## 🔧 Features  
✅ **Hot-swappable** – Detects WiFi adapter changes on the go  
✅ **Automatic switching** – Enables/disables external WiFi as needed  
✅ **Plugin-based** – Integrates seamlessly with Pwnagotchi  
✅ **Web Interface** – Monitor antenna status via browser at `/plugins/auto_antenna`  
✅ **JSON API** – RESTful API endpoint for automation at `/plugins/auto_antenna/api`  
✅ **Device Info Logging** – Logs MAC, driver, chipset, and device information  
✅ **UI Display** – Shows current antenna status on Pwnagotchi screen  
✅ **No reboots needed** – Keeps your Pwnagotchi running smoothly  

## 🛠️ Installation  

### Plugin Installation (Recommended)

1. **Copy the plugin** (`auto_antenna.py`) to your Pwnagotchi plugins directory:  
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
   ```bash
   sudo systemctl restart pwnagotchi
   ```

### Standalone Script Installation

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
  "device_name": "0000:01:00.0",
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "driver": "brcmfmac",
  "chipset": "phy0",
  "switch_count": 5,
  "last_switch": "2026-01-09 14:32:15",
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
