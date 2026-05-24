# -*- coding: utf-8 -*-
"""
LensDesigner.py
MICRO LED Lens Designer - Confirmed V10 desktop app

Use:
1. Choose output folder
2. Click "Generate STEP / STL"
3. The app exports micro_led_lens_v10.step and micro_led_lens_v10.stl

Coordinate system:
X = 0~L
Y = 0~40
Z = -30~+30

Confirmed V10 geometry:
- Continuous XZ hourglass air lens
- XY P1~P5 output cut
- LED slot
- XY and XZ TIR cuts
"""

import math
import os
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    import cadquery as cq
    import numpy as np
except Exception as e:
    cq = None
    np = None
    IMPORT_ERROR = e
else:
    IMPORT_ERROR = None


class LensDesignerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MICRO LED Lens Designer - V10")
        self.root.geometry("560x430")
        self.root.resizable(False, False)

        self.output_dir = tk.StringVar(value=os.path.abspath(os.getcwd()))

        self.L = tk.DoubleVar(value=100.0)
        self.YH = tk.DoubleVar(value=40.0)
        self.ZW = tk.DoubleVar(value=60.0)
        self.La = tk.DoubleVar(value=24.0)
        self.Lb = tk.DoubleVar(value=44.0)
        self.Ra = tk.DoubleVar(value=72.0)
        self.z_half = tk.DoubleVar(value=18.0)

        self.build_ui()

    def build_ui(self):
        tk.Label(
            self.root,
            text="MICRO LED Lens Designer - Confirmed V10",
            font=("Arial", 16, "bold")
        ).pack(pady=12)

        frame = tk.Frame(self.root)
        frame.pack(padx=18, pady=6, fill="x")

        params = [
            ("L", self.L),
            ("YH", self.YH),
            ("ZW", self.ZW),
            ("La", self.La),
            ("Lb", self.Lb),
            ("Ra", self.Ra),
            ("z_half", self.z_half),
        ]

        for i, (name, var) in enumerate(params):
            tk.Label(frame, text=name, width=10, anchor="e").grid(row=i, column=0, padx=5, pady=4)
            tk.Entry(frame, textvariable=var, width=12).grid(row=i, column=1, padx=5, pady=4)
            tk.Label(frame, text="mm").grid(row=i, column=2, padx=5, pady=4)

        path_frame = tk.LabelFrame(self.root, text="Output Folder")
        path_frame.pack(padx=18, pady=10, fill="x")

        tk.Entry(path_frame, textvariable=self.output_dir, width=55).pack(side="left", padx=8, pady=8)
        tk.Button(path_frame, text="Browse...", command=self.choose_folder).pack(side="left", padx=8)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=12)

        tk.Button(
            btn_frame,
            text="Generate STEP / STL",
            command=self.generate,
            width=22,
            height=2,
            bg="#2b7cff",
            fg="white"
        ).pack(side="left", padx=8)

        tk.Button(
            btn_frame,
            text="Close",
            command=self.root.destroy,
            width=12,
            height=2
        ).pack(side="left", padx=8)

        self.status = tk.Label(self.root, text="Status: ready", anchor="w", fg="green")
        self.status.pack(padx=18, pady=8, fill="x")

        note = (
            "Fixed coordinate system: X=0~L, Y=0~40, Z=-30~+30\n"
            "V10: continuous hourglass air lens, P1~P5 output surface, TIR cuts included"
        )
        tk.Label(self.root, text=note, justify="left", fg="#444").pack(pady=4)

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Choose STEP / STL output folder")
        if folder:
            self.output_dir.set(folder)

    def generate(self):
        if cq is None or np is None:
            messagebox.showerror(
                "Missing packages",
                "cadquery / numpy not found.\n\n"
                "If running Python directly, use Python 3.11 and run:\n"
                "pip install cadquery numpy\n\n"
                f"Error: {IMPORT_ERROR}"
            )
            return

        try:
            out_dir = self.output_dir.get()
            os.makedirs(out_dir, exist_ok=True)

            lens = self.build_lens()

            step_path = os.path.join(out_dir, "micro_led_lens_v10.step")
            stl_path = os.path.join(out_dir, "micro_led_lens_v10.stl")

            cq.exporters.export(lens, step_path)
            cq.exporters.export(lens, stl_path)

            self.status.config(text=f"Done: exported to {out_dir}", fg="green")
            messagebox.showinfo("Done", f"Generated:\n{step_path}\n{stl_path}")

        except Exception as e:
            self.status.config(text="Failed", fg="red")
            messagebox.showerror("Generate failed", str(e))

    def build_lens(self):
        L = float(self.L.get())
        YH = float(self.YH.get())
        ZW = float(self.ZW.get())
        La = float(self.La.get())
        Lb = float(self.Lb.get())
        Ra = float(self.Ra.get())
        z_half = float(self.z_half.get())

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

        exit_cut = (
            cq.Workplane("XY")
            .moveTo(78, 0)
            .spline([(84, 7), (90, 18), (95, 30), (100, 39)])
            .lineTo(130, 40)
            .lineTo(130, 0)
            .lineTo(78, 0)
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
    LensDesignerApp(root)
    root.mainloop()
