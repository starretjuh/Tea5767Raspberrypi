#!/usr/bin/python3
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import time
import subprocess
from tea5767stationscanner import tea5767

# --- GPIO ---
BUTTON_RADIO = 16
BUTTON_MORSE = 19

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_RADIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_MORSE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --- Radio opstarten ---
radio = tea5767()
time.sleep(0.2)
radio.writeFrequency(100.9, 0, 1)
print("Systeem actief — radio modus")
print("GPIO19 drukken+loslaten = morse modus aan")
print("GPIO16 = volgende zender (omhoog) of terug naar radio (morse)")

process    = None
morse_mode = False
scan_dir   = 1       # 1 = omhoog, 0 = omlaag — wisselt elke scan

MORSE_FREQ   = "101.0"
MORSE_FREQ_F = 101.0
TONE_FILE    = "tone_loop.wav"

prev_morse = GPIO.HIGH
prev_radio = GPIO.HIGH

try:
    while True:
        morse_state = GPIO.input(BUTTON_MORSE)
        radio_state = GPIO.input(BUTTON_RADIO)

        # MORSE KNOP
        if not morse_mode:
            if prev_morse == GPIO.LOW and morse_state == GPIO.HIGH:
                morse_mode = True
                radio.writeFrequency(MORSE_FREQ_F, 2, 1)
                print("\n[Morse] Modus aan — knop = toon, GPIO16 = terug naar radio")
        else:
            if prev_morse == GPIO.HIGH and morse_state == GPIO.LOW:
                if process is None:
                    process = subprocess.Popen(
                        ["sudo", "rpitx", "-m", "FM", "-i", TONE_FILE,
                         "-f", f"{MORSE_FREQ}e6"]
                    )
                    time.sleep(0.05)
                    radio.writeFrequency(MORSE_FREQ_F, 0, 1)
                    print(".", end="", flush=True)

            if prev_morse == GPIO.LOW and morse_state == GPIO.HIGH:
                if process is not None:
                    process.terminate()
                    process.wait()
                    process = None
                    radio.writeFrequency(MORSE_FREQ_F, 2, 1)

        # RADIO KNOP
        if prev_radio == GPIO.HIGH and radio_state == GPIO.LOW:
            if morse_mode:
                if process is not None:
                    process.terminate()
                    process.wait()
                    process = None
                morse_mode = False
                radio.writeFrequency(radio.freq, 0, 1)
                print(f"\n[Radio] Terug naar radio op {radio.freq} MHz")
            else:
                # Stap één frequentie voorbij de huidige zender zodat
                # scan() niet meteen weer op dezelfde blijft hangen
                stapje = 0.2 if scan_dir == 1 else -0.2
                radio.freq = round(radio.freq + stapje, 1)
                if radio.freq > 107.9:
                    radio.freq = 87.5
                elif radio.freq < 87.5:
                    radio.freq = 107.9
                radio.writeFrequency(radio.freq, 1, scan_dir)
                time.sleep(0.05)

                print(f"\n[Radio] Scannen {'omhoog' if scan_dir else 'omlaag'} vanaf {radio.freq} MHz")
                radio.scan(scan_dir)
                print(f"[Radio] Gevonden: {radio.freq} MHz")

                # Wissel richting voor volgende druk
                scan_dir = 1 - scan_dir

        prev_morse = morse_state
        prev_radio = radio_state

        time.sleep(0.01)

except KeyboardInterrupt:
    pass

finally:
    if process is not None:
        process.terminate()
        process.wait()
    radio.off()
    GPIO.cleanup()
