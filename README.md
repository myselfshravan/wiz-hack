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

basically i went from "click app button" to "control my lights from terminal/browser/literally anywhere"

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
pip install fastapi uvicorn
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

- integrate with your calendar (red light when in meeting)
- sync with your music (RGB party mode)
- create your own scenes with gradients and transitions
- automate based on literally anything (weather, stocks, github commits)
- impress your friends (or concern them)

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
