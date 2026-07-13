"""
Genera planos DXF del transformador toroidal 5kVA dentro del poste Postedor
para abrir en NanoCAD.
Planos: 1-planta 2-lateral 3-spider 4-termico
"""
import math, os
import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment

POST_OD = 350
WALL_T = 5
POST_ID = POST_OD - 2 * WALL_T
TRANS_OD = 300
TRANS_ID = 150
TRANS_H = 160
GAP_Y = 40
MARGIN = 50

C_STEEL, C_AL, C_CORE, C_COPPER, C_DIM, C_TEXT, C_HOT, C_WARM, C_COOL = 252, 8, 140, 40, 3, 7, 10, 30, 140

OUT = r"C:\Postgres\Postedor\simulacion_fem\planos"

def dim(msp, p1, p2, offset=(0,-12), text=""):
    """Dibuja cota simple: línea de referencia + texto"""
    dx, dy = offset
    mid = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
    # Extension lines
    msp.add_line((p1[0]+dx, p1[1]+dy), p1, dxfattribs={"color": C_DIM})
    msp.add_line((p2[0]+dx, p2[1]+dy), p2, dxfattribs={"color": C_DIM})
    # Dimension line
    msp.add_line((p1[0]+dx, p1[1]+dy), (p2[0]+dx, p2[1]+dy), dxfattribs={"color": C_DIM})
    # Arrows
    msp.add_solid([(p1[0]+dx, p1[1]+dy), (p1[0]+dx-2, p1[1]+dy-1.5), (p1[0]+dx-2, p1[1]+dy+1.5)],
                  dxfattribs={"color": C_DIM})
    msp.add_solid([(p2[0]+dx, p2[1]+dy), (p2[0]+dx+2, p2[1]+dy-1.5), (p2[0]+dx+2, p2[1]+dy+1.5)],
                  dxfattribs={"color": C_DIM})
    # Text
    if not text:
        text = f"{abs(p2[0]-p1[0]):.0f}" if p1[0]!=p2[0] else f"{abs(p2[1]-p1[1]):.0f}"
    msp.add_text(text, height=2.5, dxfattribs={"color": C_DIM}).set_placement(
        (mid[0]+dx, mid[1]+dy-4), align=TextEntityAlignment.CENTER)

def dim_diameter(msp, cx, cy, d, text=""):
    """Cota de diámetro con línea guía"""
    r = d/2
    x1, y1 = cx + r, cy
    x2, y2 = cx + r + 8, cy
    msp.add_line((x1, y1), (x2, y2), dxfattribs={"color": C_DIM})
    msp.add_line((cx+r, cy), (cx+r*0.7, cy+r*0.7), dxfattribs={"color": C_DIM})
    if not text:
        text = f"⌀{d}"
    msp.add_text(text, height=2.5, dxfattribs={"color": C_DIM}).set_placement(
        (x2+2, y2-1.5), align=TextEntityAlignment.LEFT)

def label(msp, pos, text, h=3, color=C_TEXT, align="CENTER"):
    al = {"LEFT": TextEntityAlignment.LEFT, "CENTER": TextEntityAlignment.CENTER}.get(align, TextEntityAlignment.CENTER)
    msp.add_text(text, height=h, dxfattribs={"color": color}).set_placement(pos, align=al)

def make_plan():
    doc = ezdxf.new("R2010", units=units.MM)
    msp = doc.modelspace()
    cx = cy = POST_OD/2

    # Poste exterior
    msp.add_lwpolyline([(0,0),(POST_OD,0),(POST_OD,POST_OD),(0,POST_OD)], close=True,
                       dxfattribs={"color": C_STEEL, "lineweight": 50})
    # Poste interior
    msp.add_lwpolyline([(WALL_T,WALL_T),(POST_OD-WALL_T,WALL_T),(POST_OD-WALL_T,POST_OD-WALL_T),(WALL_T,POST_OD-WALL_T)],
                       close=True, dxfattribs={"color": C_STEEL, "lineweight": 25})

    # Hatch pared
    h = msp.add_hatch(color=C_STEEL)
    h.paths.add_polyline_path([(0,0),(POST_OD,0),(POST_OD,POST_OD),(0,POST_OD)], is_closed=True)
    h.paths.add_polyline_path([(WALL_T,WALL_T),(POST_OD-WALL_T,WALL_T),(POST_OD-WALL_T,POST_OD-WALL_T),(WALL_T,POST_OD-WALL_T)], is_closed=True)

    # Ejes simetría
    msp.add_line((cx,-15),(cx,POST_OD+15), dxfattribs={"color": 1, "linetype": "CENTER"})
    msp.add_line((-15,cy),(POST_OD+15,cy), dxfattribs={"color": 1, "linetype": "CENTER"})

    # Transformador
    msp.add_circle((cx,cy), TRANS_OD/2, dxfattribs={"color": C_CORE, "lineweight": 35})
    msp.add_circle((cx,cy), TRANS_ID/2, dxfattribs={"color": C_CORE, "lineweight": 35})
    msp.add_circle((cx,cy), 100, dxfattribs={"color": C_COPPER, "linetype": "DASHED"})
    msp.add_circle((cx,cy), 125, dxfattribs={"color": C_COPPER, "linetype": "DASHED"})

    # Spider 4 brazos
    for ang in [45, 135, 225, 315]:
        r = math.radians(ang)
        r1 = TRANS_OD/2 + 2
        r2 = POST_ID/2
        msp.add_line((cx+r1*math.cos(r), cy+r1*math.sin(r)),
                     (cx+r2*math.cos(r), cy+r2*math.sin(r)),
                     dxfattribs={"color": C_AL, "lineweight": 40})

    # Cotas manuales
    dim(msp, (0,0), (POST_OD,0), offset=(0,-20))
    dim(msp, (0,POST_OD/2), (WALL_T,POST_OD/2), offset=(POST_OD+10,0))
    dim_diameter(msp, cx, cy, TRANS_OD)
    dim_diameter(msp, cx, cy, TRANS_ID, "⌀150")

    label(msp, (POST_OD/2, POST_OD+20), "POSTE 350×350×5mm — ACERO GALVANIZADO", h=3)
    label(msp, (POST_OD/2, -35), "TRANSFORMADOR TOROIDAL 5kVA  OD=300  ID=150  H=160")
    label(msp, (cx+120, cy+120), "BRAZO SPIDER AL 6063 ×4", color=C_AL, h=2.5, align="LEFT")

    doc.saveas(os.path.join(OUT, "plano_01_planta.dxf"))
    print("  OK plano_01_planta.dxf")

def make_lateral():
    doc = ezdxf.new("R2010", units=units.MM)
    msp = doc.modelspace()
    n = 4
    th = 2*MARGIN + n*TRANS_H + (n-1)*GAP_Y
    pw = POST_OD/2

    # Paredes poste
    msp.add_line((0,0),(0,th), dxfattribs={"color": C_STEEL, "lineweight": 50})
    msp.add_line((WALL_T,0),(WALL_T,th), dxfattribs={"color": C_STEEL, "lineweight": 25})
    msp.add_line((pw,0),(pw,th), dxfattribs={"color": C_STEEL, "lineweight": 50})
    msp.add_line((pw-WALL_T,0),(pw-WALL_T,th), dxfattribs={"color": C_STEEL, "lineweight": 25})

    for hw in [((0,0),(WALL_T,0),(WALL_T,th),(0,th)),
               ((pw,0),(pw-WALL_T,0),(pw-WALL_T,th),(pw,th))]:
        ha = msp.add_hatch(color=C_STEEL)
        ha.paths.add_polyline_path(hw, is_closed=True)

    # Transformadores
    for t in range(n):
        yb = MARGIN + t*(TRANS_H+GAP_Y)
        yt = yb + TRANS_H
        xl, xr = WALL_T+2, pw-WALL_T-2
        msp.add_lwpolyline([(xl,yb),(xr,yb),(xr,yt),(xl,yt)], close=True,
                           dxfattribs={"color": C_CORE, "lineweight": 25})
        cw = 10
        msp.add_lwpolyline([((xl+xr)/2-cw,yb+5),((xl+xr)/2+cw,yb+5),
                            ((xl+xr)/2+cw,yt-5),((xl+xr)/2-cw,yt-5)], close=True,
                           dxfattribs={"color": 140, "lineweight": 15})
        msp.add_line((xl+5,yb+3),(xr-5,yb+3), dxfattribs={"color": C_COPPER})
        msp.add_line((xl+5,yt-3),(xr-5,yt-3), dxfattribs={"color": C_COPPER})
        # Spider
        ym = (yb+yt)/2
        msp.add_line((WALL_T,ym),(xl,ym), dxfattribs={"color": C_AL, "lineweight": 40})
        msp.add_line((pw-WALL_T,ym),(xr,ym), dxfattribs={"color": C_AL, "lineweight": 40})
        label(msp, ((xl+xr)/2, ym-3), "5kVA", h=6)

    label(msp, (pw+15, MARGIN/2), "MARGEN")
    label(msp, (pw+15, MARGIN+TRANS_H+GAP_Y/2), f"GAP {GAP_Y}")
    dim(msp, (0,0), (0,th), offset=(-20,0))
    dim(msp, (0,MARGIN), (0,MARGIN+TRANS_H), offset=(-20,0))
    label(msp, (pw/2, th+15), f"CORTE VERTICAL — 4×5kVA = 20kVA  Altura total {th}mm", h=3.5)

    doc.saveas(os.path.join(OUT, "plano_02_lateral.dxf"))
    print("  OK plano_02_lateral.dxf")

def make_spider():
    doc = ezdxf.new("R2010", units=units.MM)
    msp = doc.modelspace()
    al, ah = (POST_ID-TRANS_OD)/2, 50
    x0, y0 = 50, 100

    msp.add_lwpolyline([(x0,y0),(x0+al,y0),(x0+al,y0+ah),(x0,y0+ah)], close=True,
                       dxfattribs={"color": C_AL, "lineweight": 35})
    for yp in [y0+10, y0+ah-10]:
        msp.add_circle((x0+3,yp), 2, dxfattribs={"color": 7})
        msp.add_circle((x0+al-3,yp), 2, dxfattribs={"color": 7})
    msp.add_line((x0,y0),(x0-15,y0), dxfattribs={"color": C_AL, "lineweight": 25})
    msp.add_line((x0,y0+ah),(x0-15,y0+ah), dxfattribs={"color": C_AL, "lineweight": 25})
    msp.add_arc((x0-15,(y0+y0+ah)/2), radius=ah/2, start_angle=270, end_angle=90,
                dxfattribs={"color": C_AL, "lineweight": 25})
    msp.add_lwpolyline([(x0+al,y0-10),(x0+al+WALL_T+5,y0-10),(x0+al+WALL_T+5,y0+ah+10),(x0+al,y0+ah+10)],
                       close=True, dxfattribs={"color": C_STEEL, "lineweight": 30})
    dim(msp, (x0,y0), (x0+al,y0), offset=(0,-10))
    dim(msp, (x0,y0), (x0,y0+ah), offset=(-5,0))

    yn = y0-25
    label(msp, (x0+al/2, y0+ah+30), "BRAZO SPIDER — ALUMINIO 6063-T5", h=3.5)
    notes = [
        "• 4 brazos por transformador (a 90°)",
        "• Sección 20×5mm extruido",
        "• Tornillos M4×12 a pared poste",
        "• Abrazo mecánico al núcleo",
        "• k=200 W/mK  |  ΔT ≈ 2°C",
    ]
    for i,n in enumerate(notes):
        label(msp, (x0, yn-(i+1)*7), n, h=2.5, align="LEFT")

    doc.saveas(os.path.join(OUT, "plano_03_spider.dxf"))
    print("  OK plano_03_spider.dxf")

def make_termico():
    doc = ezdxf.new("R2010", units=units.MM)
    msp = doc.modelspace()
    cx = cy = POST_OD/2

    msp.add_lwpolyline([(0,0),(POST_OD,0),(POST_OD,POST_OD),(0,POST_OD)], close=True,
                       dxfattribs={"color": C_STEEL, "lineweight": 50})
    msp.add_lwpolyline([(WALL_T,WALL_T),(POST_OD-WALL_T,WALL_T),(POST_OD-WALL_T,POST_OD-WALL_T),(WALL_T,POST_OD-WALL_T)],
                       close=True, dxfattribs={"color": C_STEEL, "lineweight": 25})

    # Isotermas
    msp.add_circle((cx,cy), 50, dxfattribs={"color": C_HOT, "lineweight": 20})
    label(msp, (cx,cy), "124°C", color=C_HOT)
    msp.add_circle((cx,cy), 100, dxfattribs={"color": C_WARM, "lineweight": 20})
    label(msp, (cx+10,cy+75), "120°C", color=C_WARM, align="LEFT")
    msp.add_circle((cx,cy), TRANS_OD/2, dxfattribs={"color": C_COPPER, "lineweight": 35})
    label(msp, (cx+110,cy+110), "118°C", color=C_COPPER, align="LEFT")
    msp.add_circle((cx,cy), TRANS_ID/2, dxfattribs={"color": C_CORE, "lineweight": 25, "linetype": "DASHED"})
    label(msp, (WALL_T+3,cy), "115°C", color=C_WARM, align="LEFT")
    label(msp, (POST_OD+8,cy), "30°C", color=C_COOL, align="LEFT")

    # Flechas flujo calor
    for (x1,y1,x2,y2) in [(cx-155,cy,WALL_T+5,cy), (cx+155,cy,POST_OD-WALL_T-5,cy),
                           (cx,cy-155,cx,WALL_T+5), (cx,cy+155,cx,POST_OD-WALL_T-5)]:
        msp.add_line((x1,y1),(x2,y2), dxfattribs={"color": C_HOT, "lineweight": 15})
        ang = math.atan2(y2-y1,x2-x1)
        for s in [-1,1]:
            msp.add_line((x2,y2), (x2-5*math.cos(ang+s*0.5), y2-5*math.sin(ang+s*0.5)),
                        dxfattribs={"color": C_HOT, "lineweight": 15})

    # Leyenda
    ly = 20
    for col,txt in [(C_HOT,"124°C — Núcleo (máx)"),(C_WARM,"118-120°C — Devanados"),
                    (C_COPPER,"115°C — Gap/pared"),(C_STEEL,"Pared poste acero"),
                    (C_COOL,"30°C — Ambiente exterior")]:
        msp.add_line((POST_OD+50,ly),(POST_OD+60,ly), dxfattribs={"color": col, "lineweight": 30})
        label(msp, (POST_OD+65,ly), txt, h=2.5, align="LEFT"); ly += 7

    label(msp, (POST_OD/2,-12), "MAPA TÉRMICO — 20kVA (4×5kVA) — Flujo calor → pared → ambiente", h=3)
    doc.saveas(os.path.join(OUT, "plano_04_termico.dxf"))
    print("  OK plano_04_termico.dxf")

if __name__ == "__main__":
    print("Generando planos DXF para NanoCAD...")
    make_plan()
    make_lateral()
    make_spider()
    make_termico()
    print(f"\nListo. Archivos en: {OUT}")
