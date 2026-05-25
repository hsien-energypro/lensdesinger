# 達源技術有限公司 透鏡成像產生器 - V3 修正版

修正項目：
1. `runtime_hook.py` 修 CadQuery / CasADi DLL 載入，解決 Export STEP/STL 跳錯。
2. 右側等照度圖會跟 L / La / Lb / Ra / P1~P5 改變。
3. workflow 會自動使用根目錄的 `icon.ico`；沒有也能編譯。

GitHub 上請保留：
- LensDesignerPro.py
- runtime_hook.py
- README.md
- .github/workflows/build-exe.yml
- icon.ico（可選，放根目錄）

下載 Artifact 後一定要保留整個 LensDesignerPro 資料夾，不要只拿 EXE。
