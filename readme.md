# Wave‑Pot G‑code Generator ― 日本語版 README

Ender‑3（Marlin ファーム）向けに、**波形側壁**と **格子状底面**をもつ長方形ポットの G‑code を生成するスクリプトです。外形サイズ・波形・格子パラメータをすべてコマンドラインで指定できます。

---

## 特長

* **フットプリントを完全パラメトリック** – `--width`×`--height` で iPhone サイズから 10 mm キューブまで
* **波形側壁** – 振幅・波長 / 波数・位相（0 と π で噛み合う）を自由設定
* **格子底面** – 蛇行一筆書きで出力し、最後に外周バーを必ず追加

  * 角は **速度を減速**（`--corner-factor`）し **0.2 秒停止**して剥がれを防止
* **初層だけ押出 120 %**（0.20 mm）、2 層目以降は 0.40 mm ピッチ
* **全層押出倍率** `--flow-factor` で一括微調整
* 単一ファイル CLI（`rect_wave_pot_grid_bottom.py`）
* Jupyter でも動作（`-f` フラグを無視）

---

## 動作環境

* Python 3.8 以降
* 追加ライブラリ不要（標準の *argparse*、*math*、*pathlib* のみ）
* Marlin ファームの 3D プリンタ（温度などは Ender‑3 用既定値。必要に応じて変更）

---

## クイックスタート

```bash
# 100 mm × 100 mm、波長 15 mm、角速度 30%、押出 200%
python rect_wave_pot_grid_bottom.py \
  -o square100.gcode \
  --width 100 --height 100 \
  --wavelength 15 --amp 3 \
  --grid-layers 3 --z-max 25 \
  --flow-factor 2 --corner-factor 0.3
```

生成された **.gcode** を SD カードに入れて印刷してください。

---

## コマンドラインオプション一覧

| オプション                    | 既定値          | 説明                                     |
| ------------------------ | ------------ | -------------------------------------- |
| `-o`, `--outfile`        | `part.gcode` | G‑code 生成先ファイル名                        |
| `--width`                | 71.6         | 外形 X サイズ (mm)                          |
| `--height`               | 147.6        | 外形 Y サイズ (mm)                          |
| `--phase`                | 0.0          | 波の位相 (rad) ─ 0 と π で噛み合いペア             |
| `--amp`                  | 2.5          | 波振幅 (mm)                               |
| `--wavelength`           | 0.0          | 波長 λ (mm) を固定。>0 で `--waves-x/y` を自動計算 |
| `--waves-x`, `--waves-y` | 4 / 8        | λ を指定しない場合の手動波数                        |
| `--grid-layers`          | 2            | 底面格子層数（1 層=0.20 mm + 0.40 mm×(n‑1)）    |
| `--slit-width`           | 2.0          | 格子バー幅 (mm)                             |
| `--slit-gap`             | 2.0          | 格子バー間隔 (mm)                            |
| `--z-max`                | 25.0         | 造形高さ Z\_max (mm)                       |
| `--flow-factor`          | 1.0          | 全層押出倍率 (例 1.5=+50 %)                   |
| `--corner-factor`        | 1.0          | U ターン部の速度倍率 (0.3=30 %)                 |

---

## 例

### 噛み合うペア

```bash
python rect_wave_pot_grid_bottom.py -o left.gcode  --phase 0
python rect_wave_pot_grid_bottom.py -o right.gcode --phase 3.14159
```

### 固定波長で自動波数

```bash
python rect_wave_pot_grid_bottom.py -o tray_iphone.gcode \
  --width 71.6 --height 147.6 \
  --wavelength 20  # λ=20 mm → X:4 波, Y:7 波
```

### 超小型 10 mm 角

```bash
python rect_wave_pot_grid_bottom.py -o cube10.gcode \
  --width 10 --height 10 \
  --waves-x 2 --waves-y 2 \
  --grid-layers 1 --slit-width 1 --slit-gap 1
```

---

## 調整ポイント（他機種の場合）

* `BED_TEMP`, `EXTRUDER_TEMP` を材料に合わせて変更
* ノズル径に応じて `LINE_WIDTH` / `FIRST_LAYER_H` / `LAYER_HEIGHT` を調整
* プリンタ固有のスタート / エンド G-code は `start_gcode()` / `end_gcode()` を差し替え

---

## よくあるトラブル

| 症状          | 対処                                                      |
| ----------- | ------------------------------------------------------- |
| 1 層目が薄い／剥がれ | `FIRST_LAYER_FLOW` をさらに上げる・ベッド温度+5 °C・速度を落とす            |
| 波がつぶれる      | `--amp` を増やす or 印刷温度を下げる                                |
| ペアが噛み合わない   | `--phase` が 0 / π になっているか確認、押出過多なら `--flow-factor` を下げる |

---

## ライセンス

MIT License — © 2025 Migaku Onoshi
