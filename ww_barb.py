"""
╔═══════════════════════════════════════════════════════════╗
║   WW BARB — Macro v3  (Controller Display + WW Hold)      ║
║   Diablo 4 Season 13 / Lord of Hatred                     ║
║                                                           ║
║   INSTALLATION :  pip install pynput                      ║
║   LANCEMENT    :  python ww_barb_macro.py                 ║
║                                                           ║
║   POUR LE HOLD WHIRLWIND :                                ║
║   → Dans D4 : Paramètres → Contrôles → Clavier            ║
║   → Ajoute une touche secondaire pour Whirlwind (ex: 5)   ║
║   → Configure cette touche dans les Settings ⚙            ║
╚═══════════════════════════════════════════════════════════╝
"""

import tkinter as tk
import threading, queue, time, json, os, sys, random, winsound
import i18n

try:
    from pynput import keyboard as pynput_kb
    from pynput.keyboard import Controller as KbCtrl, KeyCode, Key
except ImportError:
    print("ERREUR : pip install pynput")
    sys.exit(1)

# ── COULEURS BOUTONS XBOX ─────────────────────────────────────────────────────
XBOX = {
    "A":  ("#1f6b1f", "#55cc55"),   # (off_bg, on_bg)
    "B":  ("#6b1f1f", "#cc4444"),
    "X":  ("#1a3f6b", "#4488cc"),
    "Y":  ("#6b5500", "#ccaa00"),
    "RB": ("#333344", "#8888aa"),
    "LB": ("#333344", "#8888aa"),
    "RT": ("#442255", "#9944bb"),
    "LT": ("#442255", "#9944bb"),
}

def xbox_colors(label, active):
    off, on = XBOX.get(label.upper(), ("#222233", "#666677"))
    return (on, "#ffffff") if active else (off, "#666677")

# ── CONFIG ────────────────────────────────────────────────────────────────────
CONFIG_DIR  = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "DoktorP3st")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
os.makedirs(CONFIG_DIR, exist_ok=True)

DEFAULT_CONFIG = {
    "lang":             "fr",
    "toggle_key":       "F1",
    "overlay_pos":      {"x": 20, "y": 200},
    "press_duration_ms": 120,       # durée de chaque frappe (ms)
    "press_gap_ms":      60,        # délai minimum entre deux frappes
    "whirlwind_hold": {
        "ctrl_label":    "A",       # bouton manette affiché
        "vk":            0x35,      # touche clavier secondaire D4 (défaut: 5)
        "key_label":     "5",
        "ww_interval_ms": 80,       # délai entre chaque appui WW (ms)
        "enabled":       False,     # activer dans Settings ⚙
    },
    "potion": {
        "enabled":    False,
        "key_label":  "Q",
        "vk":         0x51,
        "interval_s": 8.0,
    },
    "skills": [
        # Les 5 skills gérés par cooldown timer
        {"name": "Iron Skin",     "ctrl_label": "X",  "vk": 0x36, "key_label": "6", "cd": 14.0, "color": "#4488cc", "enabled": True},
        {"name": "Rallying Cry",  "ctrl_label": "Y",  "vk": 0x31, "key_label": "1", "cd":  5.1, "color": "#ccaa00", "enabled": True},
        {"name": "War Cry",       "ctrl_label": "RB", "vk": 0x34, "key_label": "4", "cd": 25.0, "color": "#cc4444", "enabled": True},
        {"name": "Chall. Shout",  "ctrl_label": "LT", "vk": 0x33, "key_label": "3", "cd": 25.0, "color": "#9944bb", "enabled": True},
        {"name": "Call Ancients", "ctrl_label": "RT", "vk": 0x32, "key_label": "2", "cd": 50.0, "color": "#33aa66", "enabled": True},
    ]
}

VK_MAP = {
    "1":0x31,"2":0x32,"3":0x33,"4":0x34,"5":0x35,
    "6":0x36,"7":0x37,"8":0x38,"9":0x39,"0":0x30,
    "Q":0x51,"W":0x57,"E":0x45,"R":0x52,"T":0x54,
    "Y":0x59,"U":0x55,"I":0x49,"O":0x4F,"P":0x50,
    "A":0x41,"S":0x53,"D":0x44,"F":0x46,"G":0x47,
    "H":0x48,"J":0x4A,"K":0x4B,"L":0x4C,"Z":0x5A,
    "X":0x58,"C":0x43,"V":0x56,"B":0x42,"N":0x4E,"M":0x4D,
}

def load_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                cfg = json.load(f)
            i18n.load(cfg.get("lang", "fr"))
            return cfg
        except Exception:
            pass
    i18n.load("fr")
    return json.loads(json.dumps(DEFAULT_CONFIG))

def save_cfg(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

# ── KEY SENDER (file unique — évite les frappes simultanées) ─────────────────
#
#   Toutes les frappes passent par une seule file d'attente traitée
#   par un thread dédié → le jeu reçoit les touches l'une après l'autre,
#   jamais en simultané, ce qui maximise la détection même pendant Whirlwind.
#
_kb       = KbCtrl()
_key_q    = queue.Queue()
_gap_ms   = DEFAULT_CONFIG["press_gap_ms"]

def _sender_loop():
    while True:
        item = _key_q.get()
        if item is None:
            break
        vk, hold_ms = item
        key = KeyCode.from_vk(vk)
        _kb.press(key)
        time.sleep(hold_ms / 1000.0)
        _kb.release(key)
        time.sleep(_gap_ms / 1000.0)   # gap minimal entre frappes
        _key_q.task_done()

_sender_thread = threading.Thread(target=_sender_loop, daemon=True)
_sender_thread.start()

def enqueue_key(vk, hold_ms):
    """Ajoute une frappe dans la file — non bloquant."""
    _key_q.put((vk, hold_ms))

def _j(seconds):
    """Ajoute ±12ms de jitter aléatoire à une durée en secondes."""
    return seconds + random.uniform(-0.012, 0.012)


# ── SKILL STATE ───────────────────────────────────────────────────────────────
class Skill:
    def __init__(self, s):
        self.name       = s["name"]
        self.ctrl_label = s.get("ctrl_label", "?")
        self.vk         = s["vk"]
        self.cd         = s["cd"]
        self.color      = s["color"]
        self.enabled    = s.get("enabled", True)
        self.remaining  = 0.0
        self._lock      = threading.Lock()

    def trigger(self):
        with self._lock:
            self.remaining = self.cd

    def update(self, dt):
        with self._lock:
            if self.remaining > 0:
                self.remaining = max(0.0, self.remaining - dt)

    @property
    def ready(self):
        with self._lock:
            return self.remaining <= 0

    @property
    def progress(self):
        with self._lock:
            if self.remaining <= 0:
                return 1.0
            return 1.0 - self.remaining / self.cd

# ── MACRO ENGINE ──────────────────────────────────────────────────────────────
class Engine:
    def __init__(self, cfg):
        self.cfg              = cfg
        self.active           = False
        self.skills           = [Skill(s) for s in cfg["skills"] if s.get("enabled", True)]
        self.potion_remaining = 0.0
        self.potion_interval  = cfg.get("potion", {}).get("interval_s", 8.0)
        self._ww_key          = None

    def reload(self, cfg):
        was = self.active
        if was:
            self.stop()
            time.sleep(0.1)   # laisse le thread WW relâcher la touche
        self.cfg     = cfg
        self.skills  = [Skill(s) for s in cfg["skills"] if s.get("enabled", True)]
        self._ww_key = None
        if was: self.start()

    def start(self):
        self.active = True
        ms  = self.cfg.get("press_duration_ms", 120)
        ww  = self.cfg.get("whirlwind_hold", {})
        pot = self.cfg.get("potion", {})

        # 1. Opener intelligent : tous les buffs d'abord, WW démarre après
        opener_done = threading.Event()

        def opener():
            for i, sk in enumerate(self.skills):
                time.sleep(_j(i * 0.18))
                if self.active:
                    enqueue_key(sk.vk, ms)
                    sk.trigger()
            opener_done.set()

        threading.Thread(target=opener, daemon=True).start()

        # 2. Whirlwind — vrai hold : touche maintenue enfoncée jusqu'au stop
        if ww.get("enabled", False):
            ww_key = KeyCode.from_vk(ww["vk"])
            self._ww_key = ww_key
            def ww_hold():
                opener_done.wait()
                time.sleep(0.1)
                pressed = False
                if self.active:
                    _kb.press(ww_key)
                    pressed = True
                while self.active:
                    time.sleep(0.05)
                if pressed:
                    _kb.release(ww_key)
                self._ww_key = None
            threading.Thread(target=ww_hold, daemon=True).start()

        # 3. Boucle cyclique par skill
        def cycle(sk, delay):
            time.sleep(_j(delay + sk.cd))
            while self.active:
                enqueue_key(sk.vk, ms)
                sk.trigger()
                time.sleep(_j(sk.cd))

        for i, sk in enumerate(self.skills):
            threading.Thread(target=cycle, args=(sk, i * 0.18), daemon=True).start()

        # 4. Potion automatique
        if pot.get("enabled", False):
            iv = pot.get("interval_s", 8.0)
            self.potion_interval  = iv
            self.potion_remaining = iv
            def pot_loop():
                while self.active:
                    time.sleep(0.05)
                    self.potion_remaining = max(0.0, self.potion_remaining - 0.05)
                    if self.potion_remaining <= 0 and self.active:
                        enqueue_key(pot["vk"], ms)
                        self.potion_remaining = iv + random.uniform(-0.3, 0.3)
            threading.Thread(target=pot_loop, daemon=True).start()

    def stop(self):
        self.active = False
        for sk in self.skills:
            sk.remaining = 0.0

    def update(self, dt):
        if self.active:
            for sk in self.skills:
                sk.update(dt)

# ── SETTINGS WINDOW ───────────────────────────────────────────────────────────
class Settings:
    def __init__(self, parent, cfg, on_save):
        self.cfg      = json.loads(json.dumps(cfg))
        self.on_save  = on_save
        self.rows_v   = []
        self.win = tk.Toplevel(parent)
        self.win.title("⚙ Settings — WW Barb")
        self.win.configure(bg="#0c0c14")
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)
        self.win.geometry("620x740")
        self._build()

    def _lbl(self, p, t, **kw):
        return tk.Label(p, text=t, bg="#0c0c14",
                        font=("Courier", 9), fg="#aaaaaa", **kw)

    def _entry(self, p, var, w=6, fg="#ffffff", size=9):
        return tk.Entry(p, textvariable=var, width=w,
                        font=("Courier", size), bg="#1a1a2e", fg=fg,
                        insertbackground="white", relief="flat")

    def _build(self):
        tk.Label(self.win, text=i18n.t("settings.title"),
                 font=("Courier",12,"bold"), fg="#e94560", bg="#0c0c14"
                 ).pack(pady=(12,4))

        # Sélecteur de langue — radio buttons (code direct, pas de pb d'encodage)
        lang_row = tk.Frame(self.win, bg="#13131f", pady=5)
        lang_row.pack(fill="x", padx=12, pady=(0,6))
        self._lbl(lang_row, i18n.t("settings.lang_label")).pack(side="left", padx=8)
        self.lang_var = tk.StringVar(value=i18n.current())
        for code, name in i18n.LANGUAGES.items():
            tk.Radiobutton(lang_row, text=name, variable=self.lang_var, value=code,
                           font=("Courier",9), fg="#cccccc", bg="#13131f",
                           activebackground="#13131f", activeforeground="#ffffff",
                           selectcolor="#1a1a2e", relief="flat"
                           ).pack(side="left", padx=(0,8))
        self.lang_var.trace_add("write", self._reload_language)

        # Réglages globaux
        top = tk.Frame(self.win, bg="#13131f", pady=6)
        top.pack(fill="x", padx=12, pady=(0,8))

        self._lbl(top, i18n.t("settings.toggle_key")).pack(side="left", padx=8)
        self.tv = tk.StringVar(value=self.cfg.get("toggle_key","F1"))
        self._entry(top, self.tv, 5).pack(side="left", padx=4)

        self._lbl(top, i18n.t("settings.press_dur")).pack(side="left", padx=(16,0))
        self.dv = tk.StringVar(value=str(self.cfg.get("press_duration_ms",120)))
        self._entry(top, self.dv, 5).pack(side="left", padx=4)

        # Section Whirlwind
        ww_frame = tk.Frame(self.win, bg="#1a2a1a", pady=8)
        ww_frame.pack(fill="x", padx=12, pady=(0,8))

        tk.Label(ww_frame, text=i18n.t("settings.ww_section"),
                 font=("Courier",10,"bold"), fg="#55cc55", bg="#1a2a1a"
                 ).pack(anchor="w", padx=10, pady=(0,4))

        ww = self.cfg.get("whirlwind_hold", DEFAULT_CONFIG["whirlwind_hold"])
        row = tk.Frame(ww_frame, bg="#1a2a1a")
        row.pack(fill="x", padx=10)

        self.ww_en = tk.BooleanVar(value=ww.get("enabled", False))
        tk.Checkbutton(row, text=i18n.t("settings.ww_enable"),
                        variable=self.ww_en,
                        font=("Courier",9), fg="#88cc88", bg="#1a2a1a",
                        activebackground="#1a2a1a", selectcolor="#0a1a0a"
                        ).pack(side="left")

        self._lbl(ww_frame, i18n.t("settings.ww_ctrl")).pack(anchor="w", padx=10, pady=(6,0))

        r2 = tk.Frame(ww_frame, bg="#1a2a1a")
        r2.pack(fill="x", padx=10, pady=2)
        self.ww_ctrl = tk.StringVar(value=ww.get("ctrl_label","A"))
        self._entry(r2, self.ww_ctrl, 4, "#ffd700").pack(side="left", padx=4)

        self._lbl(r2, i18n.t("settings.ww_key")).pack(side="left", padx=(16,0))
        self.ww_key = tk.StringVar(value=ww.get("key_label","5"))
        self._entry(r2, self.ww_key, 4, "#aaffaa").pack(side="left", padx=4)

        r3 = tk.Frame(ww_frame, bg="#1a2a1a")
        r3.pack(fill="x", padx=10, pady=(4,0))
        self._lbl(r3, i18n.t("settings.ww_interval")).pack(side="left")
        self.ww_iv = tk.StringVar(value=str(ww.get("ww_interval_ms", 80)))
        self._entry(r3, self.ww_iv, 5, "#aaffaa").pack(side="left", padx=4)
        tk.Label(r3, text=i18n.t("settings.ww_jitter"), font=("Courier",8),
                 fg="#446644", bg="#1a2a1a").pack(side="left", padx=(8,0))

        tk.Label(ww_frame, text=i18n.t("settings.ww_hint"),
                 font=("Courier",7), fg="#446644", bg="#1a2a1a"
                 ).pack(anchor="w", padx=10, pady=(4,0))

        # Section Potion
        pot_frame = tk.Frame(self.win, bg="#2a1a0a", pady=8)
        pot_frame.pack(fill="x", padx=12, pady=(0,8))

        tk.Label(pot_frame, text=i18n.t("settings.pot_section"),
                 font=("Courier",10,"bold"), fg="#ff8844", bg="#2a1a0a"
                 ).pack(anchor="w", padx=10, pady=(0,4))

        pot = self.cfg.get("potion", DEFAULT_CONFIG["potion"])
        pr = tk.Frame(pot_frame, bg="#2a1a0a")
        pr.pack(fill="x", padx=10)

        self.pot_en = tk.BooleanVar(value=pot.get("enabled", False))
        tk.Checkbutton(pr, text=i18n.t("settings.pot_enable"),
                       variable=self.pot_en,
                       font=("Courier",9), fg="#ffaa66", bg="#2a1a0a",
                       activebackground="#2a1a0a", selectcolor="#1a0a00"
                       ).pack(side="left")

        pr2 = tk.Frame(pot_frame, bg="#2a1a0a")
        pr2.pack(fill="x", padx=10, pady=(4,0))
        self._lbl(pr2, i18n.t("settings.pot_key")).pack(side="left")
        self.pot_key = tk.StringVar(value=pot.get("key_label","Q"))
        self._entry(pr2, self.pot_key, 4, "#ffcc88").pack(side="left", padx=4)

        self._lbl(pr2, i18n.t("settings.pot_interval")).pack(side="left", padx=(16,0))
        self.pot_iv = tk.StringVar(value=str(pot.get("interval_s", 8.0)))
        self._entry(pr2, self.pot_iv, 5, "#ffcc88").pack(side="left", padx=4)

        # Tableau skills — grid layout
        sf = tk.Frame(self.win, bg="#0c0c14")
        sf.pack(fill="x", padx=12, pady=(8,0))
        sf.columnconfigure(1, weight=1, minsize=130)

        headers = [
            i18n.t("settings.col_order"), i18n.t("settings.col_skill"),
            i18n.t("settings.col_ctrl"),  i18n.t("settings.col_key"),
            i18n.t("settings.col_cd"),    i18n.t("settings.col_on"),
        ]
        for col, txt in enumerate(headers):
            tk.Label(sf, text=txt, font=("Courier",11,"bold"),
                     fg="#556677", bg="#0c0c14", anchor="w"
                     ).grid(row=0, column=col, padx=(6,4), pady=(4,6), sticky="w")
        tk.Frame(sf, bg="#223344", height=1
                 ).grid(row=1, column=0, columnspan=6, sticky="ew", padx=4, pady=(0,4))

        self.rows_v = []
        for i, sk in enumerate(self.cfg["skills"]):
            r = i * 2 + 2

            af = tk.Frame(sf, bg="#0c0c14")
            af.grid(row=r, column=0, padx=(6,2), pady=6, sticky="w")
            tk.Button(af, text="▲", font=("Courier",8), fg="#445566",
                      bg="#1a1a2e", relief="flat", width=2,
                      command=lambda i=i: self._move(i,-1)).pack()
            tk.Button(af, text="▼", font=("Courier",8), fg="#445566",
                      bg="#1a1a2e", relief="flat", width=2,
                      command=lambda i=i: self._move(i,1)).pack()

            nv = tk.StringVar(value=sk["name"])
            self._entry(sf, nv, 14, "#eeeeee", size=11
                        ).grid(row=r, column=1, padx=(4,6), pady=6, sticky="ew")

            cv = tk.StringVar(value=sk.get("ctrl_label","?"))
            self._entry(sf, cv, 5, "#ffd700", size=11
                        ).grid(row=r, column=2, padx=4, pady=6, sticky="ew")

            kv = tk.StringVar(value=sk.get("key_label","?"))
            self._entry(sf, kv, 5, "#aaaacc", size=11
                        ).grid(row=r, column=3, padx=4, pady=6, sticky="ew")

            cdv = tk.StringVar(value=str(sk["cd"]))
            self._entry(sf, cdv, 6, "#f59e0b", size=11
                        ).grid(row=r, column=4, padx=4, pady=6, sticky="ew")

            env = tk.BooleanVar(value=sk.get("enabled",True))
            tk.Checkbutton(sf, variable=env, bg="#0c0c14",
                            activebackground="#0c0c14", selectcolor="#1a1a2e"
                            ).grid(row=r, column=5, padx=4, pady=6)

            tk.Frame(sf, bg="#1c1c2c", height=1
                     ).grid(row=r+1, column=0, columnspan=6, sticky="ew", padx=4)

            self.rows_v.append((nv, cv, kv, cdv, env))

        # Boutons
        btn = tk.Frame(self.win, bg="#0c0c14")
        btn.pack(pady=14)
        tk.Button(btn, text=i18n.t("settings.btn_save"), font=("Courier",10,"bold"),
                  fg="#fff", bg="#10b981", relief="flat", padx=14, pady=7,
                  command=self._save).pack(side="left", padx=8)
        tk.Button(btn, text=i18n.t("settings.btn_cancel"), font=("Courier",10),
                  fg="#aaa", bg="#1a1a2e", relief="flat", padx=14, pady=7,
                  command=self.win.destroy).pack(side="left", padx=8)

    def _move(self, idx, d):
        sk = self.cfg["skills"]
        ni = idx + d
        if 0 <= ni < len(sk):
            sk[idx], sk[ni] = sk[ni], sk[idx]
            self._read_form()
            self.win.destroy()
            Settings(None, self.cfg, self.on_save)

    def _read_form(self):
        """Lit les valeurs du formulaire dans self.cfg sans sauvegarder."""
        try:
            self.cfg["lang"]             = self.lang_var.get()
            self.cfg["toggle_key"]       = self.tv.get().strip()
            self.cfg["press_duration_ms"] = int(self.dv.get())

            pot_kl = self.pot_key.get().strip().upper()
            self.cfg["potion"] = {
                "enabled":    self.pot_en.get(),
                "key_label":  pot_kl,
                "vk":         VK_MAP.get(pot_kl, 0x51),
                "interval_s": float(self.pot_iv.get()),
            }

            ww_kl = self.ww_key.get().strip().upper()
            self.cfg["whirlwind_hold"] = {
                "ctrl_label":    self.ww_ctrl.get().strip().upper(),
                "key_label":     ww_kl,
                "vk":            VK_MAP.get(ww_kl, 0x35),
                "ww_interval_ms": int(self.ww_iv.get()),
                "enabled":       self.ww_en.get(),
            }

            for i, (nv, cv, kv, cdv, env) in enumerate(self.rows_v):
                kl = kv.get().strip().upper()
                self.cfg["skills"][i].update({
                    "name":       nv.get().strip() or self.cfg["skills"][i]["name"],
                    "ctrl_label": cv.get().strip().upper(),
                    "key_label":  kl,
                    "vk":         VK_MAP.get(kl, self.cfg["skills"][i]["vk"]),
                    "cd":         float(cdv.get()),
                    "enabled":    env.get(),
                })
        except Exception:
            pass  # champs partiellement remplis tolérés pendant le switch de langue

    def _reload_language(self, *_):
        """Appelé dès qu'un radio button langue change — recharge la fenêtre instantanément."""
        new_code = self.lang_var.get()
        if not new_code or new_code == i18n.current():
            return
        self._read_form()
        i18n.load(new_code)
        self.cfg["lang"] = new_code
        for w in self.win.winfo_children():
            w.destroy()
        self.rows_v = []
        self._build()

    def _save(self):
        try:
            self._read_form()
            save_cfg(self.cfg)
            self.on_save(self.cfg)
            self.win.destroy()
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror(i18n.t("settings.err_title"), str(e))

# ── MAIN OVERLAY ──────────────────────────────────────────────────────────────
class App:
    W = 265

    def __init__(self):
        self.cfg          = load_cfg()
        self.engine       = Engine(self.cfg)
        self.running      = True
        self._dx = self._dy = 0
        self._anim        = 0
        self._active_since = None

        n = len([s for s in self.cfg["skills"] if s.get("enabled",True)])
        ww_row  = 1 if self.cfg.get("whirlwind_hold",{}).get("enabled",False) else 0
        pot_row = 1 if self.cfg.get("potion",{}).get("enabled",False) else 0
        h = 46 + (n + ww_row + pot_row) * 42 + 30

        pos = self.cfg.get("overlay_pos", {"x": 20, "y": 200})
        self.root = tk.Tk()
        self.root.title("WW Barb")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)
        self.root.geometry(f"{self.W}x{h}+{pos['x']}+{pos['y']}")
        self.root.configure(bg="#0c0c14")

        self._build()
        self._start_loop()
        self._start_hotkey()

    # ── BUILD ─────────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg="#13131f", height=46)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="⚔  WW BARB",
                 font=("Courier",11,"bold"), fg="#e94560", bg="#13131f"
                 ).place(x=10, y=13)

        self.s_dot = tk.Label(hdr, text="●", font=("Courier",14),
                               fg="#1e1e2e", bg="#13131f")
        self.s_dot.place(x=self.W-72, y=11)
        self.s_lbl = tk.Label(hdr, text=i18n.t("overlay.status_off"), font=("Courier",9,"bold"),
                               fg="#1e1e2e", bg="#13131f")
        self.s_lbl.place(x=self.W-54, y=15)

        gear = tk.Label(hdr, text="⚙", font=("Courier",12),
                         fg="#445566", bg="#13131f", cursor="hand2")
        gear.place(x=self.W-30, y=12)
        gear.bind("<Button-1>", lambda e: self._open_settings())

        close = tk.Label(hdr, text="✕", font=("Courier",10),
                          fg="#333355", bg="#13131f", cursor="hand2")
        close.place(x=self.W-14, y=4)
        close.bind("<Button-1>", lambda e: self._quit())

        for w in (hdr, self.root):
            w.bind("<Button-1>", self._ds)
            w.bind("<B1-Motion>", self._dm)

        self.rows = []

        # Whirlwind hold row (si activé)
        ww = self.cfg.get("whirlwind_hold", {})
        self.ww_badge = None
        self.ww_status = None
        if ww.get("enabled", False):
            self._add_ww_row(ww)

        # Potion row (si activée)
        pot = self.cfg.get("potion", {})
        self.pot_badge  = None
        self.pot_canvas = None
        self.pot_lbl    = None
        if pot.get("enabled", False):
            self._add_pot_row(pot)

        # Skill rows
        for sk in self.engine.skills:
            self._add_skill_row(sk)

        # Footer
        footer = tk.Frame(self.root, bg="#13131f", height=30)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        key = self.cfg.get("toggle_key","F1")
        self.f_lbl = tk.Label(footer,
                               text=i18n.t("overlay.footer_idle", key=key),
                               font=("Courier",7), fg="#1e2e3e", bg="#13131f")
        self.f_lbl.pack(side="left", padx=8, pady=8)

    def _add_ww_row(self, ww):
        frame = tk.Frame(self.root, bg="#0a1a0a", height=42)
        frame.pack(fill="x", padx=6)
        frame.pack_propagate(False)
        tk.Frame(frame, bg="#1a3a1a", height=1).pack(fill="x")

        inner = tk.Frame(frame, bg="#0a1a0a")
        inner.pack(fill="both", expand=True)

        # Badge A
        self.ww_badge = tk.Label(inner, text=ww.get("ctrl_label","A"),
                                   font=("Courier",8,"bold"),
                                   fg="#444444", bg="#0c1a0c",
                                   width=3, relief="flat", padx=2)
        self.ww_badge.pack(side="left", padx=(4,3), pady=6)

        tk.Label(inner, text=i18n.t("overlay.ww_label"), font=("Courier",8),
                 fg="#336633", bg="#0a1a0a", anchor="w", width=12
                 ).pack(side="left", padx=2)

        self.ww_canvas = tk.Canvas(inner, width=62, height=14,
                                    bg="#0a1a0a", highlightthickness=0)
        self.ww_canvas.pack(side="left", pady=6)

        self.ww_status = tk.Label(inner, text=i18n.t("overlay.ww_stop"), font=("Courier",8,"bold"),
                                   fg="#336633", bg="#0a1a0a", width=6, anchor="e")
        self.ww_status.pack(side="left", padx=3)

    def _add_pot_row(self, pot):
        frame = tk.Frame(self.root, bg="#1a0a00", height=42)
        frame.pack(fill="x", padx=6)
        frame.pack_propagate(False)
        tk.Frame(frame, bg="#3a1a00", height=1).pack(fill="x")

        inner = tk.Frame(frame, bg="#1a0a00")
        inner.pack(fill="both", expand=True)

        self.pot_badge = tk.Label(inner, text=pot.get("key_label","Q"),
                                   font=("Courier",8,"bold"),
                                   fg="#664422", bg="#1a0a00",
                                   width=3, relief="flat", padx=2)
        self.pot_badge.pack(side="left", padx=(4,3), pady=6)

        tk.Label(inner, text=i18n.t("overlay.pot_label"), font=("Courier",8),
                 fg="#664422", bg="#1a0a00", anchor="w", width=12
                 ).pack(side="left", padx=2)

        self.pot_canvas = tk.Canvas(inner, width=62, height=14,
                                     bg="#1a0a00", highlightthickness=0)
        self.pot_canvas.pack(side="left", pady=6)

        self.pot_lbl = tk.Label(inner, text=i18n.t("overlay.pot_ready"), font=("Courier",8,"bold"),
                                 fg="#ff8844", bg="#1a0a00", width=6, anchor="e")
        self.pot_lbl.pack(side="left", padx=3)

    def _add_skill_row(self, sk):
        frame = tk.Frame(self.root, bg="#0c0c14", height=42)
        frame.pack(fill="x", padx=6)
        frame.pack_propagate(False)
        tk.Frame(frame, bg="#1c1c2c", height=1).pack(fill="x")

        inner = tk.Frame(frame, bg="#0c0c14")
        inner.pack(fill="both", expand=True)

        off_bg, _ = xbox_colors(sk.ctrl_label, False)
        badge = tk.Label(inner, text=sk.ctrl_label,
                          font=("Courier",8,"bold"),
                          fg="#444455", bg=off_bg,
                          width=3, relief="flat", padx=2)
        badge.pack(side="left", padx=(4,3), pady=6)

        tk.Label(inner, text=sk.name, font=("Courier",8),
                 fg="#555566", bg="#0c0c14", anchor="w", width=12
                 ).pack(side="left", padx=2)

        canvas = tk.Canvas(inner, width=62, height=14,
                            bg="#0c0c14", highlightthickness=0)
        canvas.pack(side="left", pady=6)

        t_lbl = tk.Label(inner, text=i18n.t("overlay.skill_ready"), font=("Courier",8,"bold"),
                          fg="#10b981", bg="#0c0c14", width=6, anchor="e")
        t_lbl.pack(side="left", padx=3)

        self.rows.append((badge, canvas, t_lbl, sk))

    # ── LOOP ──────────────────────────────────────────────────────────────────
    def _start_loop(self):
        self._last = time.time()

        def loop():
            while self.running:
                now = time.time()
                self.engine.update(now - self._last)
                self._last = now
                self._anim = (self._anim + 1) % 30
                try:
                    self.root.after(0, self._refresh)
                except Exception:
                    break
                time.sleep(0.033)

        threading.Thread(target=loop, daemon=True).start()

    def _refresh(self):
        active = self.engine.active

        # Timer de session
        if active and self._active_since:
            elapsed = int(time.time() - self._active_since)
            m, s = divmod(elapsed, 60)
            self.f_lbl.config(text=i18n.t("overlay.footer_active", m=m, s=s), fg="#ccaa00")

        ww_en  = self.cfg.get("whirlwind_hold",{}).get("enabled", False)
        ww_lbl = self.cfg.get("whirlwind_hold",{}).get("ctrl_label","A")

        # Whirlwind hold row
        if self.ww_badge and self.ww_status:
            ww_active = active and ww_en
            off_bg, on_bg = xbox_colors(ww_lbl, ww_active)
            if ww_active:
                self.ww_badge.config(bg=on_bg, fg="#ffffff")
                dots = "·" * (self._anim // 6 + 1)
                self.ww_status.config(text=i18n.t("overlay.ww_spinning") + dots[:3], fg="#55cc55")
                # Barre animée
                self.ww_canvas.delete("all")
                self.ww_canvas.create_rectangle(0,0,62,14, fill="#0a2a0a", outline="#1a3a1a")
                x = int(30 + 28 * __import__("math").sin(self._anim * 0.4))
                self.ww_canvas.create_oval(x-5,2,x+5,12, fill="#33aa33", outline="")
            else:
                self.ww_badge.config(bg="#0c1a0c", fg="#336633")
                self.ww_status.config(text=i18n.t("overlay.ww_stop"), fg="#335533")
                self.ww_canvas.delete("all")
                self.ww_canvas.create_rectangle(0,0,62,14, fill="#0a1a0a", outline="")

        # Potion row
        if self.pot_badge and self.pot_canvas and self.pot_lbl:
            pot_cfg = self.cfg.get("potion", {})
            iv = self.engine.potion_interval or pot_cfg.get("interval_s", 8.0)
            rem = self.engine.potion_remaining
            if active and pot_cfg.get("enabled", False):
                self.pot_badge.config(fg="#ff8844" if rem <= 0 else "#664422")
                self.pot_canvas.delete("all")
                self.pot_canvas.create_rectangle(0,0,62,14, fill="#2a1000", outline="#3a1a00")
                prog = 1.0 - (rem / iv) if iv > 0 else 1.0
                bw = int(60 * max(0.0, min(1.0, prog)))
                if bw > 1:
                    self.pot_canvas.create_rectangle(1,1,1+bw-1,13, fill="#cc5500", outline="")
                if rem <= 0:
                    self.pot_lbl.config(text=i18n.t("overlay.pot_ready"), fg="#ff8844")
                else:
                    self.pot_lbl.config(
                        text=f"{rem:.1f}s" if rem < 10 else f" {int(rem)}s",
                        fg="#dd3333" if rem < 2 else "#774422")
            else:
                self.pot_badge.config(fg="#331100")
                self.pot_canvas.delete("all")
                self.pot_canvas.create_rectangle(0,0,62,14, fill="#1a0a00", outline="")
                self.pot_lbl.config(text=i18n.t("overlay.inactive"), fg="#1e1e2e")

        # Skill rows
        for badge, canvas, t_lbl, sk in self.rows:
            off_bg, on_bg = xbox_colors(sk.ctrl_label, active and sk.ready)

            if active and sk.ready:
                badge.config(bg=on_bg, fg="#ffffff")
            else:
                badge.config(bg=off_bg, fg="#444455")

            canvas.delete("all")
            if not active:
                canvas.create_rectangle(0,0,62,14, fill="#0c0c14", outline="")
                t_lbl.config(text=i18n.t("overlay.inactive"), fg="#1e1e2e")
                continue

            canvas.create_rectangle(0,0,62,14, fill="#1a1a2e", outline="#222233")
            bw = int(60 * sk.progress)

            if sk.ready:
                canvas.create_rectangle(1,1,61,13, fill=sk.color, outline="")
                t_lbl.config(text=i18n.t("overlay.skill_ready"), fg=sk.color)
            else:
                if bw > 1:
                    canvas.create_rectangle(1,1,1+bw-1,13, fill=sk.color, outline="")
                r = sk.remaining
                t_lbl.config(
                    text=f" {r:.1f}s" if r < 10 else f"  {int(r)}s",
                    fg="#dd3333" if r < 3 else "#666677"
                )

    # ── TOGGLE ────────────────────────────────────────────────────────────────
    def _start_hotkey(self):
        ks  = self.cfg.get("toggle_key","F1").lower()
        tok = getattr(Key, ks, None)

        def on_press(key):
            if key == tok:
                self.root.after(0, self._toggle)
            elif key == Key.esc and self.engine.active:
                self.root.after(0, self._toggle)

        l = pynput_kb.Listener(on_press=on_press)
        l.daemon = True
        l.start()

    def _toggle(self):
        if self.engine.active:
            self.engine.stop()
            self._active_since = None
            self.s_dot.config(fg="#1e1e2e")
            self.s_lbl.config(text=i18n.t("overlay.status_off"), fg="#1e1e2e")
            key = self.cfg.get("toggle_key","F1")
            self.f_lbl.config(text=i18n.t("overlay.footer_idle", key=key), fg="#1e2e3e")
            threading.Thread(target=lambda: winsound.Beep(440, 120), daemon=True).start()
        else:
            self.engine.start()
            self._active_since = time.time()
            self.s_dot.config(fg="#10b981")
            self.s_lbl.config(text=i18n.t("overlay.status_on"), fg="#10b981")
            threading.Thread(target=lambda: winsound.Beep(880, 80), daemon=True).start()

    # ── SETTINGS ──────────────────────────────────────────────────────────────
    def _open_settings(self):
        def on_save(cfg):
            self.cfg = cfg
            global _gap_ms
            _gap_ms  = cfg.get("press_gap_ms", 60)
            self.engine.reload(cfg)
            self._rebuild()

        Settings(self.root, self.cfg, on_save)

    def _rebuild(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.rows      = []
        self.ww_badge  = None
        self.ww_status = None
        self.pot_badge  = None
        self.pot_canvas = None
        self.pot_lbl    = None
        n     = len([s for s in self.cfg["skills"] if s.get("enabled",True)])
        ww_r  = 1 if self.cfg.get("whirlwind_hold",{}).get("enabled",False) else 0
        pot_r = 1 if self.cfg.get("potion",{}).get("enabled",False) else 0
        self.root.geometry(f"{self.W}x{46+(n+ww_r+pot_r)*42+30}")
        self._build()

    # ── DRAG ──────────────────────────────────────────────────────────────────
    def _ds(self, e): self._dx, self._dy = e.x, e.y
    def _dm(self, e):
        nx = self.root.winfo_x() + e.x - self._dx
        ny = self.root.winfo_y() + e.y - self._dy
        self.root.geometry(f"+{nx}+{ny}")
        self.cfg["overlay_pos"] = {"x": nx, "y": ny}

    def _quit(self):
        self.running = False
        self.engine.stop()
        self.cfg["overlay_pos"] = {
            "x": self.root.winfo_x(),
            "y": self.root.winfo_y(),
        }
        save_cfg(self.cfg)
        _key_q.put(None)
        self.root.after(0, self.root.destroy)

    def run(self):
        self.root.mainloop()

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import math   # pour l'animation WW
    print("▶  WW Barb Macro v3 — Controller Display + WW Hold + Hardware Keys")
    print(f"   Config : {CONFIG_FILE}")
    print("   ⚙  Clique l'engrenage pour configurer\n")
    print("   BOUTONS MANETTE PAR DÉFAUT :")
    print("   X=Iron Skin  Y=Rallying  RB=War Cry  LT=Chall.  RT=Ancients  A=Whirlwind\n")
    App().run()
