# PlexOnEchoKids

Plays random music from a Plex playlist to **Echo Dot KIDS** on every boot.

## Why?

* My kid has a Echo Dot Kids and a lot of audiobooks on my Plex Server.
* Due to limitations the official "Alexa Plex Skill" is not available on the KIDS device so I needed something else...
* I've tried this with some ESP-Modules but it was pure pain with limited RAM and PCM/MP3 conversion etc...
* In the end I did it with the Pi Zero in Python!
* So he can tell Alexa to turn on the smart socket "Audiobooks" which will turn on the Pi Zero which will start to play audiobooks from Plex
* Restart the smart socket for next track, maybe I will add some GPIO-Buttons later to Play/Pause, Next Track etc...

---

## Device

I use a **Pi Zero 2W** with **Raspberry Pi OS Lite (64-bit)**
(flashed with Raspberry Pi Imager – enable SSH + Wi-Fi)

---

## Install OS Requirements

```bash
sudo apt update
sudo apt install -y \
  mpv \
  bluez-alsa-utils \
  pulseaudio \
  bluetooth \
  git\
  python3-venv\
  python3-pip 
```

## Install PlexOnEchoKids

```bash
git clone https://github.com/tomtom1337/PlexOnEchoKids
cd PlexOnEchoKids
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt --upgrade
deactivate
```

## Pair Bluetooth Speaker (once)

```bash
sudo rfkill unblock bluetooth
bluetoothctl
power on
agent on
scan on
```

- Say "Alexa, Connect" or go to the App -> Device -> Bluetooth -> Connect...
- When “Echo Dot-xxxx XX:XX:XX:XX:XX:XX ” appears in the Terminal:

```bash
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
```

Test audio:

```bash
mpv --no-video --audio-device=alsa/bluealsa /usr/share/sounds/alsa/Front_Center.wav

```


## Config

Copy example_config.ini to config.ini:

```bash
cd PlexOnEchoKids
cp example_config.ini config.ini
nano config.ini
```

- Go to your Plex server via a Webbrowser, start the playlist
- You should now see all information in the URL
- **TOKEN** is **OPTIONAL** leave empty when not used e.g. whitlisted all local IPs in the settings

```ini
[PLEX]
url = http://192.168.0.1:32400
playlist_id = 123456
token = 

[BLUETOOTH]
bt_mac = XX:XX:XX:XX:XX:XX
```

---


## Test

Test script:

```bash
cd PlexOnEchoKids
source venv/bin/activate
python plexonechokids.py
deactivate
```

---

## Auto Start Service

Create:

```bash
sudo nano /etc/systemd/system/plexonechokids.service
```

- Example for Pi, change path if needed
- Must be run as User=root to restart Bluetooth if needed since the Alexa is not very stable...

```
[Unit]
Description=PlexOnEchoKids
After=network-online.target bluetooth.service
Wants=network-online.target

[Service]
User=root
WorkingDirectory=/home/pi/plexonechokids
ExecStart=/home/pi/PlexOnEchoKids/venv/bin/python /home/pi/PlexOnEchoKids/plexonechokids.py
Restart=always
RestartSec=8

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable plexonechokids
sudo systemctl start plexonechokids
```

Logs:

```bash
journalctl -u plexonechokids -f
```

## Speedup Pi Zero (Optional)

The Pi Zero takes up 60 Seconds to boot and play - which can be reduces by some tweaks to ~30 seconds

### BOOT CONFIG

Edit `nano /boot/firmware/config.txt` and add these lines:

```bash
hdmi_blanking=2
disable_overscan=1
dtoverlay=vc4-kms-v3d,nohdmi
max_framebuffers=0

disable_splash=1
boot_delay=0
initial_turbo=20

camera_auto_detect=0
display_auto_detect=0

# Bluetooth only audio
dtparam=audio=off
```

------------------------------------------------------------------------

### CMDLINE CONFIG

Edit `nano /boot/firmware/cmdline.txt` and add to the end of the line:

```bash
quiet loglevel=1 logo.nologo vt.global_cursor_default=0 plymouth.enable=0 fastboot noswap ipv6.disable=1 rfkill.default_state=1
```

------------------------------------------------------------------------

### BLUETOOTH CONFIG

Edit `nano /etc/bluetooth/main.conf` and uncomment these lines:

```bash
FastConnectable = true
ReconnectAttempts=5
ReconnectIntervals=1,2,3,5
AutoEnable=true
```

------------------------------------------------------------------------

