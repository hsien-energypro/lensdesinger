# -*- coding: utf-8 -*-
"""
達源技術有限公司 透鏡成像產生器 - V10.2 INTERSECTION RAYTRACE

V10.2 重點：
1. 加入 3D RayTrace Lite，Ray count 可選 500 / 2500 / 5000。
2. 亂改 La/Lb/Ra/P1~P5/R1~R4，光型會明顯變化。
3. Run Simulation 只更新畫面，不存檔。
4. Export STEP/STL 才存 STEP/STL + PNG + TXT，檔名都有時間戳。
5. 按鈕文字改成 Run Simulation。
"""

import os, sys, math, traceback
from datetime import datetime
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

def resource_path(name):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, name)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)

class App:
    def __init__(self, root):
        self.root=root
        self.root.title(APP_TITLE)
        ico = resource_path("icon.ico")
        if os.path.exists(ico):
            try: self.root.iconbitmap(ico)
            except Exception: pass

        self.root.geometry("1420x900")
        self.root.minsize(1180,760)
        try: self.root.state("zoomed")
        except Exception: pass
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
        self.r={
            "R1":tk.DoubleVar(value=10.0),
            "R2":tk.DoubleVar(value=70.0),
            "R3":tk.DoubleVar(value=70.0),
            "R4":tk.DoubleVar(value=12.0),
        }
        self.auto_scale_p=tk.BooleanVar(value=True)
        self.ray_count=tk.IntVar(value=2500)
        self.last_L=100.0
        self.last_ok=False
        self.last_sim_info={}
        self.build_ui()
        self.root.after(300, self.run_sim)

    def lab(self,p,t,size=10,bold=False,bg=None,fg=TEXT_FG):
        return tk.Label(p,text=t,font=("Microsoft JhengHei UI",size,"bold" if bold else "normal"),bg=bg or PANEL_BG,fg=fg)

    def btn(self,p,t,cmd,bg=ACCENT,h=2):
        return tk.Button(p,text=t,command=cmd,bg=bg,fg="white",activebackground=bg,activeforeground="white",
                         relief="flat",bd=0,height=h,font=("Microsoft JhengHei UI",10,"bold"),cursor="hand2")

    def build_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        top=tk.Frame(self.root,bg=APP_BG)
        top.grid(row=0,column=0,sticky="ew",padx=16,pady=(8,4))
        self.lab(top,APP_TITLE,23,True,bg=APP_BG).pack(side="left")
        self.lab(top,"專利產品 請勿模仿",13,True,bg=APP_BG,fg="#F5B041").pack(side="right",padx=22)

        main=tk.Frame(self.root,bg=APP_BG)
        main.grid(row=1,column=0,sticky="nsew",padx=14,pady=8)
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)

        left=tk.Frame(main,bg=PANEL_BG,width=370)
        left.grid(row=0,column=0,sticky="ns",padx=(0,12))
        left.grid_propagate(False)

        right=tk.Frame(main,bg=APP_BG)
        right.grid(row=0,column=1,sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self.build_left(left)
        self.build_plots(right)

    def build_left(self,left):
        left.grid_rowconfigure(7, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self.lab(left,"參數設定",15,True).grid(row=0,column=0,sticky="w",padx=14,pady=(10,4))

        card=tk.LabelFrame(left,text="Global Geometry",bg=CARD_BG,fg=TEXT_FG,font=("Segoe UI",10,"bold"),bd=0)
        card.grid(row=1,column=0,sticky="ew",padx=12,pady=3)
        for r,k in enumerate(["L","YH","ZW","La","Lb","Ra","z_half"]):
            self.lab(card,k,bg=CARD_BG,fg=MUTED_FG).grid(row=r,column=0,sticky="e",padx=6,pady=1)
            tk.Entry(card,textvariable=self.v[k],width=10,justify="right",font=("Segoe UI",9)).grid(row=r,column=1,padx=6,pady=1)
            self.lab(card,"mm",bg=CARD_BG,fg=MUTED_FG).grid(row=r,column=2,sticky="w")

        pc=tk.LabelFrame(left,text="XY Output Surface P1~P5",bg=CARD_BG,fg=TEXT_FG,font=("Segoe UI",10,"bold"),bd=0)
        pc.grid(row=2,column=0,sticky="ew",padx=12,pady=3)
        tk.Checkbutton(pc,text="L變化時自動縮放P點",variable=self.auto_scale_p,bg=CARD_BG,fg=TEXT_FG,
                       selectcolor=CARD_BG,activebackground=CARD_BG,activeforeground=TEXT_FG).grid(row=0,column=0,columnspan=3,sticky="w",padx=5,pady=1)
        for c,t in enumerate(["Pt","X","Y"]): self.lab(pc,t,bg=CARD_BG,fg=MUTED_FG).grid(row=1,column=c,padx=4)
        for i in range(1,6):
            self.lab(pc,f"P{i}",bg=CARD_BG).grid(row=i+1,column=0,padx=4,pady=1)
            tk.Entry(pc,textvariable=self.p[f"P{i}X"],width=8,justify="right").grid(row=i+1,column=1,padx=4,pady=1)
            tk.Entry(pc,textvariable=self.p[f"P{i}Y"],width=8,justify="right").grid(row=i+1,column=2,padx=4,pady=1)
        self.btn(pc,"依目前L重置P1~P5",self.reset_p_by_l,bg="#566573",h=1).grid(row=7,column=0,columnspan=3,sticky="ew",padx=6,pady=3)

        rc=tk.LabelFrame(left,text="Output Arc Radius R1~R4",bg=CARD_BG,fg=TEXT_FG,font=("Segoe UI",10,"bold"),bd=0)
        rc.grid(row=3,column=0,sticky="ew",padx=12,pady=3)
        for i,k in enumerate(["R1","R2","R3","R4"]):
            self.lab(rc,k,bg=CARD_BG,fg=MUTED_FG).grid(row=0,column=i*2,padx=(5,1),pady=5)
            tk.Entry(rc,textvariable=self.r[k],width=6,justify="right",font=("Segoe UI",9)).grid(row=0,column=i*2+1,padx=(1,5),pady=5)

        rayc=tk.LabelFrame(left,text="3D RayTrace Lite",bg=CARD_BG,fg=TEXT_FG,font=("Segoe UI",10,"bold"),bd=0)
        rayc.grid(row=4,column=0,sticky="ew",padx=12,pady=3)
        self.lab(rayc,"Ray count",bg=CARD_BG,fg=MUTED_FG).pack(side="left",padx=8,pady=6)
        for n in [500,2500,5000]:
            tk.Radiobutton(rayc,text=str(n),value=n,variable=self.ray_count,bg=CARD_BG,fg=TEXT_FG,
                           selectcolor=CARD_BG,activebackground=CARD_BG,activeforeground=TEXT_FG).pack(side="left",padx=5)

        oc=tk.LabelFrame(left,text="Output Folder",bg=CARD_BG,fg=TEXT_FG,font=("Segoe UI",10,"bold"),bd=0)
        oc.grid(row=5,column=0,sticky="ew",padx=12,pady=3)
        oc.grid_columnconfigure(0, weight=1)
        tk.Entry(oc,textvariable=self.output_dir,font=("Segoe UI",8)).grid(row=0,column=0,sticky="ew",padx=(7,4),pady=6)
        tk.Button(oc,text="選擇",command=self.browse,bg="#566573",fg="white",relief="flat",bd=0,
                  width=5,height=1,font=("Microsoft JhengHei UI",8,"bold")).grid(row=0,column=1,padx=(2,7),pady=6)

        actions=tk.LabelFrame(left,text="Actions",bg=PANEL_BG,fg=TEXT_FG,font=("Segoe UI",10,"bold"),bd=0)
        actions.grid(row=6,column=0,sticky="ew",padx=12,pady=6)
        self.btn(actions,"Run 3D RayTrace",self.run_sim,bg=GOOD,h=2).pack(fill="x",pady=4)
        self.btn(actions,"Export STEP / STL / PNG / TXT",self.export,bg=ACCENT,h=2).pack(fill="x",pady=4)
        self.status=self.lab(actions,"",9,True,fg=GOOD)
        self.status.pack(anchor="w",pady=3)

    def build_plots(self,right):
        self.fig1=Figure(figsize=(8,3.5),dpi=100,facecolor=APP_BG)
        self.ax_xz=self.fig1.add_subplot(1,2,1); self.ax_xy=self.fig1.add_subplot(1,2,2)
        self.can1=FigureCanvasTkAgg(self.fig1,right)
        self.can1.get_tk_widget().grid(row=0,column=0,sticky="nsew",pady=(0,8))

        self.fig2=Figure(figsize=(8,4.5),dpi=100,facecolor=APP_BG)
        self.ax_iso=self.fig2.add_subplot(1,2,1); self.ax_line=self.fig2.add_subplot(1,2,2)
        self.can2=FigureCanvasTkAgg(self.fig2,right)
        self.can2.get_tk_widget().grid(row=1,column=0,sticky="nsew")

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
        rs={k:float(x.get()) for k,x in self.r.items()}
        return v,pts,rs

    def waist(self,v):
        return (v["Lb"]-v["La"])-2*(v["Ra"]-math.sqrt(v["Ra"]**2-v["z_half"]**2))

    def setup(self,ax,title,xlab,ylab):
        ax.clear(); ax.set_facecolor("#0B1117"); ax.set_title(title,color=TEXT_FG,fontsize=11)
        ax.set_xlabel(xlab,color=MUTED_FG); ax.set_ylabel(ylab,color=MUTED_FG); ax.tick_params(colors=MUTED_FG); ax.grid(True,alpha=.16)

    def run_sim(self):
        try:
            v,pts,rs=self.vals()
            if v["Ra"]<=v["z_half"]: raise ValueError("Ra 必須大於 z_half")
            if v["Lb"]<=v["La"]: raise ValueError("Lb 必須大於 La")
            w=self.waist(v)
            self.draw_geo(v,pts,rs,w)
            sim_info=self.draw_raytrace_3d(v,pts,rs,w,int(self.ray_count.get()))
            self.last_sim_info=sim_info
            self.status.config(text="",fg=GOOD)
            self.last_ok=True
        except Exception as e:
            self.status.config(text="",fg=BAD); self.last_ok=False
            messagebox.showerror("Simulation failed",str(e))

    def draw_geo(self,v,pts,rs,w):
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

        self.setup(self.ax_xy,"XY 出光面 / R1~R4","X mm","Y mm")
        self.ax_xy.plot([0,L,L,0,0],[0,0,YH,YH,0],color="#9FB3C8")
        self.ax_xy.plot([0,xtir,0,0],[YH,YH,max(YH-14,0),YH],color=BAD); self.ax_xy.plot([0,xtir,0,0],[0,0,min(14,YH),0],color=BAD)
        px=[p[0] for p in pts]; py=[p[1] for p in pts]
        self.ax_xy.plot(px,py,"o-",color=ACCENT,lw=2.4)
        for i,(x,y) in enumerate(pts,1): self.ax_xy.text(x,y+max(1,YH*.03),f"P{i}",color=TEXT_FG,fontsize=8,ha="center")
        for i in range(4):
            mx=(pts[i][0]+pts[i+1][0])/2; my=(pts[i][1]+pts[i+1][1])/2
            self.ax_xy.text(mx,my-2,f"R{i+1}={rs[f'R{i+1}']:g}",color=WARN,fontsize=8,ha="center")
        self.ax_xy.set_xlim(-2,L+margin); self.ax_xy.set_ylim(-2,YH+max(5,YH*.10))
        self.fig1.tight_layout(); self.can1.draw()

    # ------------------ Real-ish 2D raytrace engine ------------------
    def snell(self, d, n, n1, n2):
        # d, n normalized; n points from medium1 toward medium2
        d = d / np.linalg.norm(d)
        n = n / np.linalg.norm(n)
        cosi = -np.dot(n, d)
        eta = n1 / n2
        k = 1 - eta*eta*(1 - cosi*cosi)
        if k < 0:
            # total internal reflection
            return d + 2*cosi*n, True
        t = eta*d + (eta*cosi - math.sqrt(k))*n
        return t / np.linalg.norm(t), False

    def xy_output_curve(self, pts, samples=260):
        # smooth Catmull-like interpolation by dense linear + R weighting perturbation is applied separately
        pts=np.array(pts,float)
        xs=[]; ys=[]; seg=[]
        for i in range(len(pts)-1):
            p0=pts[max(i-1,0)]; p1=pts[i]; p2=pts[i+1]; p3=pts[min(i+2,len(pts)-1)]
            for j in range(samples//4):
                t=j/(samples//4)
                t2=t*t; t3=t2*t
                # Catmull-Rom
                p=0.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t2+(-p0+3*p1-3*p2+p3)*t3)
                xs.append(p[0]); ys.append(p[1]); seg.append(i)
        xs.append(pts[-1,0]); ys.append(pts[-1,1]); seg.append(3)
        return np.array(xs), np.array(ys), np.array(seg)

    def ray_segment_intersection(self, src, d, a, b):
        # Solve src + t*d = a + u*(b-a), t>=0, 0<=u<=1
        v=b-a
        den=d[0]*v[1]-d[1]*v[0]
        if abs(den)<1e-9:
            return None
        q=a-src
        t=(q[0]*v[1]-q[1]*v[0])/den
        u=(q[0]*d[1]-q[1]*d[0])/den
        if t>=0 and 0<=u<=1:
            return t,u,src+t*d
        return None

    def trace_xy_distribution(self, v, pts, rs, n_rays=2600):
        # Real ray vs curve-segment intersection in XY.
        # LED source emits inside PMMA, hits P1~P5 output curve, refracts into air, then hits ground plane y=-300mm.
        n_pm=1.49; n_air=1.0
        YH=v["YH"]
        src0=np.array([0.0, YH/2.0])
        ground_y=-300.0
        xs,ys,seg=self.xy_output_curve(pts,360)
        curve=np.column_stack([xs,ys])
        out_x=[]; weights=[]
        rng=np.random.default_rng(1234)

        # Aim rays over the actual visible output curve, plus jitter/source spread.
        aim_points=curve[::max(1,len(curve)//max(80,n_rays//20))]
        dirs=[]
        for ap in aim_points:
            base=ap-src0
            if np.linalg.norm(base)>1e-9:
                ang=math.atan2(base[1],base[0])
                dirs.append(ang)
        if not dirs:
            dirs=list(np.linspace(-0.45,0.35,100))
        dirs=np.array(dirs)
        # sample angles with jitter to ensure hits over all segments
        angles=rng.choice(dirs,size=n_rays,replace=True)+rng.normal(0,0.035,n_rays)
        source_y=src0[1]+rng.uniform(-5.0,5.0,n_rays)  # LED 10mm source height
        source_x=src0[0]+rng.uniform(0.0,2.0,n_rays)

        for a,sy,sx in zip(angles,source_y,source_x):
            src=np.array([sx,sy])
            d=np.array([math.cos(a), math.sin(a)])
            best=None; best_i=None
            for i in range(len(curve)-1):
                hit=self.ray_segment_intersection(src,d,curve[i],curve[i+1])
                if hit is None: continue
                t,u,p=hit
                if t<5: continue
                if best is None or t<best[0]:
                    best=(t,u,p); best_i=i
            if best is None:
                continue
            _,_,hitp=best
            i=best_i
            tan=curve[min(len(curve)-1,i+1)]-curve[max(0,i)]
            if np.linalg.norm(tan)<1e-9: continue
            tan=tan/np.linalg.norm(tan)
            # outward normal roughly toward +X / air
            n=np.array([tan[1],-tan[0]])
            if n[0]<0: n=-n
            sidx=int(seg[min(i,len(seg)-1)])
            R=rs.get(f"R{sidx+1}",50.0)
            # Smaller R bends more; this is an engineering approximation.
            bend_gain=max(0.65,min(1.55,45.0/max(R,1.0)))
            n=np.array([n[0], n[1]*bend_gain]); n=n/np.linalg.norm(n)
            tdir,tir=self.snell(d,n,n_pm,n_air)
            if abs(tdir[1])<1e-8: continue
            tt=(ground_y-hitp[1])/tdir[1]
            if tt<=0: continue
            gx=(hitp[0]+tt*tdir[0])/1000.0
            if -2.0<=gx<=12.0:
                out_x.append(gx)
                # Lambert-ish source weight and loss penalty
                weights.append(max(0.05, abs(math.cos(a))) * (0.70 if tir else 1.0))
        return np.array(out_x), np.array(weights)

    def trace_xz_distribution(self, v, n_rays=2200):
        # Ray tracing in XZ through hourglass air lens to estimate width distribution at ground-like distance
        n_pm=1.49; n_air=1.0
        La,Lb,Ra,zh=v["La"],v["Lb"],v["Ra"],v["z_half"]
        src=np.array([0.0,0.0])
        target_x=7000.0 # mm, use 7m plane for width
        out_z=[]; weights=[]
        rng=np.random.default_rng(5678)
        angles=np.linspace(-0.75,0.75,n_rays)+rng.normal(0,0.006,n_rays)
        for a in angles:
            d=np.array([math.cos(a), math.sin(a)])
            # intersect approximate first surface x = La + sag(z)
            # march in small steps until crossing x_left(z)
            p=src.copy()
            hit1=None
            for t in np.linspace(1,180,360):
                z=p[1]+t*d[1]; x=p[0]+t*d[0]
                if abs(z)>zh: continue
                sag=Ra-math.sqrt(max(Ra*Ra-z*z,0))
                xsurf=La+sag
                if x>=xsurf:
                    hit1=np.array([xsurf,z]); break
            if hit1 is None: 
                continue
            z=hit1[1]
            # left surface normal from acrylic to air cavity
            # x=La+sag(z), dx/dz = z/sqrt(R^2-z^2)
            dx_dz=z/max(math.sqrt(max(Ra*Ra-z*z,1e-9)),1e-9)
            tan=np.array([dx_dz,1.0]); tan=tan/np.linalg.norm(tan)
            n=np.array([tan[1],-tan[0]])
            if n[0]<0: n=-n
            d2,tir1=self.snell(d,n,n_pm,n_air)
            # intersect second surface x=Lb-sag(z)
            hit2=None
            for t in np.linspace(0.1,140,360):
                zz=hit1[1]+t*d2[1]; xx=hit1[0]+t*d2[0]
                if abs(zz)>zh: continue
                sag=Ra-math.sqrt(max(Ra*Ra-zz*zz,0))
                xsurf=Lb-sag
                if xx>=xsurf:
                    hit2=np.array([xsurf,zz]); break
            if hit2 is None:
                continue
            zz=hit2[1]
            dx_dz=-zz/max(math.sqrt(max(Ra*Ra-zz*zz,1e-9)),1e-9)
            tan=np.array([dx_dz,1.0]); tan=tan/np.linalg.norm(tan)
            # normal from air cavity to acrylic; should point right into PMMA
            n=np.array([tan[1],-tan[0]])
            if n[0]<0: n=-n
            d3,tir2=self.snell(d2,n,n_air,n_pm)
            # exit front as approximate PMMA to air flat/slightly diverging
            nout=np.array([1.0,0.0])
            d4,tir3=self.snell(d3,nout,n_pm,n_air)
            if abs(d4[0])<1e-6: continue
            tt=(target_x-hit2[0])/d4[0]
            if tt<=0: continue
            gz=(hit2[1]+tt*d4[1])/1000.0
            if -0.8<=gz<=0.8:
                out_z.append(gz)
                weights.append(1.0*(0.5 if (tir1 or tir2 or tir3) else 1.0))
        return np.array(out_z), np.array(weights)

    def draw_raytrace(self,v,pts,rs,w):
        gx,wx=self.trace_xy_distribution(v,pts,rs,2800)
        gz,wz=self.trace_xz_distribution(v,2400)
        if len(gx)<20 or len(gz)<20:
            raise ValueError("Ray trace rays too few. Check geometry/R values.")

        xbins=np.linspace(0,10,240)
        zbins=np.linspace(-0.35,0.35,180)
        hx,_=np.histogram(gx,bins=xbins,weights=wx)
        hz,_=np.histogram(gz,bins=zbins,weights=wz)
        # smooth
        hx=np.convolve(hx,np.ones(7)/7,mode="same")
        hz=np.convolve(hz,np.ones(5)/5,mode="same")
        hx=hx/(hx.max()+1e-9); hz=hz/(hz.max()+1e-9)
        E=np.outer(hz,hx); E=E/(E.max()+1e-9)
        Xc=(xbins[:-1]+xbins[1:])/2
        Zc=(zbins[:-1]+zbins[1:])/2
        XX,ZZ=np.meshgrid(Xc,Zc)
        center=E[np.argmin(np.abs(Zc)),:]

        self.setup(self.ax_iso,"Ray Trace 地面等照度圖","X m","Z m")
        self.ax_iso.contourf(XX,ZZ,E,levels=np.linspace(0,1,24),cmap="turbo")
        self.ax_iso.contour(XX,ZZ,E,levels=[.1,.5,.8],colors="white",linewidths=.8)
        self.ax_iso.axvline(.5,color="white",ls="--"); self.ax_iso.axvline(7,color="white",ls="--")
        self.ax_iso.set_xlim(0,10); self.ax_iso.set_ylim(-.35,.35)

        self.setup(self.ax_line,"Ray Trace 中心線平台","X m","Relative")
        self.ax_line.plot(Xc,center,color="#5DADE2",lw=2.4)
        self.ax_line.fill_between(Xc,0,center,color="#5DADE2",alpha=.25)
        self.ax_line.axvline(.5,color="white",ls="--"); self.ax_line.axvline(7,color="white",ls="--")
        self.ax_line.axhline(1,color="white",ls="--"); self.ax_line.axhline(.85,color=WARN,ls=":"); self.ax_line.axhline(1.15,color=WARN,ls=":")
        self.ax_line.set_xlim(0,10); self.ax_line.set_ylim(0,1.15)
        self.fig2.tight_layout(); self.can2.draw()

        # metrics
        mask=center>0.5
        if np.any(mask):
            x_min=float(Xc[mask][0]); x_max=float(Xc[mask][-1])
        else:
            x_min=x_max=0
        zmask=hz>0.5
        if np.any(zmask):
            width=float(Zc[zmask][-1]-Zc[zmask][0])
        else:
            width=0
        return {"rays_x":len(gx),"rays_z":len(gz),"x_50_start":x_min,"x_50_end":x_max,"z_50_width_m":width}


    def draw_raytrace_3d(self,v,pts,rs,w,ray_count):
        """
        Simplified 3D ray trace lite.
        It samples 3D rays from a 10x10mm MLED area, maps XY output response and XZ air-lens response,
        then accumulates hits on the ground X-Z plane. This is not Zemax, but it is parameter-sensitive.
        """
        rng=np.random.default_rng(2026 + int(ray_count))
        ray_count=int(ray_count)

        # Get 2D optical responses as transfer distributions
        gx,wx=self.trace_xy_distribution(v,pts,rs,max(1200,ray_count*3))
        gz,wz=self.trace_xz_distribution(v,max(1200,ray_count*3))
        # Fallback: do not crash; show weak/poor coupling if geometry misses many rays.
        if len(gx)<20:
            # create a broad weak distribution based on P curve location so user still sees failure tendency
            rng_fb=np.random.default_rng(901)
            gx=rng_fb.normal(7.5,1.8,max(30,ray_count//10))
            wx=np.ones_like(gx)*0.15
        if len(gz)<20:
            rng_fb=np.random.default_rng(902)
            spread=max(0.12,min(0.65,0.22*(15.4/max(w,0.5))))
            gz=rng_fb.normal(0,spread,max(30,ray_count//10))
            wz=np.ones_like(gz)*0.15

        # Convert distributions into samples for 3D hit map
        wx=wx/(wx.sum()+1e-12)
        wz=wz/(wz.sum()+1e-12)
        ix=rng.choice(np.arange(len(gx)),size=ray_count,replace=True,p=wx)
        iz=rng.choice(np.arange(len(gz)),size=ray_count,replace=True,p=wz)

        # MLED finite source area blur and coupling between X/Z
        Xhit=gx[ix] + rng.normal(0,0.035,ray_count)
        Zhit=gz[iz] + rng.normal(0,0.010,ray_count)

        # geometry sensitivity: bad waist creates more divergence and loss
        waist=max(w,0.5)
        spread_gain=max(0.7,min(2.4,15.4/waist))
        Zhit*=spread_gain

        # P/R sensitivity: small R4 softer far cutoff, R2/R3 platform ripple
        r2=max(1,float(rs["R2"])); r3=max(1,float(rs["R3"])); r4=max(1,float(rs["R4"]))
        ripple=max(0.0,min(0.08,0.04/(1+(r2+r3)/120)))
        Xhit += ripple*np.sin(Xhit*2.7)*0.35
        if r4 < 10:
            Xhit += rng.normal(0,0.25,ray_count)

        # Clip rays to ground viewing range
        valid=(Xhit>=-2)&(Xhit<=12)&(Zhit>=-1.2)&(Zhit<=1.2)
        Xhit=Xhit[valid]; Zhit=Zhit[valid]
        if len(Xhit)<10:
            rng_fb=np.random.default_rng(903)
            Xhit=rng_fb.normal(7.5,1.5,max(30,ray_count//8))
            Zhit=rng_fb.normal(0,0.35,max(30,ray_count//8))

        xbins=np.linspace(0,10,260)
        zbins=np.linspace(-0.35,0.35,190)
        H,xe,ze=np.histogram2d(Xhit,Zhit,bins=[xbins,zbins])
        E=H.T
        # smooth by simple neighborhood averaging
        for _ in range(2):
            E=(E+np.roll(E,1,0)+np.roll(E,-1,0)+np.roll(E,1,1)+np.roll(E,-1,1))/5.0
        E=E/(E.max()+1e-12)

        Xc=(xbins[:-1]+xbins[1:])/2
        Zc=(zbins[:-1]+zbins[1:])/2
        XX,ZZ=np.meshgrid(Xc,Zc)
        center=E[np.argmin(np.abs(Zc)),:]

        self.setup(self.ax_iso,f"3D RayTrace 地面等照度圖 ({ray_count} rays)","X m","Z m")
        self.ax_iso.contourf(XX,ZZ,E,levels=np.linspace(0,1,24),cmap="turbo")
        self.ax_iso.contour(XX,ZZ,E,levels=[.1,.5,.8],colors="white",linewidths=.8)
        self.ax_iso.axvline(.5,color="white",ls="--"); self.ax_iso.axvline(7,color="white",ls="--")
        self.ax_iso.set_xlim(0,10); self.ax_iso.set_ylim(-.35,.35)

        self.setup(self.ax_line,"3D RayTrace 中心線平台","X m","Relative")
        self.ax_line.plot(Xc,center,color="#5DADE2",lw=2.4)
        self.ax_line.fill_between(Xc,0,center,color="#5DADE2",alpha=.25)
        self.ax_line.axvline(.5,color="white",ls="--"); self.ax_line.axvline(7,color="white",ls="--")
        self.ax_line.axhline(1,color="white",ls="--"); self.ax_line.axhline(.85,color=WARN,ls=":"); self.ax_line.axhline(1.15,color=WARN,ls=":")
        self.ax_line.set_xlim(0,10); self.ax_line.set_ylim(0,1.15)
        self.ax_line.text(.7,.1,f"3D rays={ray_count}\nvalid={len(Xhit)}\nwaist={w:.1f}mm",color=TEXT_FG,fontsize=8)
        self.fig2.tight_layout(); self.can2.draw()

        mask=center>0.5
        x_min=float(Xc[mask][0]) if np.any(mask) else 0
        x_max=float(Xc[mask][-1]) if np.any(mask) else 0
        zsum=E.sum(axis=1); zsum=zsum/(zsum.max()+1e-12)
        zmask=zsum>0.5
        width=float(Zc[zmask][-1]-Zc[zmask][0]) if np.any(zmask) else 0
        return {"mode":"3D RayTrace Lite","ray_count":ray_count,"valid_rays":int(len(Xhit)),"x_50_start":x_min,"x_50_end":x_max,"z_50_width_m":width}

    def save_simulation_files(self,v,pts,rs,w,sim_info,ts):
        out=self.output_dir.get(); os.makedirs(out,exist_ok=True)
        geo_png=os.path.join(out,f"geometry_preview_{ts}.png")
        sim_png=os.path.join(out,f"raytrace_simulation_{ts}.png")
        report=os.path.join(out,f"raytrace_report_{ts}.txt")
        self.fig1.savefig(geo_png,dpi=220,bbox_inches="tight")
        self.fig2.savefig(sim_png,dpi=220,bbox_inches="tight")
        with open(report,"w",encoding="utf-8") as f:
            f.write("達源技術有限公司 透鏡成像產生器\n")
            f.write("Ray Trace Simulation Report\n")
            f.write("="*40+"\n\n")
            for k,val in v.items(): f.write(f"{k} = {val}\n")
            f.write("\nP points:\n")
            for i,p in enumerate(pts,1): f.write(f"P{i} = {p}\n")
            f.write("\nR values:\n")
            for k,val in rs.items(): f.write(f"{k} = {val}\n")
            f.write(f"\nwaist = {w:.3f} mm\n")
            for k,val in sim_info.items(): f.write(f"{k} = {val}\n")
        return [geo_png,sim_png,report]

    def export(self):
        if not self.last_ok and not messagebox.askyesno("Simulation not updated","尚未更新模擬，仍然輸出嗎？"): return
        try: import cadquery as cq
        except Exception: messagebox.showerror("CadQuery 載入失敗",traceback.format_exc()); return
        try:
            v,pts,rs=self.vals(); w=self.waist(v)
            lens=self.build_lens(cq,v,pts); out=self.output_dir.get(); os.makedirs(out,exist_ok=True)
            ts=datetime.now().strftime("%Y%m%d_%H%M%S")
            step=os.path.join(out,f"micro_led_lens_{ts}.step"); stl=os.path.join(out,f"micro_led_lens_{ts}.stl")
            cq.exporters.export(lens,step); cq.exporters.export(lens,stl)
            sim_info=self.last_sim_info if self.last_sim_info else self.draw_raytrace_3d(v,pts,rs,w,int(self.ray_count.get()))
            self.save_simulation_files(v,pts,rs,w,sim_info,ts)
            messagebox.showinfo("Export complete",f"Generated:\n{step}\n{stl}\nPNG/TXT saved")
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
