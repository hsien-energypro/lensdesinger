import os, sys
base=getattr(sys,"_MEIPASS",os.path.dirname(sys.executable))
paths=[base]
for root,dirs,files in os.walk(base):
    if any(f.lower().endswith((".dll",".pyd")) for f in files):
        paths.append(root)
for p in paths:
    try: os.add_dll_directory(p)
    except Exception: pass
os.environ["PATH"]=os.pathsep.join(paths+[os.environ.get("PATH","")])
