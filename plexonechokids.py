#!/usr/bin/env python3

import time
import random
import subprocess
import configparser
import threading
from plexapi.server import PlexServer

# ======= CONFIG =======
config = configparser.ConfigParser()
config.read("config.ini")

# Plex
PLEX_URL = config["PLEX"]["url"]
PLAYLIST_ID = int(config["PLEX"]["playlist_id"])
PLEX_TOKEN = config["PLEX"].get("token", "")

# Bluetooth
BT_MAC = config["BLUETOOTH"]["bt_mac"]

# MPV Settings
VOLUME = 100
CACHE = 20
MPV_AUDIO_DEVICE = "alsa/bluealsa"

# ======= FUNCTIONS =======

def bt_is_connected():
    """Check if BT device is connected"""
    result = subprocess.run(
        ["bluetoothctl", "info", BT_MAC],
        capture_output=True,
        text=True
    )
    return "Connected: yes" in result.stdout


def connect_bt_device():
    """Connect or Reconect BT"""
    print("Connect or Reconect BT")
    subprocess.run(["bluetoothctl", "disconnect", BT_MAC])
    time.sleep(1)
    subprocess.run(["rfkill", "unblock", "bluetooth"])
    subprocess.run(["bluetoothctl", "power", "on"])
    subprocess.run(["bluetoothctl", "connect", BT_MAC])
    time.sleep(3)


def get_random_track(plex):
    """Get a random track from the playlist"""
    pl = None
    for p in plex.playlists():
        print(p.title, p.ratingKey)
        if p.ratingKey == PLAYLIST_ID:
            pl = p
            break
    if not pl:
        raise Exception(f"Playlist {PLAYLIST_ID} not found")
    items = pl.items()
    return random.choice(items)


def pcm_available():
    """Check if BlueALSA PCM is available"""
    out = subprocess.getoutput("aplay -L")
    return "bluealsa" in out


# ===== Watchdog Thread =====
def bt_watchdog(stop_event):
    """Continuously monitor BT connection and reconnect if needed"""
    while not stop_event.is_set():
        if not bt_is_connected():
            print("⚠ Bluetooth disconnected → reconnecting...")
            connect_bt_device()
        time.sleep(5) 


def play_track(url):
    """Play a track via MPV with BT/PCM watchdog"""
    cmd = [
        "mpv",
        url,
        "--no-video",
        f"--audio-device={MPV_AUDIO_DEVICE}",
        f"--volume={VOLUME}",
        "--cache=yes",
        f"--cache-secs={CACHE}",
        "--gapless-audio=yes",
        "--demuxer-readahead-secs=30",
        "--audio-buffer=2",
        "--audio-stream-silence=yes",
        "--msg-level=all=warn",
        "--no-terminal",
    ]

    # Start BT watchdog thread
    stop_event = threading.Event()
    watchdog_thread = threading.Thread(target=bt_watchdog, args=(stop_event,))
    watchdog_thread.start()

    # Start MPV process
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    while proc.poll() is None:
        # Read stderr for PCM errors
        line = proc.stderr.readline()
        if "PCM not found" in line:
            print("⚠ PCM lost → reconnecting Bluetooth")
            connect_bt_device()
        time.sleep(1)

    # Stop watchdog
    stop_event.set()
    watchdog_thread.join()

    return proc.returncode == 0


# ======= MAIN LOOP =======
def main():
    # Initial connection
    if not bt_is_connected():
        connect_bt_device()

    # Connect to Plex
    if PLEX_TOKEN:
        plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    else:
        plex = PlexServer(PLEX_URL)

    while True:
        try:
            track = get_random_track(plex)
            print("▶ Playing:", track.title)

            url = track.getStreamURL()
            ok = play_track(url)

            if not ok:
                print("Retrying same track after reconnect")
                time.sleep(2)
                continue

        except Exception as e:
            print("Error:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
