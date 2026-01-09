# 📶 Pwnagotchi Auto Antenna Plugin

**Version 1.1.0**

This plugin **automatically switches between internal and external WiFi adapters** on your **Pwnagotchi**, depending on whether a USB WiFi adapter is plugged in. No more reboots required!

It runs as a Pwnagotchi plugin and detects WiFi adapter changes in real time, restarting the Pwnagotchi service with the correct WiFi interface. It includes a web interface for monitoring and detailed device information logging.

> [!IMPORTANT]
> This project was developed with the assistance of AI. See [agents.md](agents.md) for details.

## 🔧 Features

- ✅ **Hot-swappable** – Detects WiFi adapter changes on the go without reboots.
- ✅ **Automatic switching** – Enables/disables external WiFi as needed.
- ✅ **Plugin-based** – Integrates seamlessly with the Pwnagotchi ecosystem.
- ✅ **Web Interface** – Monitor antenna status and device info via browser at `/plugins/auto_antenna`.
- ✅ **JSON API** – RESTful API endpoint for automation at `/plugins/auto_antenna/api`.
- ✅ **Device Info Logging** – Logs MAC, driver, chipset, and device information.
- ✅ **UI Display** – Shows current antenna status (`A:i` or `A:e`) on the Pwnagotchi screen.
- ✅ **Minimal Footprint** – Designed to be lightweight and unobtrusive.

## 🛠️ Installation

### Pwnagotchi Plugin Installation (Recommended)

1. **Copy the plugin file** to your Pwnagotchi custom plugins directory:
   ```bash
   sudo cp auto_antenna.py /usr/local/share/pwnagotchi/custom-plugins/
   ```

2. **Enable the plugin** in your configuration file (`/etc/pwnagotchi/config.toml`):
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

## 🌐 Web Interface & API

### Web Interface
Access the real-time status at: `http://<pwnagotchi-ip>:8080/plugins/auto_antenna`

Features:
- Dark theme terminal style.
- Displays MAC, Driver, Chipset, and Switch Count.
- Auto-refreshes every 5 seconds.

### JSON API
Programmatic access at: `http://<pwnagotchi-ip>:8080/plugins/auto_antenna/api`

Example Response:
```json
{
  "antenna": "external",
  "device_name": "0000:01:00.0",
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "driver": "rtl8xxxu",
  "chipset": "phy1",
  "switch_count": 3,
  "last_switch": "2026-01-09 14:32:15",
  "switching": false
}
```

## 📋 Requirements

- **Python 3.7+**
- Pwnagotchi Firmware
- `ethtool` and `iw` packages (for device information)
- Root/sudo access

## 🔧 Troubleshooting

1. **Web UI not loading?** Ensure `main.ui.web.enabled = true` is set in your `config.toml`.
2. **Not switching?** Check if the external adapter is recognized as `wlan1` via `ip link`.
3. **No device info?** Run `sudo apt-get install ethtool iw`.
4. **Logs?** Check them with `sudo journalctl -u pwnagotchi -f | grep auto-antenna`.

## 📄 License

MIT License - See repository for details.

##  Authors

- **SMAW / Terminatoror** - Original author and maintainer

---

Now your Pwnagotchi will **automatically switch WiFi adapters without requiring a reboot!** 🚀
