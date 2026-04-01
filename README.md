# Raspberry Pi FM Radio and Morse Code Transmitter

A Raspberry Pi project that combines an FM radio receiver with a manual Morse code transmitter. Using a TEA5767 FM module and two buttons, you can listen to FM radio and transmit Morse code over FM and hear your own transmissions through the same speaker.

---

## Table of Contents

- [Features](#features)
- [Hardware](#hardware)
- [Wiring](#wiring)
- [Software Dependencies](#software-dependencies)
- [Installation](#installation)
- [File Overview](#file-overview)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Known Limitations](#known-limitations)
- [Credits](#credits)

---

## Features

- FM radio reception via TEA5767 module (87.5–107.9 MHz)
- Automatic station scanning with signal strength detection
- Manual Morse code transmission via GPIO button (telegraph key style)
- Self-monitoring: hear your own Morse transmissions through the speaker
- Clean mode switching between radio and Morse with a single button press
- Silence between Morse tones (no radio bleed-through during transmission)

---

## Hardware

| Component | Details |
|---|---|
| Raspberry Pi | Pi 4 (also works on Pi 3) |
| FM module | TEA5767 breakout board |
| Buttons | 2× momentary push buttons |
| Speaker | USB-powered speaker connected to TEA5767 headphone jack |
| Antenna | FM antenna (included with TEA5767 module) |
| Misc | Breadboard, jumper wires |

---

## Wiring

### TEA5767 → Raspberry Pi (I²C)

```
TEA5767        Raspberry Pi
-------        ------------
VCC      →     3.3V  (Pin 1)
GND      →     GND   (Pin 6)
SDA      →     GPIO2 (Pin 3)  [I²C SDA]
SCL      →     GPIO3 (Pin 5)  [I²C SCL]
```

The TEA5767 audio output (headphone jack) connects to your speaker. The antenna port connects to your FM antenna, do not confuse with the headphone jack.

### Buttons → Raspberry Pi (GPIO)

```
Button         Raspberry Pi
------         ------------
RADIO button   GPIO16 (Pin 36) → GND
MORSE button   GPIO19 (Pin 35) → GND
```

Both buttons are wired between their GPIO pin and GND. The software uses the Pi's internal pull-up resistors, so no external resistors are needed.

### rpitx FM Transmitter

rpitx transmits via **GPIO4 (Pin 7)**. Connect a short wire (~17cm for 101 MHz) as an antenna for short-range transmission. Keep this wire away from sensitive components.

> **Warning:** Transmitting on FM frequencies may be restricted in your country. Keep the antenna short and use only for personal/experimental purposes.

### Full Pin Reference

```
Pin 1   3.3V        → TEA5767 VCC
Pin 3   GPIO2 SDA   → TEA5767 SDA
Pin 5   GPIO3 SCL   → TEA5767 SCL
Pin 6   GND         → TEA5767 GND, Button GND rail
Pin 7   GPIO4       → rpitx TX antenna wire
Pin 35  GPIO19      → Morse button
Pin 36  GPIO16      → Radio/scan button
```

---

## Software Dependencies

### Python libraries

```bash
pip3 install RPi.GPIO smbus quick2wire-api websocket-client
```

### rpitx

rpitx turns the Pi's GPIO4 clock into an FM transmitter.

```bash
git clone https://github.com/F5OEO/rpitx
cd rpitx
./install.sh
```

### System packages

```bash
sudo apt-get update
sudo apt-get install python3-smbus i2c-tools
```

### Enable I²C

```bash
sudo raspi-config
# Interface Options → I2C → Enable
```

Verify the TEA5767 is detected (should show address `0x60`):

```bash
sudo i2cdetect -y 1
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/rpi-radio-morse.git
cd rpi-radio-morse

# Install Python dependencies
pip3 install RPi.GPIO smbus quick2wire-api websocket-client

# Install rpitx (if not already installed)
git clone https://github.com/F5OEO/rpitx
cd rpitx && ./install.sh && cd ..

# Generate the tone file (or use the included tone_loop.wav)
# The included tone_loop.wav is a 1000Hz sine wave, 30 seconds long
```

### File placement

All files should be in the same directory:

```
rpi-radio-morse/
├── tea5767controller.py      # Main program — run this
├── tea5767stationscanner.py  # TEA5767 driver (I²C communication)
├── tone_loop.wav             # 30-second tone for Morse transmission
└── README.md
```

---

## File Overview

### `tea5767controller.py`

The main program. Handles all button logic and coordinates between the radio and the Morse transmitter.

**Key variables at the top of the file:**

```python
BUTTON_RADIO = 16       # GPIO pin for scan/radio button
BUTTON_MORSE = 19       # GPIO pin for Morse button
MORSE_FREQ   = "101.0"  # FM frequency rpitx transmits on (MHz)
MORSE_FREQ_F = 101.0    # Same frequency as float for TEA5767
TONE_FILE    = "tone_loop.wav"  # Audio file rpitx broadcasts
```

### `tea5767stationscanner.py`

Driver for the TEA5767 chip over I²C. Originally written by Dipto Pratyaksa (LinuxCircle.com, 2015), modified for this project.

**Main methods used:**

| Method | Description |
|---|---|
| `writeFrequency(freq, mute, direction)` | Tune to a frequency. mute: 0=on, 1=search, 2=muted |
| `scan(direction)` | Scan for next strong station. 1=up, 0=down |
| `calculateFrequency()` | Read current frequency from chip registers |
| `getLevel()` | Read signal strength (0–15) |
| `getStereoFlag()` | Returns "stereo" or "mono" |
| `off()` | Mute and power down the chip |

**`writeFrequency` mute parameter:**

| Value | Effect |
|---|---|
| `0` | Normal listening mode |
| `1` | Search/scan mode (muted during seek) |
| `2` | Both channels fully muted |

**Important:** always pass `direction=1` in the final `writeFrequency` call after scanning. This keeps the HLSI (High/Low Side Injection) bit consistent — alternating it causes the chip to detune slightly, producing a rough audio quality.

### `tone_loop.wav`

A 1000 Hz sine wave, 30 seconds long, mono, 44100 Hz sample rate. rpitx broadcasts this file as an FM signal on `MORSE_FREQ` when the Morse button is held. 30 seconds is long enough for any practical Morse transmission before the file ends.

To generate your own:

```bash
# Using sox
sox -n -r 44100 -c 1 tone_loop.wav synth 30 sin 1000

# Using Python
python3 -c "
import wave, struct, math
rate = 44100
duration = 30
freq = 1000
with wave.open('tone_loop.wav', 'w') as f:
    f.setnchannels(1)
    f.setsampwidth(4)
    f.setframerate(rate)
    for i in range(rate * duration):
        v = int(0.5 * 2**31 * math.sin(2 * math.pi * freq * i / rate))
        f.writeframes(struct.pack('<i', v))
"
```

---

## Usage

### Starting the program

```bash
sudo python3 tea5767controller.py
```

`sudo` is required because rpitx needs root access to control the GPIO clock hardware.

### Button controls

```
┌─────────────────────────────────────────────────────┐
│  RADIO MODE (default on startup)                    │
│                                                     │
│  GPIO16 (radio button):  scan to next station       │
│  GPIO19 (morse button):  press and release → enter  │
│                          Morse mode                 │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  MORSE MODE                                         │
│                                                     │
│  GPIO19 (morse button):  hold = transmit tone       │
│                          release = silence          │
│  GPIO16 (radio button):  return to radio mode       │
└─────────────────────────────────────────────────────┘
```

### Step-by-step workflow

**Listening to radio:**

1. Run the program — it starts on 100.9 MHz by default
2. Press GPIO16 to scan for the next station
3. The chip scans down the FM band and stops at the strongest signal

**Sending Morse code:**

1. Press and release GPIO19 — you hear silence (radio is muted)
2. Press and hold GPIO19 — tone transmits on 101.0 MHz, TEA5767 tunes to 101.0 and you hear the tone through the speaker
3. Release GPIO19 — silence
4. Repeat for each dot/dash
5. Press GPIO16 when done — returns to radio on last tuned frequency

**Morse code timing guide:**

| Symbol | Duration |
|---|---|
| Dot (·) | Short press (~100ms) |
| Dash (−) | Long press (~300ms) |
| Gap between symbols | Short silence (~100ms) |
| Gap between letters | Medium silence (~300ms) |
| Gap between words | Long silence (~700ms) |

**International Morse code reference:**

```
A ·−    B −···  C −·−·  D −··   E ·
F ··−·  G −−·   H ····  I ··    J ·−−−
K −·−   L ·−··  M −−    N −·    O −−−
P ·−−·  Q −−·−  R ·−·   S ···   T −
U ··−   V ···−  W ·−−   X −··−  Y −·−−
Z −−··

1 ·−−−−  2 ··−−−  3 ···−−  4 ····−  5 ·····
6 −····  7 −−···  8 −−−··  9 −−−−·  0 −−−−−
```

---

## How It Works

### Radio reception

The TEA5767 communicates over I²C at address `0x60`. To tune to a frequency, the controller calculates a 14-bit PLL word from the target frequency using the crystal oscillator constant (32768 Hz):

```
freq14bit = int(4 × (freq_MHz × 1,000,000 + 225,000) / 32768)
```

This word is split into a high byte and low byte and written to the chip along with configuration bytes for mute state, stereo/mono, and LO injection side (HLSI bit).

**HLSI consistency:** the TEA5767 can use either high-side or low-side local oscillator injection. The direction must stay consistent — if you write `direction=1` (HLSI=1, high-side) when tuning, all subsequent writes must also use `direction=1`. Alternating this bit shifts the internal tuning by ~225 kHz, causing the audio to sound rough or noisy. This project always uses `direction=1`.

### Station scanning

`scan(direction)` steps 0.1 MHz at a time and checks two status bits after each step:

- `readyFlag` (bit 7 of status byte 0): set when the chip has locked onto a carrier
- Signal level (bits 7–4 of status byte 3): 0–15, higher is stronger

Scanning continues until `readyFlag=1` and signal level is sufficient. The scan averages two frequency readback methods (`calculateFrequency` and `getFreq`) for accuracy.

### Morse transmission

rpitx modulates the Pi's GPIO4 clock pin at 101.0 MHz FM. It reads `tone_loop.wav` and uses it as the audio modulation source — a 1000 Hz tone produces a clean FM signal.

When the Morse button is pressed:

1. rpitx starts as a subprocess, transmitting on 101.0 MHz
2. After 50ms (startup time for rpitx), the TEA5767 is retuned to 101.0 MHz with `mute=0`
3. The TEA5767 now receives its own transmission and sends audio to the speaker
4. When the button is released, rpitx is terminated and the TEA5767 is muted (`mute=2`)

This self-monitoring approach requires no extra hardware — the same module that receives FM also receives the Pi's own transmission.

### Button edge detection

The main loop runs at 10ms intervals and tracks the previous state of each button. Actions trigger on edges (state changes), not levels:

- **Falling edge** (HIGH→LOW): button pressed — start tone
- **Rising edge** (LOW→HIGH): button released — stop tone, or enter Morse mode

Morse mode activation uses a rising edge (release) rather than a falling edge (press). This prevents the same button press from both activating Morse mode and immediately starting a tone transmission.

---

## Configuration

### Change the startup frequency

In `tea5767controller.py`:

```python
radio.writeFrequency(100.9, 0, 1)  # Change 100.9 to your preferred MHz
```

### Change the Morse transmit frequency

```python
MORSE_FREQ   = "101.0"   # String for rpitx subprocess argument
MORSE_FREQ_F = 101.0     # Float for TEA5767 — must match above
```

Keep at least 0.5 MHz distance from any strong local radio station to avoid interference.

### Change the tone frequency

Replace `tone_loop.wav` with any mono WAV file. A higher frequency (e.g. 1200 Hz) gives a higher-pitched tone. The file must be at least as long as your longest intended Morse press — the included file is 30 seconds.

### Scan direction

By default the scan alternates direction (up then down) with each button press. Change the starting direction:

```python
scan_dir = 1   # 1 = up, 0 = down
```

---

## Troubleshooting

### TEA5767 not detected on I²C

```bash
sudo i2cdetect -y 1
```

Should show `60` at address 0x60. If not: check VCC/GND/SDA/SCL wiring, confirm I²C is enabled in `raspi-config`, check for bent or swapped pins.

### Only ruis (noise) from speaker

- Antenna not connected or connected to wrong port — antenna goes in the antenna port, not the headphone jack
- Tuned to a frequency with no station nearby — press GPIO16 to scan
- HLSI inconsistency — make sure you're using the fixed `tea5767stationscanner.py` from this repo

### Morse tone sounds distorted or cuts out

- `tone_loop.wav` missing or not in the same directory as the scripts
- rpitx not installed or not in PATH, test with `which rpitx`
- The Pi needs `sudo` for rpitx, always run the controller with `sudo python3`

### Radio button doesn't respond

- Check breadboard connections — jumper wires can break internally without visible damage
- Test the button pin directly:

```python
import RPi.GPIO as GPIO, time
GPIO.setmode(GPIO.BCM)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)
while True:
    print(GPIO.input(16))
    time.sleep(0.1)
```

Should print `1` normally and `0` when button is pressed.

- If `0` never appears: button is wired incorrectly or jumper wire is broken
- Button must be wired between GPIO16 and GND, not between GPIO16 and 3.3V

### Scan always lands on same station

This is normal if there is only one strong station in your area. The scanner stops at the first signal strong enough to lock on. In an area with multiple strong stations (e.g. in a car with a proper antenna) the scan will find different stations each time.


### `rpitx` warning messages on startup

```
Warning : rpitx V2 is only to try to be compatible with version 1
RPi4 GPIO detected
```

These are normal and harmless. rpitx prints them on every start.

---

## Known Limitations

- **Single antenna, no diversity:** reception quality depends heavily on antenna placement and local transmitter proximity
- **Blocking scan:** `radio.scan()` blocks the main loop while searching. On a press during scan the button may not register immediately — wait for the scan to complete
- **30-second tone limit:** if a single Morse press exceeds 30 seconds the tone stops (rpitx finishes the file). This is not a practical limitation for Morse code
- **101.0 MHz fixed transmit frequency:** changing this requires updating both `MORSE_FREQ` and `MORSE_FREQ_F` in the controller
- **No automatic Morse encoding:** the button is a manual telegraph key — text-to-Morse conversion is not implemented

---

## Credits

- TEA5767 Python driver originally by **Dipto Pratyaksa** for LinuxCircle.com (August 2015)
- rpitx by **F5OEO** — https://github.com/F5OEO/rpitx
- quick2wire Python API — https://github.com/quick2wire/quick2wire-python-api

