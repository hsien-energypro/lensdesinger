# -*- coding: utf-8 -*-
import os, math, traceback
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

APP_TITLE = "達源技術有限公司 透鏡成像產生器"
APP_BG="#101820"; PANEL_BG="#17212B"; CARD_BG="#1F2B38"
TEXT_FG="#EAF2F8"; MUTED_FG="#AAB7C4"; ACCENT="#2F80ED"; GOOD="#27AE60"; BAD="#EB5757"; WARN="#F2C94C"

class App:
    def __init__(self, root):
        self.root=root
        self.root.title(APP_TITLE)
        self.root.geometry("1400x880")
        self.root.minsize(1280,820)
        self.root.configure(bg=APP_BG)

        self.output_dir=tk.StringVar(value=os.path.abspath(os.getcwd()))
        self.v={
            "L":tk.DoubleVar(value=100.0),"YH":tk.DoubleVar(value=40.0),"ZW":tk.DoubleVar(value=60.0),
            "La":tk.DoubleVar(value=24.0),"Lb":tk.DoubleVar(value=44.0),"Ra":tk.DoubleVar(value=72.0),
            "z_half":tk.DoubleVar(value=18.0)
        }
        self.p={
            "P1X":tk.DoubleVar(value=78.0),"P1Y":tk.DoubleVar(value=0.0),
            "P2X":tk.DoubleVar(value=84.0),"P2Y":tk.DoubleVar(value=7.0),
            "P3X":tk.DoubleVar(value=90.0),"P3Y":tk.DoubleVar(value=18.0),
            "P4X":tk.DoubleVar(value=95.0),"P4Y":tk.DoubleVar(value=30.0),
            "P5X":tk.DoubleVar(value=100.0),"P5Y":tk.DoubleVar(value=39.0)
        }
        self.auto_scale_p=tk.BooleanVar(value=True)
        self.last_L=100.0
        self.last_ok=False
        self.build_ui()
        self.run_sim()

    def lab(self,p,t,size=10,bold=False,bg=None,fg=TEXT_FG):
        return tk.Label(p,text=t,font=("Microsoft JhengHei UI",size,"bold" if bold else "normal"),bg=bg or PANEL_BG,fg=fg)

    def btn(self,p,t,cmd,bg=ACCENT,h=2):
        return tk.Button(p,text=t,command=cmd,bg=bg,fg="white",activebackground=bg,activeforeground="white",
                         relief="flat",bd=0,height=h,font=("Microsoft JhengHei UI",10,"bold"),cursor="hand2")

    def build_ui(self):
        top=tk.Frame(self.root,bg=APP_BG); top.pack(fill="x",padx=16,pady=(10,6))
        self.lab(top,APP_TITLE,23,True,bg=APP_BG).pack(side="left")
        self.lab(top,"V5 UI固定版：Run Simulation / Export STEP 按鈕固定顯示",10,bg=APP_BG,fg=MUTED_FG).pack(side="left",padx=20)

        main=tk.Frame(self.root,bg=APP_BG); main.pack(fill="both",expand=True,padx=14,pady=8)
        left=tk.Frame(main,bg=PANEL_BG,width=360); left.pack(side="left",fill="y",padx=(0,12)); left.pack_propagate(False)
        right=tk.Frame(main,bg=APP_BG); right.pack(side="left",fill="both",expand=True)

        self.build_left(left)
        self.build_plots(right)

    def build_left(self,left):
        self.lab(left,"參數設定",15,True).pack(anchor="w",padx=14,pady=(12,6))

        card=tk.LabelFrame(left,text="Global Geometry",bg=CARD_BG,fg=TEXT_FG,font=("Segoe UI",10,"bold"),bd=0)
        card.pack(fill="x",padx=12,pady=6)
        for r,k in enumerate(["L","YH","ZW","La","Lb","Ra","z_half"]):
            self.lab(card,k,bg=CARD_BG,fg=MUTED_FG).grid(row=r,column=0,sticky="e",padx=6,pady=3)
            tk.Entry(card,textvariable=self.v[k],width=10,justify="right",font=("Segoe UI",10)).grid(row=r,column=1,padx=6,pady=3)
            self.lab(card,"mm",bg=CARD_BG,fg=MUTED_FG).grid(row=r,column=2,sticky="w")

        pc=tk.LabelFrame(left,text="XY Output Surface P1~P5",bg=CARD_BG,fg=TEXT_FG,font=("Segoe UI",10,"bold"),bd=0)
        pc.pack(fill="x",padx=12,pady=6)
        tk.Checkbutton(pc,text="L變化時自動縮放P點",variable=self.auto_scale_p,bg=CARD_BG,fg=TEXT_FG,
                       selectcolor=CARD_BG,activebackground=CARD_BG,activeforeground=TEXT_FG).grid(row=0,column=0,columnspan=3,sticky="w",padx=5,pady=2)
        for c,t in enumerate(["Pt","X","Y"]): self.lab(pc,t,bg=CARD_BG,fg=MUTED_FG).grid(row=1,column=c,padx=4)
        for i in range(1,6):
            self.lab(pc,f"P{i}",bg=CARD_BG).grid(row=i+1,column=0,padx=4,pady=2)
            tk.Entry(pc,textvariable=self.p[f"P{i}X"],width=8,justify="right").grid(row=i+1,column=1,padx=4,pady=2)
            tk.Entry(pc,textvariable=self.p[f"P{i}Y"],width=8,justify="right").grid(row=i+1,column=2,padx=4,pady=2)
        self.btn(pc,"依目前L重置P1~P5",self.reset_p_by_l,bg="#566573",h=1).grid(row=7,column=0,columnspan=3,sticky="ew",padx=6,pady=5)

        oc=tk.LabelFrame(left,text="Output Folder",bg=CARD_BG,fg=TEXT_FG,font=("Segoe UI",10,"bold"),bd=0)
        oc.pack(fill="x",padx=12,pady=6)
        tk.Entry(oc,textvariable=self.output_dir,width=31,font=("Segoe UI",9)).pack(side="left",padx=7,pady=8)
        # 小一點，避免「選擇」被切掉
        tk.Button(oc,text="選擇",command=self.browse,bg="#566573",fg="white",relief="flat",bd=0,
                  width=6,height=1,font=("Microsoft JhengHei UI",8,"bold")).pack(side="left",padx=4,pady=8)

        # 固定功能按鈕區，不讓它被壓掉
        actions=tk.LabelFrame(left,text="Actions",bg=PANEL_BG,fg=TEXT_FG,font=("Segoe UI",10,"bold"),bd=0)
        actions.pack(fill="x",side="bottom",padx=12,pady=12)
        self.btn(actions,"Run Simulation / 更新光型",self.run_sim,bg=GOOD,h=2).pack(fill="x",pady=5)
        self.btn(actions,"Export STEP / STL 產生3D檔",self.export,bg=ACCENT,h=2).pack(fill="x",pady=5)
        self.status=self.lab(actions,"Ready",10,True,fg=GOOD)
        self.status.pack(anchor="w",pady=5)

        note="修正：\n1. 選擇按鈕字縮小\n2. Run Simulation 固定在左下\n3. Export STEP/STL 固定在左下\n4. 尺規隨 L/YH/ZW 改變"
        self.lab(left,note,9,bg=PANEL_BG,fg=MUTED_FG).pack(anchor="w",padx=14,pady=6)

    def build_plots(self,right):
        self.fig1=Figure(figsize=(8,3.5),dpi=100,facecolor=APP_BG)
        self.ax_xz=self.fig1.add_subplot(1,2,1); self.ax_xy=self.fig1.add_subplot(1,2,2)
        self.can1=FigureCanvasTkAgg(self.fig1,right); self.can1.get_tk_widget().pack(fill="both",expand=True,pady=(0,10))
        self.fig2=Figure(figsize=(8,4.5),dpi=100,facecolor=APP_BG)
        self.ax_iso=self.fig2.add_subplot(1,2,1); self.ax_line=self.fig2.add_subplot(1,2,2)
        self.can2=FigureCanvasTkAgg(self.fig2,right); self.can2.get_tk_widget().pack(fill="both",expand=True)

    def browse(self):
        d=filedialog.askdirectory()
        if d: self.output_dir.set(d)

    def reset_p_by_l(self):
        L=float(self.v["L"].get()); s=L/100.0
        vals=[(78*s,0),(84*s,7),(90*s,18),(95*s,30),(L,39)]
        for i,(x,y) in enumerate(vals,1):
            self.p[f"P{i}X"].set(round(x,3)); self.p[f"P{i}Y"].set(y)
        self.last_L=L; self.run_sim()

    def maybe_scale_p(self):
        L=float(self.v["L"].get())
        if self.auto_scale_p.get() and abs(L-self.last_L)>1e-9:
            s=L/100.0
            vals=[(78*s,0),(84*s,7),(90*s,18),(95*s,30),(L,39)]
            for i,(x,y) in enumerate(vals,1):
                self.p[f"P{i}X"].set(round(x,3)); self.p[f"P{i}Y"].set(y)
            self.last_L=L

    def vals(self):
        self.maybe_scale_p()
        v={k:float(x.get()) for k,x in self.v.items()}
        pts=[(float(self.p[f"P{i}X"].get()),float(self.p[f"P{i}Y"].get())) for i in range(1,6)]
        return v,pts

    def waist(self,v):
        return (v["Lb"]-v["La"])-2*(v["Ra"]-math.sqrt(v["Ra"]**2-v["z_half"]**2))

    def setup(self,ax,title,xlab,ylab):
        ax.clear(); ax.set_facecolor("#0B1117"); ax.set_title(title,color=TEXT_FG,fontsize=11)
        ax.set_xlabel(xlab,color=MUTED_FG); ax.set_ylabel(ylab,color=MUTED_FG); ax.tick_params(colors=MUTED_FG); ax.grid(True,alpha=.16)

    def run_sim(self):
        try:
            v,pts=self.vals()
            if v["Ra"]<=v["z_half"]: raise ValueError("Ra 必須大於 z_half")
            if v["Lb"]<=v["La"]: raise ValueError("Lb 必須大於 La")
            w=self.waist(v); self.draw_geo(v,pts,w); self.draw_sim(v,pts,w)
            self.status.config(text=f"Simulation OK | waist={w:.2f} mm",fg=GOOD); self.last_ok=True
        except Exception as e:
            self.status.config(text=f"Simulation failed: {e}",fg=BAD); self.last_ok=False
            messagebox.showerror("Simulation failed",str(e))

    def draw_geo(self,v,pts,w):
        L,YH,ZW=v["L"],v["YH"],v["ZW"]; La,Lb,Ra,zh=v["La"],v["Lb"],v["Ra"],v["z_half"]
        margin=max(6,L*.08); xtir=min(25,L*.25)
        self.setup(self.ax_xz,"XZ 空氣透鏡 / TIR","X mm","Z mm")
        self.ax_xz.plot([0,L,L,0,0],[-ZW/2,-ZW/2,ZW/2,ZW/2,-ZW/2],color="#9FB3C8")
        self.ax_xz.plot([0,xtir,0,0],[ZW/2,ZW/2,6,ZW/2],color=BAD); self.ax_xz.plot([0,xtir,0,0],[-ZW/2,-ZW/2,-6,-ZW/2],color=BAD)
        self.ax_xz.plot([0,5,5,0,0],[-6,-6,6,6,-6],color=WARN,lw=2)
        zs=np.linspace(zh,-zh,180); lx=[];lz=[];rx=[];rz=[]
        for z in zs:
            sag=Ra-math.sqrt(Ra**2-z**2); lx.append(La+sag); lz.append(z); rx.append(Lb-sag); rz.append(z)
        self.ax_xz.fill(lx+rx[::-1],lz+rz[::-1],color=GOOD,alpha=.18); self.ax_xz.plot(lx,lz,color=GOOD,lw=2.6); self.ax_xz.plot(rx,rz,color=GOOD,lw=2.6)
        self.ax_xz.text((La+Lb)/2,0,f"waist={w:.1f}mm",color=TEXT_FG,ha="center",fontsize=8)
        self.ax_xz.set_xlim(-2,L+margin); self.ax_xz.set_ylim(-ZW/2-5,ZW/2+5)

        self.setup(self.ax_xy,"XY 出光面","X mm","Y mm")
        self.ax_xy.plot([0,L,L,0,0],[0,0,YH,YH,0],color="#9FB3C8")
        self.ax_xy.plot([0,xtir,0,0],[YH,YH,max(YH-14,0),YH],color=BAD); self.ax_xy.plot([0,xtir,0,0],[0,0,min(14,YH),0],color=BAD)
        px=[p[0] for p in pts]; py=[p[1] for p in pts]
        self.ax_xy.plot(px,py,"o-",color=ACCENT,lw=2.4)
        for i,(x,y) in enumerate(pts,1): self.ax_xy.text(x,y+max(1,YH*.03),f"P{i}",color=TEXT_FG,fontsize=8,ha="center")
        self.ax_xy.set_xlim(-2,L+margin); self.ax_xy.set_ylim(-2,YH+max(5,YH*.10))
        self.fig1.tight_layout(); self.can1.draw()

    def draw_sim(self,v,pts,w):
        L,Ra=v["L"],v["Ra"]; x=np.linspace(0,10,520); z=np.linspace(-.35,.35,290); X,Z=np.meshgrid(x,z)
        p1x,p5x=pts[0][0],pts[-1][0]; ref_p1=78*(L/100.0); ref_p5=L
        start=.50+0.003*(p1x-ref_p1); end=7.0+0.006*(p5x-ref_p5); end=max(start+1,min(10,end))
        hw=max(.06,min(.32,.15*(w/15.4))); edge=max(.010,min(.04,.018*(72.0/Ra)))
        ymid=(pts[2][1]+pts[3][1])/2; ripple=max(.004,min(.08,.012+abs(ymid-24)/500))
        E=(1/(1+np.exp(-(X-start)/.06)))*(1/(1+np.exp((X-end)/.23)))
        E*=1+ripple*np.cos((X-3.7)/3.3*np.pi); E*=1/(1+np.exp((np.abs(Z)-hw)/edge)); E/=E.max()
        center=E[np.argmin(np.abs(z)),:]
        self.setup(self.ax_iso,"地面等照度圖","X m","Z m")
        self.ax_iso.contourf(X,Z,E,levels=np.linspace(0,1,24),cmap="turbo"); self.ax_iso.contour(X,Z,E,levels=[.1,.5,.8],colors="white",linewidths=.8)
        self.ax_iso.axvline(start,color="white",ls="--"); self.ax_iso.axvline(end,color="white",ls="--"); self.ax_iso.axhline(hw,color="white",ls="--",lw=.8); self.ax_iso.axhline(-hw,color="white",ls="--",lw=.8)
        self.ax_iso.set_xlim(0,10); self.ax_iso.set_ylim(-.35,.35)
        self.setup(self.ax_line,"中心線平台","X m","Relative")
        self.ax_line.plot(x,center,color="#5DADE2",lw=2.5); self.ax_line.fill_between(x,0,center,color="#5DADE2",alpha=.25)
        self.ax_line.axvline(start,color="white",ls="--"); self.ax_line.axvline(end,color="white",ls="--"); self.ax_line.axhline(1,color="white",ls="--"); self.ax_line.axhline(.85,color=WARN,ls=":"); self.ax_line.axhline(1.15,color=WARN,ls=":")
        self.ax_line.text(.8,.1,f"L={L:g}, width≈{2*hw:.2f}m",color=TEXT_FG,fontsize=8)
        self.ax_line.set_xlim(0,10); self.ax_line.set_ylim(0,1.15)
        self.fig2.tight_layout(); self.can2.draw()

    def export(self):
        if not self.last_ok and not messagebox.askyesno("Simulation not updated","尚未更新模擬，仍然輸出嗎？"): return
        try: import cadquery as cq
        except Exception: messagebox.showerror("CadQuery 載入失敗",traceback.format_exc()); return
        try:
            v,pts=self.vals(); lens=self.build_lens(cq,v,pts); out=self.output_dir.get(); os.makedirs(out,exist_ok=True)
            step=os.path.join(out,"micro_led_lens_v10.step"); stl=os.path.join(out,"micro_led_lens_v10.stl")
            cq.exporters.export(lens,step); cq.exporters.export(lens,stl)
            self.status.config(text=f"Exported: {out}",fg=GOOD); messagebox.showinfo("Export complete",f"Generated:\n{step}\n{stl}")
        except Exception: messagebox.showerror("Export failed",traceback.format_exc())

    def build_lens(self,cq,v,pts):
        L,YH,ZW=v["L"],v["YH"],v["ZW"]; La,Lb,Ra,zh=v["La"],v["Lb"],v["Ra"],v["z_half"]
        lens=cq.Workplane("XY").box(L,YH,ZW,centered=(False,False,True))
        lens=lens.cut(cq.Workplane("YZ").center(20,0).rect(12,12).extrude(12,both=True))
        zs=np.linspace(zh,-zh,100); left=[]; right=[]
        for z in zs:
            sag=Ra-math.sqrt(Ra**2-z**2); left.append((La+sag,z)); right.append((Lb-sag,z))
        lens=lens.cut(cq.Workplane("XZ").polyline(left+right[::-1]).close().extrude(100,both=True))
        cut_x=L+30*(L/100.0)
        lens=lens.cut(cq.Workplane("XY").moveTo(pts[0][0],pts[0][1]).spline(pts[1:]).lineTo(cut_x,YH).lineTo(cut_x,0).lineTo(pts[0][0],pts[0][1]).close().extrude(100,both=True))
        xtir=min(25,L*.25)
        lens=lens.cut(cq.Workplane("XY").polyline([(0,YH),(xtir,YH),(0,max(YH-14,0))]).close().extrude(100,both=True))
        lens=lens.cut(cq.Workplane("XY").polyline([(0,0),(xtir,0),(0,min(14,YH))]).close().extrude(100,both=True))
        lens=lens.cut(cq.Workplane("XZ").polyline([(0,ZW/2),(xtir,ZW/2),(0,6)]).close().extrude(100,both=True))
        lens=lens.cut(cq.Workplane("XZ").polyline([(0,-ZW/2),(xtir,-ZW/2),(0,-6)]).close().extrude(100,both=True))
        return lens

if __name__=="__main__":
    root=tk.Tk(); App(root); root.mainloop()
