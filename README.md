# LensDesignerPro V10.2 Intersection RayTrace

修正：
- XY 光追改成真正 ray vs output-curve segment intersection，不再用 nearest point 假交點。
- 放寬 XZ/3D clipping，不會預設值就 rays too few。
- 若幾何真的 miss，會顯示弱光型而不是直接空白。
- UI 基本不變。
