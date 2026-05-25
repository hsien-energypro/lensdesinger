# -*- coding: utf-8 -*-
import tkinter as tk

root = tk.Tk()
root.title("達源技術有限公司 透鏡成像產生器")

title = tk.Label(
    root,
    text="達源技術有限公司 透鏡成像產生器",
    font=("Segoe UI", 22, "bold")
)
title.pack(pady=40)

info = tk.Label(
    root,
    text="GitHub EXE Compiler Final Package",
    font=("Segoe UI", 12)
)
info.pack(pady=10)

root.geometry("900x600")
root.mainloop()
