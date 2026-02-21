# 🥔 Tater Automations (Home Assistant)

**Tater Automations** is a Home Assistant custom integration that makes it easy to run
*Tater automation plugins* directly from Home Assistant automations — **no YAML, no REST calls, no AI routing**.

It provides a native **“Call Tater automation tool”** action in the Home Assistant UI.

This integration is designed to work with the **Tater Automations platform** and
automation-only plugins like camera events, doorbell alerts, weather summaries, and event queries.

---

## ✨ What This Does

- Adds a Home Assistant service/action for Tater automations
- Lets you call Tater tools by name (same names as in the Tater WebUI)
- Pass arguments using simple key/value fields
- Designed for **fast, reliable automations**
- No conversational AI involved (your GPU can finally relax 😌)

---

## 📦 Installation (HACS)

1. Open **HACS**
2. Go to **Integrations**
3. Click **⋮ → Custom repositories**
4. Add this repository:
   ```
   https://github.com/TaterTotterson/tater_automations
   ```
   Category: **Integration**
5. Install **Tater Automations**
6. Restart Home Assistant

---

## ⚙️ Configuration

After restart:

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **Tater Automations**
4. Enter:
   - **Host**: IP or hostname of your Tater instance  
     (example: `10.4.20.173`)
   - **Port**: Automations platform port  
     (default: `8788`)

That’s it. No YAML required.

---

## ▶️ Using in Automations

Once installed, a new automation action becomes available.

### Action:
**Call Tater automation tool**

### Fields:
- **Tool**  
  Dropdown with:
  - `camera_event`
  - `doorbell_alert`
  - `events_query_brief`
  - `weather_brief`
  - `zen_greeting`
- **Area** *(camera_event only, optional)*  
  Preset dropdown with common areas (plus custom input)
- **Camera** *(camera_event only, optional)*  
  Camera entity dropdown from Home Assistant (`camera.*`)
- **Timeframe / Query / Input Text Entity** *(events_query_brief, optional)*  
  Optional selectors for event brief generation and writing into `input_text.*`
- **Hours / Query / Input Text Entity** *(weather_brief, optional)*  
  Optional selectors for weather brief generation and writing into `input_text.*`
- **Include Date / Tone / Prompt Hint / Input Text Entity** *(zen_greeting, optional)*  
  Optional selectors for zen greeting generation and output target

---

## 🔧 Example: Camera Event Automation

**Trigger**
- Motion detected on a camera

**Action**
- Call Tater automation tool

**Tool**
```
camera_event
```

**Area**
```
front yard
```

**Camera**
```
camera.front_door_high
```

That’s it.  
Tater will:
- Fetch the snapshot
- Generate a short description
- Store the event for later queries

---

## 🔔 Example: Doorbell Alert Automation

**Action**
- Call Tater automation tool

**Tool**
```
doorbell_alert
```

No arguments are sent for this tool from the Home Assistant action form.

---

## 📋 Example: Events Query Brief Automation

**Action**
- Call Tater automation tool

**Tool**
```
events_query_brief
```

**Timeframe**
```
today
```

**Area**
```
front yard
```

---

## 🌤 Example: Weather Brief Automation

**Action**
- Call Tater automation tool

**Tool**
```
weather_brief
```

**Hours**
```
12
```

---

## 🧘 Example: Zen Greeting Automation

**Action**
- Call Tater automation tool

**Tool**
```
zen_greeting
```

**Tone**
```
zen
```

---

## 🧠 Supported Automation Plugins

This integration is intended for **automation-only** Tater plugins, such as:

- `camera_event`
- `doorbell_alert`
- `events_query_brief`
- `weather_brief`
- `zen_greeting`

The tool name is always the **plugin name shown in the Tater WebUI**.

---

## 🚫 What This Is *Not*

- ❌ Not a chat interface
- ❌ Not conversational AI
- ❌ Not a message router
- ❌ Not GPU-heavy

This integration exists specifically so automations stay:
**fast, predictable, and boring (in a good way).**

---

## 🥔 Why This Exists

Tater Totterson got a little carried away once and tried routing automations through AI.

It worked… but it wasn’t smart.

This integration puts automations back where they belong:
**direct, deterministic, and reliable** — while still letting Tater do the heavy lifting behind the scenes.

---

## 🧩 Related Projects

- **Tater Core**  
  https://github.com/TaterTotterson/Tater
- **Tater Home Assistant Integration**  
  https://github.com/TaterTotterson/Tater-HomeAssistant

---

Happy automating 🥔
