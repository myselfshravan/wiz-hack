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

## 🎵 audio visualizer mode (the fun part)

okay this is where it gets insane. your lights react to music in real-time.

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

**brightness range control** (constrain min/max brightness):

```bash
# subtle ambient (10-30% range) - won't blind you but still syncs
python audio_visualizer.py --mode pulse --min-brightness 10 --max-brightness 30

# always bright (60-100% range) - good for well-lit rooms
python audio_visualizer.py --mode pulse --min-brightness 60 --max-brightness 100

# maximum drama (5-100% range) - full dynamic range for dark room demos
python audio_visualizer.py --mode strobe --min-brightness 5 --max-brightness 100

# medium intensity (20-50% range) - perfect for background while working
python audio_visualizer.py --mode spectrum_pulse --min-brightness 20 --max-brightness 50
```

**sensitivity control** (make brightness changes MORE dramatic):

```bash
# YOUR CASE - full party mode with 10-30% range but DRAMATIC swings
# sensitivity=2.5 makes it use the FULL 10-30% range aggressively
python audio_visualizer.py --mode spectrum_pulse \
  --min-brightness 10 --max-brightness 30 \
  --sensitivity 2.5 --smoothing 0.1

# extreme party strobe (full range, max sensitivity, no smoothing)
python audio_visualizer.py --mode strobe \
  --min-brightness 5 --max-brightness 100 \
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

**demo tips for that viral video:**

- **use `pulse` or `strobe` mode** - the brightness sync is WAY more obvious than color changes
- use electronic music with clear bass drops (skrillex, deadmau5, etc.)
- film in a dark room (makes the brightness pulses super dramatic)
- show the terminal with frequency bars + brightness indicator (💡)
- `strobe` mode on beat drops = instant viral moment
- multi-light mode looks absolutely insane on camera
- pro tip: start with `pulse` mode, switch to `strobe` for the drop

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
