<div align="center">

# ⚔ WW Barb Macro
### Diablo IV — Whirlwind Barbarian Automation Overlay

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white)
![Game](https://img.shields.io/badge/Diablo%20IV-Season%2013-B91C1C?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)
![Languages](https://img.shields.io/badge/Languages-FR%20%7C%20EN%20%7C%20DE%20%7C%20ES%20%7C%20IT-7c3aed?style=flat-square)

*by [DoktorP3st](https://www.twitch.tv/paglorieux)*

</div>

---

A lightweight **always-on-top overlay** for Diablo IV that automates the Whirlwind Barbarian skill rotation.  
Displays Xbox-style controller buttons with live cooldown bars, handles Whirlwind true-hold, and fires all buffs automatically — so you can focus on the actual game.

---

## ✨ Features

| | Feature | Details |
|---|---|---|
| 🎮 | **Xbox-style overlay** | Controller button badges (A/B/X/Y/RB/LB/RT/LT) with color-coded cooldown bars |
| 🌀 | **Whirlwind true hold** | Key stays physically pressed until you toggle off — no micro-stutters |
| ⚡ | **Skill automation** | Up to 5 configurable skills with individual cooldown timers + jitter |
| 🧪 | **Auto potion** | Fires your potion key on a configurable interval |
| ⏱ | **Session timer** | Tracks how long the macro has been active |
| 🌍 | **5 languages** | Français · English · Deutsch · Español · Italiano |
| ⚙ | **In-app settings** | Full GUI — no config file editing needed |
| 💾 | **Persistent config** | Position, keybinds, cooldowns saved automatically on exit |

---

## 📸 Preview

```
┌─────────────────────────────────────────┐
│ ⚔  WW BARB                    ●  ON  ⚙ ✕│
├──────────────────────────────────────────┤
│ [A]  Whirlwind   [════════════] TOURNE···│
│ [Q]  Potion      [██████████░░]  2.4s    │
├──────────────────────────────────────────┤
│ [X]  Iron Skin   [████████████]  PRÊT    │
│ [Y]  Rallying    [████░░░░░░░░]  3.1s    │
│ [RB] War Cry     [████████████]  PRÊT    │
│ [LT] Chall. Shout[██░░░░░░░░░░] 18.7s   │
│ [RT] Call Ancients[░░░░░░░░░░░] 44.2s   │
├──────────────────────────────────────────┤
│ ⚔ ACTIF — 3m47s                         │
└──────────────────────────────────────────┘
```

---

## 📦 Installation

### Requirements

- Python **3.8+** — [python.org](https://www.python.org/downloads/)
- **pynput** library

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/DoktorP3st/DiabloIV-Macro-ByDoktor.git
cd DiabloIV-Macro-ByDoktor

# 2. Install dependencies
pip install pynput

# 3. Launch
python ww_barb_macro.py
# — or double-click —
launch.bat
```

---

## ⌨ Controls

| Key | Action |
|-----|--------|
| `F1` *(configurable)* | Toggle macro ON / OFF |
| `Esc` | Toggle OFF (if macro is active) |
| Drag header | Move overlay anywhere on screen |
| `⚙` gear icon | Open settings |
| `✕` icon | Quit |

---

## 🌀 Whirlwind Hold Setup

The Whirlwind hold requires a **secondary keyboard binding** in Diablo IV:

1. In D4 → **Settings → Controls → Keyboard**
2. Find **Whirlwind** and add a secondary key (e.g. `5`)
3. Open the macro **Settings ⚙** → enable *Whirlwind Auto-Hold* → set the same key

Once enabled, the macro presses and **holds** that key for the entire duration the macro is active.

---

## ⚙ Settings Reference

Open with the **⚙** icon in the overlay.

| Setting | Description |
|---------|-------------|
| Toggle key | Hotkey to enable/disable the macro (default: `F1`) |
| Press duration | How long each key press is held in ms (default: `120`) |
| **Whirlwind hold** | Enable true-hold on a secondary D4 key |
| Ctrl / Key | Controller button label + keyboard key per skill |
| CD(s) | Cooldown in seconds — adjust to your actual in-game CDR |
| **Auto Potion** | Fire potion key every N seconds |
| Language | UI language (FR / EN / DE / ES / IT) |

> **Tip:** Skills fire in the order listed. Use ▲▼ arrows to reorder. You can rename each skill freely.

---

## 📁 File Structure

```
DiabloIV-Macro-ByDoktor/
├── ww_barb_macro.py       # Main application
├── i18n.py                # Internationalisation module
├── ww_barb_config.json    # Saved configuration (auto-generated)
├── launch.bat             # Windows launcher
└── locales/
    ├── fr.json            # Français
    ├── en.json            # English
    ├── de.json            # Deutsch
    ├── es.json            # Español
    └── it.json            # Italiano
```

---

## 🌍 Adding a Language

1. Copy `locales/en.json` → `locales/pt.json`
2. Translate all values (keep the keys in English)
3. Add `"pt": "Português"` to the `LANGUAGES` dict in `i18n.py`
4. Restart — it appears automatically in the settings dropdown

---

## ⚠ Disclaimer

This tool simulates keyboard input using `pynput`.  
Use it at your own risk and in accordance with Blizzard's Terms of Service.  
The author is not responsible for any account action resulting from its use.

---

## 👤 Author

Made by **DoktorP3st**  
🎮 Twitch: [twitch.tv/paglorieux](https://www.twitch.tv/paglorieux)

---

<div align="center">
<sub>⚔ Built for Diablo IV Season 13 — Lord of Hatred</sub>
</div>
