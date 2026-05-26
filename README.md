# LensDesignerPro V10.1 3D RayTrace Robust

修正：
- 放寬有效光線判定，不會一開始就 rays too few。
- X/Y/Z clipping 放寬，最後再投影到 0~10m / ±0.35m 顯示視窗。
- XY/XZ ray fan 加寬，500/2500/5000 都能跑。
- 保留：Run 3D RayTrace 只更新畫面；Export 才輸出 STEP/STL/PNG/TXT。

注意：這仍是自製 3D RayTrace Lite，不是 Zemax。
