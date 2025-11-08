# i reverse-engineered my smart lights (because why not)

so basically i got bored and decided to hack and dive into my Philips Wiz lights instead of using their app like a normal person.

**the problem:** the official Wiz app is... fine? but it's missing stuff. can't integrate with my own tools, and honestly where's the fun in just using an app?

**the solution:** turns out these Rs.500 bulbs just accept UDP packets on port 38899. no auth or protocols. sending raw JSON over UDP.

## what this does

- discovers all Wiz lights on your network (UDP broadcast go brrr)
- turns them on/off via command line OR web interface
- sets any RGB color + brightness you want
- comes with a clean web UI because clicking buttons > typing commands sometimes
- FastAPI backend that actually works
- **makes your lights react to music in real-time** (bass→red, mids→green, treble→blue)

basically i went from "click app button" to "control my lights from terminal/browser/literally anywhere" AND made them dance to music

## the tech stack (keeping it simple)

```
pure python socket programming no dependencies for the core stuff
FastAPI because i'm not writing raw HTTP in 2025
vanilla HTML/CSS/JS web UI that just works
zero authentication we live dangerously (jk it's local network only)
```

## how to run this thing

1. **clone it**

```bash
git clone https://github.com/myselfshravan/wiz-hack.git
cd wiz-hack
```

2. **install deps** (you need Python 3.10+)

```bash
pip install -r requirements.txt
```

3. **make sure you're on the same WiFi as your lights** (crucial, duh)

4. **spin up the API server**

```bash
python api_server.py
```

5. **open browser** http://localhost:8000

that's it. you can now control your lights like a hacker.

## CLI mode (for the terminal warriors)

discover all lights on your network:

```bash
python wiz_control.py discover
```

turn on a specific light:

```bash
python wiz_control.py on 192.168.1.100
```

set it to purple (because why not):

```bash
python wiz_control.py color 192.168.1.100 128 0 128
```

## 🎵 audio & music visualizer modes (the fun part)

okay this is where it gets insane. your lights react to music in real-time.

### Two modes available:

1. **`audio_visualizer.py`** - Uses your microphone (live music, any audio source)
2. **`music_visualizer.py`** - Plays audio files (MP3/WAV/FLAC) with PERFECT sync

**basic usage:**

```bash
python audio_visualizer.py
```

that's it. play some music, your lights will dance to it. bass makes it red, mids make it green, treble makes it blue.

**different modes:**

**color-focused modes** (default behavior - colors change with frequencies):
```bash
# default - frequency bands mapped to RGB
python audio_visualizer.py --mode frequency_bands

# warm/cool colors based on energy
python audio_visualizer.py --mode energy

# rainbow colors based on dominant frequency
python audio_visualizer.py --mode rainbow

# multi-light mode - each light shows different frequency (sick for demos)
python audio_visualizer.py --mode multi
```

**brightness-focused modes** (NEW - makes the sync super obvious!):
```bash
# pulse mode - static warm color, brightness pulses with music
# BEST for showing sync in videos - everyone instantly sees it
python audio_visualizer.py --mode pulse

# strobe mode - aggressive brightness flashes on beats
# perfect for EDM/electronic music, looks INSANE
python audio_visualizer.py --mode strobe

# spectrum_pulse mode - subtle color hints + aggressive brightness
# best of both worlds - bass=red, treble=blue, but brightness is the star
python audio_visualizer.py --mode spectrum_pulse

# spectrum_pulse_v2 mode - SNAPPIER, MORE VOLATILE (LATEST!)
# advanced spectral flux detection, dual-time smoothing, beat pops
# feels ALIVE with micro-jitter, fast attack/slow release
# perfect for club-style lighting that reacts to every transient
python audio_visualizer.py --mode spectrum_pulse_v2
```

**control specific lights:**

```bash
# auto-discover and use all lights
python audio_visualizer.py --lights all

# use specific light(s)
python audio_visualizer.py --lights 192.168.1.100
python audio_visualizer.py --lights 192.168.1.100,192.168.1.101
```

**brightness control:**

```bash
# default brightness (1.5x boost)
python audio_visualizer.py

# max brightness mode (3x boost)
python audio_visualizer.py --brightness-boost 3.0

# subtle brightness (1x, no boost)
python audio_visualizer.py --brightness-boost 1.0
```

**sensitivity control** (make brightness changes MORE dramatic):

```bash
# dramatic party mode with aggressive swings
python audio_visualizer.py --mode spectrum_pulse \
  --sensitivity 2.5 --smoothing 0.1

# extreme party strobe (max sensitivity, no smoothing)
python audio_visualizer.py --mode strobe \
  --sensitivity 3.0 --smoothing 0

# subtle but noticeable (lower sensitivity)
python audio_visualizer.py --mode pulse \
  --sensitivity 0.5
```

**what sensitivity does:**
- sensitivity=1.0 (default): normal behavior
- sensitivity=2.0-3.0: dramatic swings, uses full brightness range
- sensitivity=0.5: subtle, gradual changes
- higher sensitivity = more party mode energy!

**how it works:**

1. captures audio from your mic using `sounddevice`
2. runs FFT (Fast Fourier Transform) to split into frequency bands
3. bass (20-250Hz) → red, mids (250-4000Hz) → green, treble (4000-20000Hz) → blue
4. sends RGB values to lights via UDP (~20-50ms latency)
5. applies smoothing so colors don't jitter

**spectrum_pulse_v2 technical deep dive** (for the nerds):

what makes v2 different:
- **spectral flux detection** - tracks frame-to-frame changes to catch transients/beats
- **dual-time smoothing** - fast attack (35ms), slower release (160ms) for natural dynamics
- **hann windowing** - reduces FFT smearing for cleaner frequency analysis
- **rolling median normalization** - auto-gain that adapts to room/volume
- **beat boost** - brief brightness overdrive on detected transients
- **micro-jitter** - small random brightness variation for "alive" feel
- **smaller buffer** (1024 vs 2048) - lower latency, snappier response

tuning tips:
```bash
# even snappier - lower buffer, more volatility
python audio_visualizer.py --mode spectrum_pulse_v2 --buffer-size 512

# more chaotic/energetic - increase jitter internally via code
# edit audio_visualizer.py line 100: jitter_amount=0.12

# calmer but still responsive - increase release time
# edit audio_visualizer.py line 96: release_ms=220
```

why it feels different:
- brightness JUMPS up on beats (fast attack) but FADES down naturally (slow release)
- spectral flux catches drum hits, snares, kicks that RMS alone misses
- beat boost briefly overdrives brightness past normal max for that "pop"
- micro-jitter prevents dead-zone flatness between beats
- result: lights feel responsive, dynamic, and ALIVE

---

## 🎼 music file visualizer (PERFECT SYNC!)

play audio files (MP3, WAV, FLAC) with lights perfectly synced - no microphone needed!

**why use this instead of mic:**
- perfect sync (no lag, no background noise)
- same song = same light show every time
- way better for demos and videos
- cleaner audio analysis

**basic usage:**

```bash
python music_visualizer.py --file song.mp3
```

**all visualizer options work:**

```bash
# party mode with dramatic swings
python music_visualizer.py --file edm.mp3 \
  --mode spectrum_pulse \
  --sensitivity 2.5 --smoothing 0.1

# extreme strobe mode
python music_visualizer.py --file dubstep.mp3 \
  --mode strobe \
  --sensitivity 3.0 --smoothing 0

# loop for continuous party
python music_visualizer.py --file party.mp3 --loop
```

**on-screen display:**
- progress bar with time
- frequency visualization
- brightness indicator
- all in real-time while music plays

---

**demo tips for that viral video:**

- **USE `music_visualizer.py` for demos** - perfect sync every time
- **use `pulse` or `strobe` mode** - the brightness sync is WAY more obvious than color changes
- use electronic music with clear bass drops (skrillex, deadmau5, etc.)
- film in a dark room (makes the brightness pulses super dramatic)
- show the terminal with progress bar + frequency bars
- `strobe` mode on beat drops = instant viral moment
- multi-light mode looks absolutely insane on camera
- record the video, then overlay the terminal output for that hacker vibe

---

## 🎬 video visualizer (NEXT LEVEL INSANITY!)

okay so audio was cool, but what if your lights sync to VIDEOS? like actual movie scenes, game footage, anything.

**DIY Ambilight but better** - Philips charges $$$$ for this. you just reverse-engineered it.

**basic usage:**

```bash
python video_visualizer.py --file movie.mp4
```

your lights will now match the colors on screen. dark scene = dim lights. explosion = bright orange/red. underwater scene = blue. it's INSANE.

**different modes:**

```bash
# dominant color mode (default) - extracts main color from entire frame
python video_visualizer.py --file video.mp4 --mode dominant_color

# edge analysis mode (TRUE Ambilight style) - uses colors from frame edges
# this is what Philips TVs do, looks sick for movies
python video_visualizer.py --file video.mp4 --mode edge_analysis

# average color mode - simple average of all pixels
python video_visualizer.py --file video.mp4 --mode average

# hybrid mode - colors from video + brightness from audio track
# the ULTIMATE experience - visual colors + audio-reactive brightness
python video_visualizer.py --file movie.mp4 --mode hybrid --audio-brightness
```

**control the effect:**

```bash
# adjust edge thickness for edge_analysis mode (0.0-0.5)
python video_visualizer.py --file video.mp4 --mode edge_analysis --edge-thickness 0.2

# color smoothing - prevent jarring color jumps
python video_visualizer.py --file video.mp4 --color-smoothing 0.7

# run lights-only mode (no video window, great for projectors)
python video_visualizer.py --file video.mp4 --no-display
```

**how it works:**

1. reads video file frame by frame using OpenCV
2. analyzes each frame for color content (K-means clustering for dominant color, or edge extraction for Ambilight)
3. sends RGB values to lights via UDP
4. syncs to video framerate for perfect timing
5. optional: extracts audio track with ffmpeg and uses it for brightness control
6. displays video with color preview and stats overlay

**epic use cases:**

- **movie nights** - your living room becomes part of the movie (explosions, sunsets, underwater scenes all sync)
- **gaming** - lights react to game footage (record gameplay, play it back with light sync)
- **music videos** - combine visual + audio sync for full sensory experience
- **presentations** - lights match your slides (record screen, play with lights)
- **horror movies** - dark scenes = dim lights, jump scares = bright flash (terrifying)

**pro tips:**

- `edge_analysis` mode works best for movies/TV shows (mimics real Ambilight)
- `dominant_color` mode is great for animated content (vibrant scenes)
- use `--audio-brightness` with music videos for double sync (colors + beats)
- `--color-smoothing 0.7` prevents seizure-inducing color flashes
- film this setup and watch the LinkedIn engagement go CRAZY

**requirements:**

```bash
# install opencv for video processing
pip install opencv-python>=4.8.0

# optional: ffmpeg for audio extraction (hybrid mode)
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: download from ffmpeg.org
```

---

## the API endpoints

```
GET  /                       web interface
GET  /discover              find all lights
POST /on                    turn on first light found
POST /off                   turn off first light found
POST /color                set color {r, g, b, brightness}
GET  /status               get light status
POST /light/{ip}/on        turn on specific light
POST /light/{ip}/off       turn off specific light
POST /light/{ip}/color     set specific light color
```

## how this actually works (the nerdy part)

Wiz lights don't have an official API. they just listen on UDP port 38899 and accept JSON commands. that's it. that's the whole security model.

```python
# literally this simple
message = {"id": 1, "method": "setPilot", "params": {"r": 255, "g": 0, "b": 0}}
sock.sendto(json.dumps(message).encode(), (light_ip, 38899))
```

for discovery, i just broadcast to 255.255.255.255 and collect responses. every light on the network yells back with their details.

shoutout to [sbidy/pywizlight](https://github.com/sbidy/pywizlight) for the unofficial protocol docs

## why i built this

1. i wanted custom automations the app doesn't support
2. reverse engineering IoT devices is fun
3. terminal > app (fight me)
4. now i can control my lights from literally anywhere - scripts, cron jobs, webhooks, you name it
5. because i can

## things you can do with this

- **audio visualizer mode** - make lights dance to music (bass/mid/treble → RGB)
- integrate with your calendar (red light when in meeting)
- create your own scenes with gradients and transitions
- automate based on literally anything (weather, stocks, github commits)
- impress your friends (or concern them)
- throw RGB parties without expensive DJ equipment

## security note

this runs on your local network with no auth. don't expose it to the internet unless you want random people changing your light colors (actually that sounds kinda fun)

## contributing

found a bug? want to add features? PRs welcome. this is a weekend hack that accidentally became useful.

## license

MIT - do whatever you want with it

---

_built by someone who thinks RGB lights should be programmable_

_follow me on [linkedin](https://linkedin.com/in/shravanrevanna) for more questionable automation projects_

p.s. - yes i know there are existing libraries for this. building it from scratch was the point >
