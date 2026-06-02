"""
RxCards Launcher
Double-click to start. Works on Mac and Windows.
Save as launcher.pyw on Windows (hides console window).
"""
import tkinter as tk
from tkinter import font as tkfont
import subprocess, sys, os, threading, time, webbrowser, socket

PORT     = 5000
URL      = f"http://localhost:{PORT}"
APP_DIR  = os.path.dirname(os.path.abspath(__file__))
APP_PY   = os.path.join(APP_DIR, "app.py")

# ── Colors matching the card creator dark theme ────────────────────────────────
BG       = "#0d1526"
SURFACE  = "#111e33"
PANEL    = "#152035"
BORDER   = "#1e3050"
ACCENT   = "#4a8fe8"
ACCENT2  = "#2563c4"
GREEN    = "#3ecf8e"
RED      = "#f06060"
GOLD     = "#e8b84a"
TEXT     = "#c8d8f0"
MUTED    = "#4a6080"
SUBTLE   = "#8096b8"


def is_port_open():
    try:
        s = socket.create_connection(("localhost", PORT), timeout=0.5)
        s.close()
        return True
    except OSError:
        return False


def check_deps():
    """Return list of missing packages."""
    missing = []
    for pkg in ("flask", "reportlab"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    return missing


class RxLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RxCards")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self._center(360, 240)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.server_proc = None
        self.status_var  = tk.StringVar(value="Starting…")
        self.dot_var     = tk.StringVar(value="●")
        self.dot_color   = GOLD

        self._build_ui()
        self.root.after(100, self._auto_start)

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Outer padding frame
        outer = tk.Frame(self.root, bg=BG, padx=24, pady=20)
        outer.pack(fill="both", expand=True)

        # Logo + title row
        header = tk.Frame(outer, bg=BG)
        header.pack(fill="x", pady=(0, 18))

        logo_canvas = tk.Canvas(header, width=44, height=44,
                                bg=BG, highlightthickness=0)
        logo_canvas.pack(side="left", padx=(0, 12))
        logo_canvas.create_rectangle(0, 0, 44, 44, fill=ACCENT2,
                                     outline=ACCENT, width=1)
        logo_canvas.create_text(22, 22, text="Rx", fill="white",
                                font=("Helvetica", 16, "bold"))

        title_frame = tk.Frame(header, bg=BG)
        title_frame.pack(side="left")
        tk.Label(title_frame, text="RxCards", bg=BG, fg="white",
                 font=("Helvetica", 18, "bold")).pack(anchor="w")
        tk.Label(title_frame, text="Drug Card Creator", bg=BG, fg=SUBTLE,
                 font=("Helvetica", 10)).pack(anchor="w")

        # Status row
        status_frame = tk.Frame(outer, bg=SURFACE,
                                highlightbackground=BORDER,
                                highlightthickness=1)
        status_frame.pack(fill="x", pady=(0, 16))
        inner_status = tk.Frame(status_frame, bg=SURFACE, padx=14, pady=10)
        inner_status.pack(fill="x")

        self.dot_label = tk.Label(inner_status, textvariable=self.dot_var,
                                  bg=SURFACE, fg=self.dot_color,
                                  font=("Helvetica", 13))
        self.dot_label.pack(side="left", padx=(0, 8))

        self.status_label = tk.Label(inner_status, textvariable=self.status_var,
                                     bg=SURFACE, fg=TEXT,
                                     font=("Helvetica", 11))
        self.status_label.pack(side="left")

        # Buttons
        btn_frame = tk.Frame(outer, bg=BG)
        btn_frame.pack(fill="x")

        self.open_btn = self._make_btn(btn_frame, "Open in Browser",
                                       ACCENT2, ACCENT, self._open_browser,
                                       state="disabled")
        self.open_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))

        self.toggle_btn = self._make_btn(btn_frame, "Stop Server",
                                         "#1a2e4a", BORDER, self._toggle_server)
        self.toggle_btn.pack(side="left", expand=True, fill="x")

        # Footer
        tk.Label(outer, text=f"Runs at  {URL}",
                 bg=BG, fg=MUTED, font=("Helvetica", 9)).pack(pady=(14, 0))

    def _make_btn(self, parent, text, bg, border, cmd, state="normal"):
        btn = tk.Button(parent, text=text, bg=bg, fg="white",
                        activebackground=ACCENT, activeforeground="white",
                        relief="flat", bd=0, padx=14, pady=8,
                        font=("Helvetica", 11, "bold"),
                        highlightbackground=border, highlightthickness=1,
                        cursor="hand2", command=cmd, state=state)
        return btn

    def _center(self, w, h):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x  = (sw - w) // 2
        y  = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ── Server management ──────────────────────────────────────────────────────
    def _auto_start(self):
        """Called once on launch — check deps then start."""
        missing = check_deps()
        if missing:
            self._set_status("Installing dependencies…", GOLD)
            threading.Thread(target=self._install_and_start,
                             args=(missing,), daemon=True).start()
        else:
            threading.Thread(target=self._start_server, daemon=True).start()

    def _install_and_start(self, packages):
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install",
                 "--break-system-packages", "--quiet"] + packages,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            self.root.after(0, lambda: self._set_status(
                "Install failed — run:  pip install flask reportlab", RED))
            return
        self._start_server()

    def _start_server(self):
        self.root.after(0, lambda: self._set_status("Starting server…", GOLD))
        try:
            self.server_proc = subprocess.Popen(
                [sys.executable, APP_PY],
                cwd=APP_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            self.root.after(0, lambda: self._set_status(
                "app.py not found — keep launcher in the same folder", RED))
            return

        # Poll until server responds (up to 10s)
        for _ in range(20):
            if is_port_open():
                self.root.after(0, self._on_server_up)
                return
            time.sleep(0.5)

        self.root.after(0, lambda: self._set_status("Server timed out", RED))

    def _on_server_up(self):
        self._set_status("Server running", GREEN)
        self.open_btn.config(state="normal")
        self.toggle_btn.config(text="Stop Server")
        webbrowser.open(URL)

    def _toggle_server(self):
        if self.server_proc and self.server_proc.poll() is None:
            # Server is running — stop it
            self.server_proc.terminate()
            self.server_proc = None
            self._set_status("Server stopped", RED)
            self.open_btn.config(state="disabled")
            self.toggle_btn.config(text="Start Server")
        else:
            # Server is stopped — start it
            self.toggle_btn.config(text="Stop Server")
            threading.Thread(target=self._start_server, daemon=True).start()

    def _open_browser(self):
        webbrowser.open(URL)

    def _set_status(self, text, color=TEXT):
        self.status_var.set(text)
        self.dot_label.config(fg=color)
        if color == GREEN:   self.dot_var.set("●")
        elif color == RED:   self.dot_var.set("●")
        else:                self.dot_var.set("◌")

    def _on_close(self):
        if self.server_proc and self.server_proc.poll() is None:
            self.server_proc.terminate()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = RxLauncher()
    app.run()
