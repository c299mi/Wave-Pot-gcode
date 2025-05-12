#!/usr/bin/env python3
"""
rect_wave_pot_grid_bottom.py  ―― 0.4 mm レイヤー版
────────────────────────────────────────────────────────────
• Ender-3 用：蛇行格子底 ＋ 波形長方形側壁
• 初層 0.20 mm だけ Flow120 %、以降レイヤーピッチ 0.40 mm
• 角速度倍率 (--corner-factor) + 冷却 G4 P200
• 全層押出倍率 (--flow-factor) も指定可
"""

from __future__ import annotations
import math, argparse
from pathlib import Path

# ── ハード定数 ───────────────────────────────────────────────
BED_TEMP, EXTRUDER_TEMP       = 60, 200      # °C
NOZZLE_DIAM, FILAMENT_DIAM    = 0.4, 1.75    # mm

FIRST_LAYER_H   = 0.20    # mm  (flow 120 %)
FIRST_LAYER_FLOW= 1.20
LAYER_HEIGHT    = 0.40    # mm  ←★ 0.8 → 0.4 に変更
LINE_WIDTH      = 0.45
RETRACTION_MM   = 2.0

FLOW_FACTOR   = 1.0       # CLI 上書き
CORNER_FACTOR = 1.0       # 〃

# ── 押出量計算 ──────────────────────────────────────────────
def extrusion_mult(h: float) -> float:
    base = (LINE_WIDTH * h)/(math.pi*(FILAMENT_DIAM/2)**2)
    if abs(h - FIRST_LAYER_H) < 1e-6:          # 初層だけ増量
        base *= FIRST_LAYER_FLOW
    return base * FLOW_FACTOR

# ── G-code テンプレート ────────────────────────────────────
def start_gcode() -> str: return f"""\
; ==== Ender-3 START ====
M140 S{BED_TEMP}
M104 S{EXTRUDER_TEMP}
M190 S{BED_TEMP}
M109 S{EXTRUDER_TEMP}
G28
G92 E0
G1 Z0.3 F3000
G1 X0.1 Y20  F5000
G1 X0.1 Y200 E20  F1500
G1 X0.4 Y200 F5000
G1 X0.4 Y20  E40  F1500
G92 E0
; ==== print ====
"""

def end_gcode() -> str: return f"""\
; ==== End ====
G92 E0
G1 E-{RETRACTION_MM} F2400
G1 X0 Y220 F3000
M104 S0
M140 S0
M84
"""

# ── 波形外周 1 層 ------------------------------------------------
def wave_rect_layer(*, cx, cy, width, height, z, layer_no,
                    feed, e0, amp, wx, wy, phase):
    hx, hy = width/2, height/2
    if layer_no % 2: amp = -amp
    edges = [((1,0),width,wx),((0,-1),height,wy),
             ((-1,0),width,wx),((0,1),height,wy)]
    g, mult = [], extrusion_mult(LAYER_HEIGHT)
    seg=[0,math.pi/2,math.pi,3*math.pi/2,2*math.pi]
    for (dx,dy),L,N in edges:
        pts=[p+2*math.pi*i for i in range(N) for p in seg]
        for s,e_ in zip(pts[:-1],pts[1:]):
            os,oe=math.sin(s+phase)*amp,math.sin(e_+phase)*amp
            if   (dx,dy)==(1,0): sx,sy=cx-hx+s*L/(2*math.pi*N),cy+hy+os; ex,ey=cx-hx+e_*L/(2*math.pi*N),cy+hy+oe
            elif (dx,dy)==(0,-1):sx,sy=cx+hx+os,cy+hy-s*L/(2*math.pi*N); ex,ey=cx+hx+oe,cy+hy-e_*L/(2*math.pi*N)
            elif (dx,dy)==(-1,0):sx,sy=cx+hx-s*L/(2*math.pi*N),cy-hy-os; ex,ey=cx+hx-e_*L/(2*math.pi*N),cy-hy-oe
            else:                sx,sy=cx-hx-os,cy-hy+s*L/(2*math.pi*N); ex,ey=cx-hx-oe,cy-hy+e_*L/(2*math.pi*N)
            d=math.hypot(ex-sx,ey-sy)
            g.append(f"G1 X{sx:.3f} Y{sy:.3f} Z{z:.3f} F{feed}")
            e0+=d*mult
            g.append(f"G1 X{ex:.3f} Y{ey:.3f} Z{z:.3f} E{e0:.5f} F{feed}")
    return g,e0

# ── 蛇行格子 1 層 -------------------------------------------------
# ── 蛇行格子 1 層（外周バーを必ず追加）────────────────────
def slit_layer(
    *, cx, cy, width, height, z, feed, e0,
    slit_w, slit_gap, orient, layer_h
):
    """
    一筆書きのスネーク充填。
    ・最後に残った余り幅(< slit_w) でも外周にバーを敷く
    ・Uターン区間は corner-factor で減速し、0.2 s ドウェル
    ・押出は常に連続
    """
    gcode = []
    hx, hy = width / 2, height / 2
    mult   = extrusion_mult(layer_h)
    slowF  = int(feed * CORNER_FACTOR)

    if orient == "x":                           # 縦バー蛇行
        x = cx - hx
        down = True
        while x < cx + hx - 1e-6:
            # 残り幅を確認し、最後は残量ぶんでバーを延長
            remaining = cx + hx - x
            w_now = slit_w if remaining > slit_w else remaining
            x1 = x + w_now

            y0, y1 = (cy + hy, cy - hy) if down else (cy - hy, cy + hy)
            # 縦バー（通常速度）
            dist_v = abs(y1 - y0)
            gcode.append(f"G1 X{x:.3f} Y{y0:.3f} Z{z:.3f} F{feed}")
            e0 += dist_v * mult
            gcode.append(f"G1 X{x:.3f} Y{y1:.3f} Z{z:.3f} E{e0:.5f} F{feed}")

            # Uターン横（低速）
            dist_h = w_now
            e0 += dist_h * mult
            gcode.append(f"G1 X{x1:.3f} Y{y1:.3f} Z{z:.3f} E{e0:.5f} F{slowF}")
            gcode.append("G4 P200")                      # 冷却

            # 次バーの開始位置
            x_next = x1 + slit_gap
            if x_next < cx + hx - 1e-6:                  # まだ入る
                e0 += slit_gap * mult
                gcode.append(f"G1 X{x_next:.3f} Y{y1:.3f} Z{z:.3f} "
                             f"E{e0:.5f} F{slowF}")
            x = x_next
            down = not down

    else:                                              # 横バー蛇行
        y = cy - hy
        right = True
        while y < cy + hy - 1e-6:
            remaining = cy + hy - y
            h_now = slit_w if remaining > slit_w else remaining
            y1 = y + h_now

            x0, x1 = (cx - hx, cx + hx) if right else (cx + hx, cx - hx)
            # 横バー（通常速度）
            dist_h = abs(x1 - x0)
            gcode.append(f"G1 X{x0:.3f} Y{y:.3f} Z{z:.3f} F{feed}")
            e0 += dist_h * mult
            gcode.append(f"G1 X{x1:.3f} Y{y:.3f} Z{z:.3f} E{e0:.5f} F{feed}")

            # Uターン縦（低速）
            dist_v = h_now
            e0 += dist_v * mult
            gcode.append(f"G1 X{x1:.3f} Y{y1:.3f} Z{z:.3f} E{e0:.5f} F{slowF}")
            gcode.append("G4 P200")

            y_next = y1 + slit_gap
            if y_next < cy + hy - 1e-6:
                e0 += slit_gap * mult
                gcode.append(f"G1 X{x1:.3f} Y{y_next:.3f} Z{z:.3f} "
                             f"E{e0:.5f} F{slowF}")
            y = y_next
            right = not right
    return gcode, e0

# ── 全体生成 ------------------------------------------------------
def generate_part(*,outfile,width,height,phase,amp,wx,wy,
                  grid_layers,sw,sg,z_max,feed,cx,cy):
    gcode,e0=[],0.0
    # 格子底
    for l in range(grid_layers):
        z= FIRST_LAYER_H if l==0 else FIRST_LAYER_H+LAYER_HEIGHT*l
        lh=FIRST_LAYER_H if l==0 else LAYER_HEIGHT
        ori="x" if l%2==0 else "y"
        lay,e0=slit_layer(cx=cx,cy=cy,width=width,height=height,
                           z=z,feed=feed,e0=e0,sw=sw,sg=sg,
                           orient=ori,h=lh)
        gcode+=lay
    # 波形壁
    z=FIRST_LAYER_H+LAYER_HEIGHT*grid_layers; layer=1
    while z<=z_max+1e-6:
        wall,e0=wave_rect_layer(cx=cx,cy=cy,width=width,height=height,
                                z=z,layer_no=layer,feed=feed,e0=e0,
                                amp=amp,wx=wx,wy=wy,phase=phase)
        gcode+=wall; z+=LAYER_HEIGHT; layer+=1
    Path(outfile).write_text(start_gcode()+"\n".join(gcode)+end_gcode())
    print("✅  G-code written:",outfile)

# ── CLI -----------------------------------------------------------
def main():
    global FLOW_FACTOR,CORNER_FACTOR
    ap=argparse.ArgumentParser("格子底 + 波形長方形柱 G-code")
    ap.add_argument("-o","--outfile",default="part.gcode")
    ap.add_argument("--width",type=float,default=71.6)
    ap.add_argument("--height",type=float,default=147.6)
    ap.add_argument("--phase",type=float,default=0.0)
    ap.add_argument("--amp",type=float,default=2.5)
    ap.add_argument("--wavelength",type=float,default=0.0)
    ap.add_argument("--waves-x",type=int,default=4)
    ap.add_argument("--waves-y",type=int,default=8)
    ap.add_argument("--grid-layers",type=int,default=2)
    ap.add_argument("--slit-width",type=float,default=2.0)
    ap.add_argument("--slit-gap",type=float,default=2.0)
    ap.add_argument("--z-max",type=float,default=25.0)
    ap.add_argument("--flow-factor",type=float,default=1.0)
    ap.add_argument("--corner-factor",type=float,default=1.0)
    args,_=ap.parse_known_args()

    FLOW_FACTOR=args.flow_factor
    CORNER_FACTOR=max(0.05,min(args.corner_factor,1.0))

    wx,wy=(max(1,round(args.width/args.wavelength)),
           max(1,round(args.height/args.wavelength))) if args.wavelength>0 \
          else (args.waves_x,args.waves_y)

    generate_part(outfile=args.outfile,width=args.width,height=args.height,
                  phase=args.phase,amp=args.amp,wx=wx,wy=wy,
                  grid_layers=args.grid_layers,sw=args.slit_width,
                  sg=args.slit_gap,z_max=args.z_max,feed=1200,cx=150,cy=150)

if __name__=="__main__":
    main()
