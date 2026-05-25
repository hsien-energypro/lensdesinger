# -*- coding: utf-8 -*-
"""
LensDesignerPro.py
達源技術有限公司 透鏡成像產生器 - Confirmed V10 Geometry

Features:
- Clean desktop GUI
- Parameter panel
- XZ air lens preview
- XY output surface preview
- Ground iso-illuminance simulation
- Center-line platform plot
- Export STEP / STL after simulation check

Confirmed coordinate system:
X = 0 ~ L
Y = 0 ~ 40
Z = -30 ~ +30

Confirmed V10 geometry baseline:
L=100, YH=40, ZW=60
La=24, Lb=44, Ra=72, z_half=18
continuous XZ hourglass air lens
P1~P5 XY output surface cut
XY + XZ TIR cuts included
"""

import math
import os
import tkinter as tk
from tkinter import filedialog, messagebox

import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

try:
    import cadquery as cq
except Exception as e:
    cq = None
    CADQUERY_ERROR = e
else:
    CADQUERY_ERROR = None


APP_BG = "#101820"
PANEL_BG = "#17212B"
CARD_BG = "#1F2B38"
TEXT_FG = "#EAF2F8"
MUTED_FG = "#AAB7C4"
ACCENT = "#2F80ED"
GOOD = "#27AE60"
WARN = "#F2C94C"
BAD = "#EB5757"


class LensDesignerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("達源技術有限公司 透鏡成像產生器")
        self.root.geometry("1360x850")
        self.root.minsize(1220, 780)
        self.root.configure(bg=APP_BG)

        self.output_dir = tk.StringVar(value=os.path.abspath(os.getcwd()))

        # Main geometry variables
        self.vars = {
            "L": tk.DoubleVar(value=100.0),
            "YH": tk.DoubleVar(value=40.0),
            "ZW": tk.DoubleVar(value=60.0),
            "La": tk.DoubleVar(value=24.0),
            "Lb": tk.DoubleVar(value=44.0),
            "Ra": tk.DoubleVar(value=72.0),
            "z_half": tk.DoubleVar(value=18.0),
        }

        # Output P1~P5 XY curve
        self.pvars = {
            "P1_X": tk.DoubleVar(value=78.0),  "P1_Y": tk.DoubleVar(value=0.0),
            "P2_X": tk.DoubleVar(value=84.0),  "P2_Y": tk.DoubleVar(value=7.0),
            "P3_X": tk.DoubleVar(value=90.0),  "P3_Y": tk.DoubleVar(value=18.0),
            "P4_X": tk.DoubleVar(value=95.0),  "P4_Y": tk.DoubleVar(value=30.0),
            "P5_X": tk.DoubleVar(value=100.0), "P5_Y": tk.DoubleVar(value=39.0),
        }

        self.last_simulation_ok = False
        self.build_ui()
        self.run_simulation()

    # ---------------- UI helpers ----------------
    def label(self, parent, text, size=10, bold=False, fg=TEXT_FG, bg=None):
        return tk.Label(
            parent,
            text=text,
            font=("Segoe UI", size, "bold" if bold else "normal"),
            fg=fg,
            bg=bg if bg else PANEL_BG
        )

    def button(self, parent, text, command, bg=ACCENT, fg="white", width=16):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            width=width,
            height=2,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2"
        )

    def entry_row(self, parent, row, name, var, unit="mm"):
        self.label(parent, name, bg=CARD_BG, fg=MUTED_FG).grid(row=row, column=0, sticky="e", padx=6, pady=4)
        e = tk.Entry(parent, textvariable=var, width=10, font=("Segoe UI", 10), justify="right")
        e.grid(row=row, column=1, sticky="w", padx=6, pady=4)
        self.label(parent, unit, bg=CARD_BG, fg=MUTED_FG).grid(row=row, column=2, sticky="w", padx=2, pady=4)
        return e

    def build_ui(self):
        # Top title bar
        top = tk.Frame(self.root, bg=APP_BG)
        top.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(
            top,
            text="達源技術有限公司 透鏡成像產生器",
            font=("Segoe UI", 22, "bold"),
            fg=TEXT_FG,
            bg=APP_BG
        ).pack(side="left")

        tk.Label(
            top,
            text="Confirmed V10 geometry  |  X=0~L, Y=0~40, Z=-30~+30",
            font=("Segoe UI", 10),
            fg=MUTED_FG,
            bg=APP_BG
        ).pack(side="left", padx=20, pady=10)

        # Main layout
        main = tk.Frame(self.root, bg=APP_BG)
        main.pack(fill="both", expand=True, padx=16, pady=8)

        left = tk.Frame(main, bg=PANEL_BG, width=300)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        center = tk.Frame(main, bg=APP_BG)
        center.pack(side="left", fill="both", expand=True)

        # Left panel
        self.build_param_panel(left)

        # Plots panel
        self.build_plot_panel(center)

    def build_param_panel(self, parent):
        tk.Label(
            parent,
            text="PARAMETERS",
            font=("Segoe UI", 14, "bold"),
            fg=TEXT_FG,
            bg=PANEL_BG
        ).pack(anchor="w", padx=14, pady=(16, 8))

        geom_card = tk.LabelFrame(
            parent,
            text="Global Geometry",
            bg=CARD_BG,
            fg=TEXT_FG,
            font=("Segoe UI", 10, "bold"),
            bd=0,
            labelanchor="nw"
        )
        geom_card.pack(fill="x", padx=12, pady=8)

        for i, key in enumerate(["L", "YH", "ZW", "La", "Lb", "Ra", "z_half"]):
            self.entry_row(geom_card, i, key, self.vars[key])

        p_card = tk.LabelFrame(
            parent,
            text="XY Output Surface P1~P5",
            bg=CARD_BG,
            fg=TEXT_FG,
            font=("Segoe UI", 10, "bold"),
            bd=0,
            labelanchor="nw"
        )
        p_card.pack(fill="x", padx=12, pady=8)

        tk.Label(p_card, text="Pt", bg=CARD_BG, fg=MUTED_FG).grid(row=0, column=0, padx=4)
        tk.Label(p_card, text="X", bg=CARD_BG, fg=MUTED_FG).grid(row=0, column=1, padx=4)
        tk.Label(p_card, text="Y", bg=CARD_BG, fg=MUTED_FG).grid(row=0, column=2, padx=4)

        for i in range(1, 6):
            tk.Label(p_card, text=f"P{i}", bg=CARD_BG, fg=TEXT_FG).grid(row=i, column=0, padx=4, pady=3)
            tk.Entry(p_card, textvariable=self.pvars[f"P{i}_X"], width=8, justify="right").grid(row=i, column=1, padx=3, pady=3)
            tk.Entry(p_card, textvariable=self.pvars[f"P{i}_Y"], width=8, justify="right").grid(row=i, column=2, padx=3, pady=3)

        out_card = tk.LabelFrame(
            parent,
            text="Output",
            bg=CARD_BG,
            fg=TEXT_FG,
            font=("Segoe UI", 10, "bold"),
            bd=0,
            labelanchor="nw"
        )
        out_card.pack(fill="x", padx=12, pady=8)

        tk.Entry(out_card, textvariable=self.output_dir, width=30).pack(side="left", padx=8, pady=10)
        self.button(out_card, "Browse", self.choose_folder, bg="#566573", width=8).pack(side="left", padx=6)

        actions = tk.Frame(parent, bg=PANEL_BG)
        actions.pack(fill="x", padx=12, pady=14)

        self.button(actions, "Run Simulation / 更新光型", self.run_simulation, bg=GOOD, width=26).pack(fill="x", pady=5)
        self.button(actions, "Export STEP / STL", self.export_step_stl, bg=ACCENT, width=26).pack(fill="x", pady=5)

        self.status = tk.Label(
            parent,
            text="Ready",
            bg=PANEL_BG,
            fg=GOOD,
            font=("Segoe UI", 10, "bold"),
            wraplength=260,
            justify="left"
        )
        self.status.pack(anchor="w", padx=14, pady=8)

        note = (
            "Workflow:\n"
            "1. Adjust parameters\n"
            "2. Run Simulation / 更新光型\n"
            "3. Check beam pattern\n"
            "4. Export STEP / STL"
        )
        tk.Label(parent, text=note, bg=PANEL_BG, fg=MUTED_FG, justify="left").pack(anchor="w", padx=14, pady=8)

    def build_plot_panel(self, parent):
        # Figure 1: geometry preview
        top_plots = tk.Frame(parent, bg=APP_BG)
        top_plots.pack(fill="both", expand=True)

        self.fig_geo = Figure(figsize=(7, 3.4), dpi=100, facecolor=APP_BG)
        self.ax_xz = self.fig_geo.add_subplot(1, 2, 1)
        self.ax_xy = self.fig_geo.add_subplot(1, 2, 2)
        self.canvas_geo = FigureCanvasTkAgg(self.fig_geo, master=top_plots)
        self.canvas_geo.get_tk_widget().pack(fill="both", expand=True, pady=(0, 10))

        # Figure 2: simulation
        self.fig_sim = Figure(figsize=(8, 4.2), dpi=100, facecolor=APP_BG)
        self.ax_iso = self.fig_sim.add_subplot(1, 2, 1)
        self.ax_line = self.fig_sim.add_subplot(1, 2, 2)
        self.canvas_sim = FigureCanvasTkAgg(self.fig_sim, master=top_plots)
        self.canvas_sim.get_tk_widget().pack(fill="both", expand=True)

    # ---------------- parameter reading ----------------
    def get_params(self):
        vals = {k: float(v.get()) for k, v in self.vars.items()}
        pts = []
        for i in range(1, 6):
            pts.append((float(self.pvars[f"P{i}_X"].get()), float(self.pvars[f"P{i}_Y"].get())))
        return vals, pts

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Choose output folder")
        if folder:
            self.output_dir.set(folder)

    # ---------------- simulation and plots ----------------
    def run_simulation(self):
        try:
            vals, pts = self.get_params()
            L = vals["L"]
            YH = vals["YH"]
            ZW = vals["ZW"]
            La = vals["La"]
            Lb = vals["Lb"]
            Ra = vals["Ra"]
            z_half = vals["z_half"]

            if Ra <= z_half:
                raise ValueError("Ra must be larger than z_half.")

            waist = (Lb - La) - 2 * (Ra - math.sqrt(Ra**2 - z_half**2))

            self.draw_geometry(vals, pts, waist)
            self.draw_illuminance(vals, waist)

            self.status.config(text=f"Simulation OK | air waist = {waist:.2f} mm", fg=GOOD)
            self.last_simulation_ok = True

        except Exception as e:
            self.status.config(text=f"Simulation failed: {e}", fg=BAD)
            self.last_simulation_ok = False
            messagebox.showerror("Simulation failed", str(e))

    def draw_geometry(self, vals, pts, waist):
        L = vals["L"]
        YH = vals["YH"]
        ZW = vals["ZW"]
        La = vals["La"]
        Lb = vals["Lb"]
        Ra = vals["Ra"]
        z_half = vals["z_half"]

        # XZ plot
        self.ax_xz.clear()
        self.ax_xz.set_facecolor("#0B1117")
        self.ax_xz.set_title("XZ Air Lens / TIR", color=TEXT_FG, fontsize=11)
        self.ax_xz.set_xlabel("X mm", color=MUTED_FG)
        self.ax_xz.set_ylabel("Z mm", color=MUTED_FG)
        self.ax_xz.tick_params(colors=MUTED_FG)

        self.ax_xz.plot([0, L, L, 0, 0], [-ZW/2, -ZW/2, ZW/2, ZW/2, -ZW/2], color="#9FB3C8", linewidth=1.2)

        # LED slot
        self.ax_xz.plot([0, 5, 5, 0, 0], [-6, -6, 6, 6, -6], color="#F2C94C", linewidth=2)
        self.ax_xz.text(1, 8, "LED", color="#F2C94C", fontsize=8)

        # TIR
        self.ax_xz.plot([0, 25, 0, 0], [30, 30, 6, 30], color="#EB5757", linewidth=1.2)
        self.ax_xz.plot([0, 25, 0, 0], [-30, -30, -6, -30], color="#EB5757", linewidth=1.2)

        z_vals = np.linspace(z_half, -z_half, 140)
        left = []
        right = []
        for z in z_vals:
            sag_z = Ra - math.sqrt(Ra**2 - z**2)
            left.append((La + sag_z, z))
            right.append((Lb - sag_z, z))

        self.ax_xz.plot([p[0] for p in left], [p[1] for p in left], color="#27AE60", linewidth=2.4)
        self.ax_xz.plot([p[0] for p in right], [p[1] for p in right], color="#27AE60", linewidth=2.4)
        self.ax_xz.text((La+Lb)/2, 0, f"waist={waist:.1f}mm", color=TEXT_FG, ha="center", fontsize=8)
        self.ax_xz.text(La, -27, f"La={La:g}", color=TEXT_FG, ha="center", fontsize=8)
        self.ax_xz.text(Lb, -27, f"Lb={Lb:g}", color=TEXT_FG, ha="center", fontsize=8)
        self.ax_xz.set_xlim(-2, L+5)
        self.ax_xz.set_ylim(-ZW/2-5, ZW/2+5)
        self.ax_xz.grid(True, alpha=0.15)

        # XY plot
        self.ax_xy.clear()
        self.ax_xy.set_facecolor("#0B1117")
        self.ax_xy.set_title("XY Output Surface", color=TEXT_FG, fontsize=11)
        self.ax_xy.set_xlabel("X mm", color=MUTED_FG)
        self.ax_xy.set_ylabel("Y mm", color=MUTED_FG)
        self.ax_xy.tick_params(colors=MUTED_FG)

        self.ax_xy.plot([0, L, L, 0, 0], [0, 0, YH, YH, 0], color="#9FB3C8", linewidth=1.2)

        # TIR cuts
        self.ax_xy.plot([0, 25, 0, 0], [40, 40, 26, 40], color="#EB5757", linewidth=1.2)
        self.ax_xy.plot([0, 25, 0, 0], [0, 0, 14, 0], color="#EB5757", linewidth=1.2)

        px = [p[0] for p in pts]
        py = [p[1] for p in pts]
        self.ax_xy.plot(px, py, marker="o", color="#2F80ED", linewidth=2.4)
        for i, (x, y) in enumerate(pts, start=1):
            self.ax_xy.text(x, y+1.2, f"P{i}", color=TEXT_FG, fontsize=8, ha="center")

        self.ax_xy.set_xlim(-2, L+8)
        self.ax_xy.set_ylim(-2, YH+5)
        self.ax_xy.grid(True, alpha=0.15)

        self.fig_geo.tight_layout()
        self.canvas_geo.draw()

    def draw_illuminance(self, vals, waist):
        L = vals["L"]
        La = vals["La"]
        Lb = vals["Lb"]
        Ra = vals["Ra"]
        pts = []
        try:
            _, pts = self.get_params()
        except Exception:
            pts = [(78,0),(84,7),(90,18),(95,30),(100,39)]

        # Conceptual simulation model that visibly reacts to parameters.
        # This is not full ray tracing, but it is useful for fast design comparison.
        x = np.linspace(0, 10, 520)
        z = np.linspace(-0.35, 0.35, 290)
        X, Z = np.meshgrid(x, z)

        p1x = pts[0][0]
        p5x = pts[-1][0]
        start_m = 0.50 + 0.004 * (p1x - 78.0)
        end_m = 7.00 * (L / 100.0) + 0.010 * (p5x - L)
        end_m = max(start_m + 1.0, min(10.0, end_m))

        half_width = 0.15 * (waist / 15.4)
        half_width = max(0.06, min(0.32, half_width))

        edge_soft = 0.018 * (72.0 / max(Ra, 1.0))
        edge_soft = max(0.010, min(0.040, edge_soft))

        y_mid = (pts[2][1] + pts[3][1]) / 2.0
        ripple_amp = max(0.004, min(0.080, 0.012 + abs(y_mid - 24.0) / 500.0))

        rise = 1 / (1 + np.exp(-(X - start_m) / 0.060))
        fall = 1 / (1 + np.exp((X - end_m) / 0.230))
        x_profile = rise * fall
        x_profile *= 1.0 + ripple_amp * np.cos((X - 3.7) / 3.3 * np.pi)
        z_profile = 1 / (1 + np.exp((np.abs(Z) - half_width) / edge_soft))

        E = x_profile * z_profile
        E /= max(E.max(), 1e-9)
        center = E[np.argmin(np.abs(z)), :]

        self.ax_iso.clear()
        self.ax_iso.set_facecolor("#0B1117")
        self.ax_iso.set_title("Ground Iso-Illuminance", color=TEXT_FG, fontsize=11)
        self.ax_iso.set_xlabel("X m", color=MUTED_FG)
        self.ax_iso.set_ylabel("Z m", color=MUTED_FG)
        self.ax_iso.tick_params(colors=MUTED_FG)

        self.ax_iso.contourf(X, Z, E, levels=np.linspace(0, 1, 24), cmap="turbo")
        self.ax_iso.contour(X, Z, E, levels=[0.1, 0.5, 0.8], colors="white", linewidths=0.8)
        self.ax_iso.axvline(start_m, color="white", linestyle="--", linewidth=1)
        self.ax_iso.axvline(end_m, color="white", linestyle="--", linewidth=1)
        self.ax_iso.axhline(half_width, color="white", linestyle="--", linewidth=0.8)
        self.ax_iso.axhline(-half_width, color="white", linestyle="--", linewidth=0.8)
        self.ax_iso.text(1.0, 0.29, f"width≈{2*half_width:.2f}m", color="white", fontsize=8)
        self.ax_iso.set_xlim(0, 10)
        self.ax_iso.set_ylim(-0.35, 0.35)

        self.ax_line.clear()
        self.ax_line.set_facecolor("#0B1117")
        self.ax_line.set_title("Center-Line Platform", color=TEXT_FG, fontsize=11)
        self.ax_line.plot(x, center, color="#5DADE2", linewidth=2.5)
        self.ax_line.fill_between(x, 0, center, color="#5DADE2", alpha=0.25)
        self.ax_line.axvline(start_m, color="white", linestyle="--", linewidth=1)
        self.ax_line.axvline(end_m, color="white", linestyle="--", linewidth=1)
        self.ax_line.axhline(1.0, color="white", linestyle="--", linewidth=1)
        self.ax_line.axhline(0.85, color="#F2C94C", linestyle=":", linewidth=1)
        self.ax_line.axhline(1.15, color="#F2C94C", linestyle=":", linewidth=1)
        self.ax_line.set_xlabel("X m", color=MUTED_FG)
        self.ax_line.set_ylabel("Relative", color=MUTED_FG)
        self.ax_line.tick_params(colors=MUTED_FG)
        self.ax_line.set_xlim(0, 10)
        self.ax_line.set_ylim(0, 1.15)
        self.ax_line.grid(True, alpha=0.18)
        self.ax_line.text(0.8, 0.10, f"L={L:g}, La={La:g}, Lb={Lb:g}, Ra={Ra:g}\nwaist={waist:.1f}mm\nwidth≈{2*half_width:.2f}m", color=TEXT_FG, fontsize=8)

        self.fig_sim.tight_layout()
        self.canvas_sim.draw()

    # ---------------- CadQuery export ----------------
    def export_step_stl(self):
        if not self.last_simulation_ok:
            ans = messagebox.askyesno("Simulation not confirmed", "Simulation was not successfully run. Export anyway?")
            if not ans:
                return

        if cq is None:
            messagebox.showerror(
                "CadQuery import failed",
                "CadQuery is missing or failed to load.\n"
                "This EXE must be built in onedir mode with all DLLs.\n\n"
                f"Error: {CADQUERY_ERROR}"
            )
            return

        try:
            out_dir = self.output_dir.get()
            os.makedirs(out_dir, exist_ok=True)
            vals, pts = self.get_params()
            lens = self.build_lens(vals, pts)

            step_path = os.path.join(out_dir, "micro_led_lens_v10.step")
            stl_path = os.path.join(out_dir, "micro_led_lens_v10.stl")

            cq.exporters.export(lens, step_path)
            cq.exporters.export(lens, stl_path)

            self.status.config(text=f"Exported STEP/STL to {out_dir}", fg=GOOD)
            messagebox.showinfo("Export complete", f"Generated:\n{step_path}\n{stl_path}")
        except Exception as e:
            self.status.config(text=f"Export failed: {e}", fg=BAD)
            messagebox.showerror("Export failed", str(e))

    def build_lens(self, vals, pts):
        L = vals["L"]
        YH = vals["YH"]
        ZW = vals["ZW"]
        La = vals["La"]
        Lb = vals["Lb"]
        Ra = vals["Ra"]
        z_half = vals["z_half"]

        lens = cq.Workplane("XY").box(L, YH, ZW, centered=(False, False, True))

        led_slot = (
            cq.Workplane("YZ")
            .center(20, 0)
            .rect(12, 12)
            .extrude(12, both=True)
        )
        lens = lens.cut(led_slot)

        z_vals = np.linspace(z_half, -z_half, 100)
        left_curve = []
        right_curve = []
        for z in z_vals:
            sag_z = Ra - math.sqrt(Ra**2 - z**2)
            left_curve.append((La + sag_z, z))
            right_curve.append((Lb - sag_z, z))

        air_pts = left_curve + right_curve[::-1]
        air_lens = (
            cq.Workplane("XZ")
            .polyline(air_pts)
            .close()
            .extrude(100, both=True)
        )
        lens = lens.cut(air_lens)

        # Use P1~P5 from UI
        exit_cut = (
            cq.Workplane("XY")
            .moveTo(pts[0][0], pts[0][1])
            .spline(pts[1:])
            .lineTo(130, 40)
            .lineTo(130, 0)
            .lineTo(pts[0][0], pts[0][1])
            .close()
            .extrude(100, both=True)
        )
        lens = lens.cut(exit_cut)

        tir_top = (
            cq.Workplane("XY")
            .polyline([(0, 40), (25, 40), (0, 26)])
            .close()
            .extrude(100, both=True)
        )
        tir_bottom = (
            cq.Workplane("XY")
            .polyline([(0, 0), (25, 0), (0, 14)])
            .close()
            .extrude(100, both=True)
        )
        lens = lens.cut(tir_top).cut(tir_bottom)

        tir_z_top = (
            cq.Workplane("XZ")
            .polyline([(0, 30), (25, 30), (0, 6)])
            .close()
            .extrude(100, both=True)
        )
        tir_z_bottom = (
            cq.Workplane("XZ")
            .polyline([(0, -30), (25, -30), (0, -6)])
            .close()
            .extrude(100, both=True)
        )
        lens = lens.cut(tir_z_top).cut(tir_z_bottom)

        return lens


if __name__ == "__main__":
    root = tk.Tk()
    app = LensDesignerPro(root)
    root.mainloop()
