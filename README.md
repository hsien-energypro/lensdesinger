# MICRO LED Lens Designer V10

This GitHub project builds a Windows `LensDesigner.exe` using GitHub Actions.

## Files

- `LensDesigner.py` - Desktop UI and confirmed V10 CadQuery geometry.
- `.github/workflows/build-exe.yml` - GitHub Actions workflow to build EXE.

## V10 geometry rules

Coordinate system:

- X = 0 ~ L
- Y = 0 ~ 40
- Z = -30 ~ +30

Confirmed default parameters:

- L = 100
- YH = 40
- ZW = 60
- La = 24
- Lb = 44
- Ra = 72
- z_half = 18

Do not revert to old wrong geometry:

- no Y=-20~+20 main body
- no separated two air holes
- no fish-eye air hole
- no wedge/boat shape
- keep TIR cuts

## How to build EXE

1. Upload these files to a GitHub repository.
2. Go to `Actions`.
3. Choose `Build LensDesigner EXE`.
4. Click `Run workflow`.
5. Open the finished run.
6. Download `LensDesigner-Windows-EXE`.
7. Extract the ZIP, then run `LensDesigner.exe`.

## App use

1. Open `LensDesigner.exe`.
2. Choose output folder.
3. Click `Generate STEP / STL`.
4. It exports:
   - `micro_led_lens_v10.step`
   - `micro_led_lens_v10.stl`
