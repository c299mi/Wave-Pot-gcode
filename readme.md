# Wave‑Pot G‑code Generator ― 日本語版 README

Ender‑3（Marlin ファーム）向けに、**波形側壁**と **格子状底面**をもつ長方形ポットの G‑code を生成するスクリプトです。外形サイズ・波形・格子パラメータをすべてコマンドラインで指定できます。

---

## 特長

* **フットプリントを完全パラメトリック** – `--width`×`--height` でサイズ指定
* **波形側壁** – 振幅・波長 / 波数・位相（0 と π で噛み合う）を自由設定
* **格子底面** – 蛇行一筆書きで出力し、最後に外周バーを必ず追加
  * 角は **速度を減速**（`--corner-factor`）し **0.2 秒停止**して剥がれを防止
* **1.0mm ノズル最適化** – 高速造形と強度を両立、大型パーツに最適
* **初層だけ押出 120 %**（0.20 mm）、2 層目以降は 0.40 mm ピッチ
* **全層押出倍率** `--flow-factor` で一括微調整
* **ビルドプレート自動中央配置** – Ender-3 サイズに最適化、印刷範囲外チェック機能付き
* **初層高さ調整機能** – `--first-layer-height` で 0.05〜1.0mm の範囲で指定可能
* 単一ファイル CLI（`rect_wave_pot_grid_bottom.py`）
* Jupyter でも動作（`-f` フラグを無視）

---

## 動作環境

* Python 3.8 以降
* 追加ライブラリ不要（標準の *argparse*、*math*、*pathlib* のみ）
* Marlin ファームの 3D プリンタ（Ender‑3 用既定値）
* **⚠️ 重要: 現在の設定は 1.0mm ノズル専用です**

---

## クイックスタート

```bash
# 150 mm × 150 mm、中央配置、初層 0.15mm 側面高さ25 ㎜
python rect_wave_pot_grid_bottom.py \
  -o square150.gcode \
  --width 150 --height 150 \
  --wavelength 20 --amp 3 \
  --first-layer-height 0.15 \
  --grid-layers 3 --z-max 25 \
  --flow-factor 1.1 --corner-factor 0.8
```

生成された **.gcode** を SD カードに入れて印刷してください。

---

## コマンドラインオプション一覧

| オプション                         | 既定値          | 説明                                     |
| ----------------------------- | ------------ | -------------------------------------- |
| `-o`, `--outfile`             | `part.gcode` | G‑code 生成先ファイル名                        |
| `--width`                     | 71.6         | 外形 X サイズ (mm)                          |
| `--height`                    | 147.6        | 外形 Y サイズ (mm)                          |
| `--phase`                     | 0.0          | 波の位相 (rad) ─ 0 と π で噛み合いペア             |
| `--amp`                       | 2.5          | 波振幅 (mm)                               |
| `--wavelength`                | 0.0          | 波長 λ (mm) を固定。>0 で `--waves-x/y` を自動計算 |
| `--waves-x`, `--waves-y`      | 4 / 8        | λ を指定しない場合の手動波数                        |
| `--grid-layers`               | 2            | 底面格子層数（1 層=0.20 mm + 0.40 mm×(n‑1)）    |
| `--slit-width`                | 2.0          | 格子バー幅 (mm)                             |
| `--slit-gap`                  | 2.0          | 格子バー間隔 (mm)                            |
| `--z-max`                     | 25.0         | 造形高さ Z\_max (mm)                       |
| `--flow-factor`               | 1.0          | 全層押出倍率 (例 1.5=+50 %)                   |
| `--corner-factor`             | 1.0          | U ターン部の速度倍率 (0.3=30 %)                 |
| `--first-layer-height`        | 0.20         | 初層のZ軸高さ (mm) 範囲: 0.05〜1.0            |
| `--center-x`, `--center-y`    | 自動計算       | 手動で中心座標を指定 (mm)                       |

---

## 使用例

### 標準的な iPhone サイズのトレイ

```bash
python rect_wave_pot_grid_bottom.py \
  -o iphone_tray.gcode \
  --width 71.6 --height 147.6 \
  --wavelength 15 --amp 2.5 \
  --first-layer-height 0.15
```

### 噛み合うペア（左右セット）

```bash
# 左側ポット
python rect_wave_pot_grid_bottom.py \
  -o left_pot.gcode \
  --width 100 --height 100 \
  --phase 0 --amp 3

# 右側ポット（噛み合う）
python rect_wave_pot_grid_bottom.py \
  -o right_pot.gcode \
  --width 100 --height 100 \
  --phase 3.14159 --amp 3
```

### 固定波長で自動波数計算

```bash
python rect_wave_pot_grid_bottom.py \
  -o auto_wave.gcode \
  --width 120 --height 80 \
  --wavelength 20  # λ=20mm → X:6波, Y:4波を自動計算
```

### 超小型キューブ（10mm角）

```bash
python rect_wave_pot_grid_bottom.py \
  -o mini_cube.gcode \
  --width 10 --height 10 \
  --waves-x 2 --waves-y 2 \
  --grid-layers 1 --slit-width 1 --slit-gap 1 \
  --first-layer-height 0.15
```

### 大型ポット（カスタム中心座標）

```bash
python rect_wave_pot_grid_bottom.py \
  -o large_pot.gcode \
  --width 150 --height 150 \
  --center-x 100 --center-y 100 \
  --flow-factor 1.2 --corner-factor 0.6
```

---

## 印刷設定の調整ポイント

### ⚠️ ノズルサイズの重要な注意事項

**現在のスクリプトは 1.0mm ノズル専用に調整されています。**

現在の設定値：
```python
NOZZLE_DIAM = 1.0        # 1.0mm ノズル
LINE_WIDTH = 2.0         # ライン幅 2.0mm
FIRST_LAYER_H = 0.20     # 初層高さ
LAYER_HEIGHT = 0.40      # レイヤー高さ
```

### 他のノズルサイズへの対応

他のノズルサイズで試す場合は以下を参考にしてください。
あくまで参考程度です。

| ノズル径  | 推奨ライン幅 | 初層高さ | レイヤー高さ | 備考                    |
| ----- | ------ | ---- | ------ | --------------------- |
| 0.4mm | 0.45mm | 0.05 | 0.20   | 標準ノズル（細かい造形向け）        |
| 0.8mm | 0.90mm | 0.15 | 0.35   | 高速造形向け                |
| **1.0mm** | **2.0mm** | **0.20** | **0.40** | **現在の設定（高速・大型造形向け）** |

### 他機種・他ノズルサイズへの変更方法

スクリプト内の以下の値を変更してください：

```python
# ノズル・材料設定
NOZZLE_DIAM = 1.0        # ← ノズル径に合わせて変更
LINE_WIDTH = 2.0         # ← ノズル径×1.1〜2.0倍に設定
FIRST_LAYER_H = 0.20     # ← ノズル径×0.1〜0.3倍
LAYER_HEIGHT = 0.40      # ← ノズル径×0.2〜0.8倍

# 温度設定
BED_TEMP = 60            # ← 材料に合わせて調整
EXTRUDER_TEMP = 200      # ← 材料に合わせて調整
```

### プリンタ固有設定の変更

* スタート/エンド G-code は `start_gcode()` / `end_gcode()` 関数を編集
* ビルドプレートサイズは `BED_SIZE_X`, `BED_SIZE_Y` を変更

### 材料別の推奨設定（1.0mm ノズル用）

| 材料  | ベッド温度 | ノズル温度 | 初層高さ     | フロー係数 | 備考                    |
| --- | ----- | ----- | -------- | ----- | --------------------- |
| PLA | 60°C  | 200°C | 0.2〜0.25 | 1.0   | 1mmノズルでも良好な仕上がり      |
| ABS | 80°C  | 240°C | 0.25〜0.3 | 1.1   | エンクロージャー推奨           |

**注意**: 1.0mmノズルは高流量のため、通常より高めの温度設定が必要な場合があります。

---

## よくあるトラブル

| 症状                 | 対処法                                                          |
| ------------------ | ------------------------------------------------------------ |
| 1 層目が薄い／剥がれる      | `--first-layer-height` を 0.25〜0.30 に・ベッド温度+5°C・速度を落とす、初層流量を大きくする        |
| 波がつぶれる             | `--amp` を増やす or 印刷温度を下げる                                    |
| ペアが噛み合わない          | `--phase` が 0 / π になっているか確認、押出過多なら `--flow-factor` を下げる     |
| ビルドプレートからはみ出す      | `--width`、`--height` を小さくするか `--center-x/y` で位置調整              |
| 格子が弱い              | `--grid-layers` を増やす・`--slit-width` を太くする                     |
| コーナーで糸引きが発生        | `--corner-factor` を 0.5〜0.8 に下げる・リトラクション設定を調整              |
| 全体的に押出不足／過多       | `--flow-factor` で調整（不足: 1.1〜1.2、過多: 0.9〜0.95）               |
| 押出が追いつかない          | ノズル温度を+10〜20°C上げる・印刷速度を下げる・フィラメント径を確認                    |
| ライン間の接着不良          | `LINE_WIDTH` を1.5〜2.5mmに調整・レイヤー高さを下げる                       |
| 細部がつぶれる            | 小さなパーツには不向き・最小幅3mm以上で設計する                               |

---

## 機能更新履歴

### v2.0.0 (2025-05-27)
- ✅ ビルドプレート自動中央配置機能追加
- ✅ 初層高さ調整オプション (`--first-layer-height`) 追加
- ✅ 印刷設定表示機能追加
- ✅ 印刷範囲チェック機能追加
- ✅ 手動中心座標指定オプション追加

### v1.0.0
- 🎉 初期リリース
- 波形側壁・格子底面生成機能
- パラメトリック設計対応

---

## ライセンス

MIT License — © 2025 Migaku Onoshi

---

## 貢献・サポート

バグ報告や機能要望は Issue でお知らせください。プルリクエストも歓迎します！

### 開発環境セットアップ

```bash
git clone [リポジトリURL]
cd wave-pot-generator
python rect_wave_pot_grid_bottom.py --help
```