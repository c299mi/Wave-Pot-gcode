#!/usr/bin/env python3
"""
rect_wave_pot_grid_bottom.py ─ 外周フレーム付き最終版（中心配置修正）
────────────────────────────────────────────────────────────
• Ender-3 用：蛇行格子底 + 波形長方形側壁
• 初層 0.20 mm（Flow 120 %）→ 以降 0.40 mm ピッチ
• 格子は一筆書き＋外周フレームを毎層 1 周描画
• U ターンで corner-factor 倍速に減速し 0.2 s 冷却
• 全層押出倍率 (--flow-factor) で微調整
• ビルドプレート中心への自動配置機能追加
"""

from __future__ import annotations
import math, argparse
from pathlib import Path

# ── プリンタ設定 ────────────────────────────────────────────
BED_TEMP, EXTRUDER_TEMP = 60, 200           # °C
NOZZLE_DIAM, FILAMENT_DIAM = 0.4, 1.75      # mm

# Ender-3 のビルドプレート設定
BED_SIZE_X, BED_SIZE_Y = 235, 235            # mm
PRINT_MARGIN = 10                           # ビルドプレート端からの余裕（mm）

FIRST_LAYER_H     = 0.20   # mm
FIRST_LAYER_FLOW  = 1.20   # 初層だけ 120 %
LAYER_HEIGHT      = 0.40   # mm
LINE_WIDTH        = 0.45   # mm
RETRACTION_MM     = 2.0

FLOW_FACTOR   = 1.0        # CLI 上書き
CORNER_FACTOR = 1.0        # 〃（角だけ速度倍率）

# ── 押出係数 ───────────────────────────────────────────────
def extrusion_mult(h: float) -> float:
    base = (LINE_WIDTH * h) / (math.pi * (FILAMENT_DIAM / 2) ** 2)
    if abs(h - FIRST_LAYER_H) < 1e-6:
        base *= FIRST_LAYER_FLOW
    return base * FLOW_FACTOR

# ── 中心座標計算 ───────────────────────────────────────────
def calculate_center(width: float, height: float) -> tuple[float, float]:
    """オブジェクトサイズに基づいてビルドプレート中心座標を計算"""
    # ビルドプレートの中心
    bed_center_x = BED_SIZE_X / 2
    bed_center_y = BED_SIZE_Y / 2
    
    # オブジェクトがビルドプレートに収まるかチェック
    max_printable_x = BED_SIZE_X - 2 * PRINT_MARGIN
    max_printable_y = BED_SIZE_Y - 2 * PRINT_MARGIN
    
    if width > max_printable_x or height > max_printable_y:
        print(f"⚠️  警告: オブジェクトサイズ ({width}×{height}mm) が")
        print(f"    印刷可能エリア ({max_printable_x}×{max_printable_y}mm) を超えています")
        print(f"    はみ出す可能性があります。")
    
    # 中央配置の座標を返す
    cx = bed_center_x
    cy = bed_center_y
    
    print(f"📍 オブジェクト配置:")
    print(f"    中心座標: ({cx:.1f}, {cy:.1f})")
    print(f"    X範囲: {cx - width/2:.1f} ～ {cx + width/2:.1f}")
    print(f"    Y範囲: {cy - height/2:.1f} ～ {cy + height/2:.1f}")
    
    return cx, cy

# ── テンプレート G-code ────────────────────────────────────
def start_gcode() -> str:
    return f"""; ==== Ender-3 START ====
M140 S{BED_TEMP}
M104 S{EXTRUDER_TEMP}
M190 S{BED_TEMP}
M109 S{EXTRUDER_TEMP}
G28
G92 E0
; prime line
G1 Z0.3 F3000
G1 X0.1 Y20  F5000
G1 X0.1 Y200 E20  F1500
G1 X0.4 Y200 F5000
G1 X0.4 Y20  E40  F1500
G92 E0
; ==== print ====
"""

def end_gcode() -> str:
    return f"""; ==== End ====
G92 E0
G1 E-{RETRACTION_MM} F2400
G1 X0 Y220 F3000
M104 S0
M140 S0
M84
"""

# ── 波形外周 1 層 ────────────────────────────────────────────
def wave_rect_layer(*, cx, cy, width, height, z,
                    layer_no, feed, e0, amp, wx, wy, phase):
    hx, hy = width/2, height/2
    if layer_no % 2:
        amp = -amp
    edges = [((1,0), width, wx), ((0,-1), height, wy),
             ((-1,0), width, wx), ((0,1), height, wy)]
    seg   = [0, math.pi/2, math.pi, 3*math.pi/2, 2*math.pi]
    mult  = extrusion_mult(LAYER_HEIGHT)
    g = []

    for (dx,dy), L, N in edges:
        pts = [p + 2*math.pi*i for i in range(N) for p in seg]
        for s, e_ in zip(pts[:-1], pts[1:]):
            os, oe = math.sin(s+phase)*amp, math.sin(e_+phase)*amp
            if   (dx,dy)==(1,0):
                sx,sy = cx-hx+s*L/(2*math.pi*N), cy+hy+os
                ex,ey = cx-hx+e_*L/(2*math.pi*N), cy+hy+oe
            elif (dx,dy)==(0,-1):
                sx,sy = cx+hx+os, cy+hy-s*L/(2*math.pi*N)
                ex,ey = cx+hx+oe, cy+hy-e_*L/(2*math.pi*N)
            elif (dx,dy)==(-1,0):
                sx,sy = cx+hx-s*L/(2*math.pi*N), cy-hy-os
                ex,ey = cx+hx-e_*L/(2*math.pi*N), cy-hy-oe
            else:
                sx,sy = cx-hx-os, cy-hy+s*L/(2*math.pi*N)
                ex,ey = cx-hx-oe, cy-hy+e_*L/(2*math.pi*N)
            d = math.hypot(ex-sx, ey-sy)
            g.append(f"G1 X{sx:.3f} Y{sy:.3f} Z{z:.3f} F{feed}")
            e0 += d * mult
            g.append(f"G1 X{ex:.3f} Y{ey:.3f} Z{z:.3f} E{e0:.5f} F{feed}")
    return g, e0

# ── 蛇行格子 1 層（外周バー確定）────────────────────────────
def slit_layer(*, cx, cy, width, height, z, feed, e0,
               slit_w, slit_gap, orient, layer_h):
    g = []
    hx, hy = width/2, height/2
    mult   = extrusion_mult(layer_h)
    slowF  = int(feed * CORNER_FACTOR)

    if orient == "x":                         # 縦バー
        x   = cx - hx
        down = True
        while x < cx + hx - 1e-6:
            remaining = cx + hx - x
            w_now     = min(slit_w, remaining)
            x1 = x + w_now
            y0, y1 = (cy + hy, cy - hy) if down else (cy - hy, cy + hy)

            d = abs(y1 - y0)
            g.append(f"G1 X{x:.3f} Y{y0:.3f} Z{z:.3f} F{feed}")
            e0 += d * mult
            g.append(f"G1 X{x:.3f} Y{y1:.3f} Z{z:.3f} E{e0:.5f} F{feed}")

            e0 += w_now * mult
            g.append(f"G1 X{x1:.3f} Y{y1:.3f} Z{z:.3f} E{e0:.5f} F{slowF}")
            g.append("G4 P200")

            # 次ストローク位置
            if remaining - w_now >= slit_gap + 1e-6:
                e0 += slit_gap * mult
                x += w_now + slit_gap
                g.append(f"G1 X{x:.3f} Y{y1:.3f} Z{z:.3f} "
                         f"E{e0:.5f} F{slowF}")
            else:
                break
            down = not down

        # 外周右端が描かれていなければ追い打ち
        if abs((cx+hx) - x1) > 1e-6:
            extra = (cx + hx) - x1
            e0 += extra * mult
            g.append(f"G1 X{cx+hx:.3f} Y{y1:.3f} Z{z:.3f} "
                     f"E{e0:.5f} F{slowF}")

    else:                                      # 横バー
        y   = cy - hy
        right = True
        while y < cy + hy - 1e-6:
            remaining = cy + hy - y
            h_now     = min(slit_w, remaining)
            y1 = y + h_now
            x0, x1 = (cx - hx, cx + hx) if right else (cx + hx, cx - hx)

            d = abs(x1 - x0)
            g.append(f"G1 X{x0:.3f} Y{y:.3f} Z{z:.3f} F{feed}")
            e0 += d * mult
            g.append(f"G1 X{x1:.3f} Y{y:.3f} Z{z:.3f} E{e0:.5f} F{feed}")

            e0 += h_now * mult
            g.append(f"G1 X{x1:.3f} Y{y1:.3f} Z{z:.3f} E{e0:.5f} F{slowF}")
            g.append("G4 P200")

            if remaining - h_now >= slit_gap + 1e-6:
                e0 += slit_gap * mult
                y += h_now + slit_gap
                g.append(f"G1 X{x1:.3f} Y{y:.3f} Z{z:.3f} "
                         f"E{e0:.5f} F{slowF}")
            else:
                break
            right = not right

        # 外周上端が描かれていなければ追い打ち
        if abs((cy+hy) - y1) > 1e-6:
            extra = (cy + hy) - y1
            e0 += extra * mult
            g.append(f"G1 X{x1:.3f} Y{cy+hy:.3f} Z{z:.3f} "
                     f"E{e0:.5f} F{slowF}")

    return g, e0

# ── 全体生成 ───────────────────────────────────────────────
def generate_part(*, outfile, width, height, phase, amp,
                  wx, wy, grid_layers, slit_w, slit_gap,
                  z_max, feed, cx=None, cy=None):
    
    # 中心座標の自動計算（指定されていない場合）
    if cx is None or cy is None:
        cx, cy = calculate_center(width, height)
    
    gcode, e0 = [], 0.0
    hx, hy    = width/2, height/2

    # 格子底（各層ごとにフレームも追加）
    for l in range(grid_layers):
        z  = FIRST_LAYER_H if l == 0 else FIRST_LAYER_H + LAYER_HEIGHT * l
        lh = FIRST_LAYER_H if l == 0 else LAYER_HEIGHT
        orient = "x" if l % 2 == 0 else "y"
        lay, e0 = slit_layer(cx=cx, cy=cy, width=width, height=height,
                             z=z, feed=feed, e0=e0,
                             slit_w=slit_w, slit_gap=slit_gap,
                             orient=orient, layer_h=lh)
        gcode += lay

        # 外周フレーム 1 周
        mult = extrusion_mult(lh)
        frame = [
            (cx-hx, cy-hy, cx+hx, cy-hy),  # 下 →
            (cx+hx, cy-hy, cx+hx, cy+hy),  # 右 ↑
            (cx+hx, cy+hy, cx-hx, cy+hy),  # 上 ←
            (cx-hx, cy+hy, cx-hx, cy-hy),  # 左 ↓
        ]
        for x0,y0,x1,y1 in frame:
            gcode.append(f"G1 X{x0:.3f} Y{y0:.3f} Z{z:.3f} F{feed}")
            e0 += math.hypot(x1-x0, y1-y0) * mult
            gcode.append(f"G1 X{x1:.3f} Y{y1:.3f} Z{z:.3f} E{e0:.5f} F{feed}")

    # 波形側壁
    z = FIRST_LAYER_H + LAYER_HEIGHT * grid_layers
    layer_no = 1
    while z <= z_max + 1e-6:
        wall, e0 = wave_rect_layer(cx=cx, cy=cy, width=width, height=height,
                                   z=z, layer_no=layer_no, feed=feed, e0=e0,
                                   amp=amp, wx=wx, wy=wy, phase=phase)
        gcode += wall
        z += LAYER_HEIGHT
        layer_no += 1

    Path(outfile).write_text(start_gcode() + "\n".join(gcode) + end_gcode())
    print("✅  G-code written:", outfile)

# ── CLI ───────────────────────────────────────────────────
def main():
    global FLOW_FACTOR, CORNER_FACTOR
    ap = argparse.ArgumentParser("Snake-grid bottom + wave walls G-code")
    ap.add_argument("-o", "--outfile", default="part.gcode")
    ap.add_argument("--width", type=float, default=71.6)
    ap.add_argument("--height", type=float, default=147.6)
    ap.add_argument("--phase", type=float, default=0.0)
    ap.add_argument("--amp", type=float, default=2.5)
    ap.add_argument("--wavelength", type=float, default=0.0)
    ap.add_argument("--waves-x", type=int, default=4)
    ap.add_argument("--waves-y", type=int, default=8)
    ap.add_argument("--grid-layers", type=int, default=2)
    ap.add_argument("--slit-width", type=float, default=2.0)
    ap.add_argument("--slit-gap", type=float, default=2.0)
    ap.add_argument("--z-max", type=float, default=25.0)
    ap.add_argument("--flow-factor", type=float, default=1.0)
    ap.add_argument("--corner-factor", type=float, default=1.0)
    # 中心座標の手動指定オプション追加
    ap.add_argument("--center-x", type=float, help="手動で中心X座標を指定")
    ap.add_argument("--center-y", type=float, help="手動で中心Y座標を指定")
    args, _ = ap.parse_known_args()

    FLOW_FACTOR   = args.flow_factor
    CORNER_FACTOR = max(0.05, min(args.corner_factor, 1.0))

    wx, wy = (max(1, round(args.width  / args.wavelength)),
              max(1, round(args.height / args.wavelength))) if args.wavelength > 0 \
             else (args.waves_x, args.waves_y)

    # 中心座標の設定（手動指定がある場合はそれを使用）
    cx = args.center_x
    cy = args.center_y

    generate_part(outfile=args.outfile, width=args.width, height=args.height,
                  phase=args.phase, amp=args.amp,
                  wx=wx, wy=wy, grid_layers=args.grid_layers,
                  slit_w=args.slit_width, slit_gap=args.slit_gap,
                  z_max=args.z_max, feed=1200, cx=cx, cy=cy)

if __name__ == "__main__":
    main()