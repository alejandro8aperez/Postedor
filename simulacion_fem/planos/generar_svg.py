"""
Genera SVG previews de los planos para la página web.
Correr después de generar_planos.py
"""
import math, os
import ezdxf
from ezdxf import units

OUT = r"C:\Postgres\Postedor\simulacion_fem\planos"
WEB_IMG = r"C:\Postgres\Postedor\website\images"

def dxf_to_svg_preview(dxf_path, svg_name, width=600, height=400):
    """Convierte un DXF a un SVG simple mostrando las entidades principales"""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    # Find bounding box
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    for e in msp:
        if e.dxftype() == 'LINE':
            for p in [e.dxf.start, e.dxf.end]:
                min_x = min(min_x, p[0]); min_y = min(min_y, p[1])
                max_x = max(max_x, p[0]); max_y = max(max_y, p[1])
        elif e.dxftype() == 'LWPOLYLINE':
            for v in e.vertices():
                min_x = min(min_x, v[0]); min_y = min(min_y, v[1])
                max_x = max(max_x, v[0]); max_y = max(max_y, v[1])
        elif e.dxftype() == 'CIRCLE':
            c = e.dxf.center; r = e.dxf.radius
            min_x = min(min_x, c[0]-r); min_y = min(min_y, c[1]-r)
            max_x = max(max_x, c[0]+r); max_y = max(max_y, c[1]+r)

    if min_x == float('inf'):
        min_x, min_y, max_x, max_y = 0, 0, 350, 350

    padding = 20
    bw = max_x - min_x + 2*padding
    bh = max_y - min_y + 2*padding
    scale = min(width/bw, height/bh, 2.0)
    cx, cy = width/2, height/2

    def tx(x,y):
        return (x - (min_x+max_x)/2)*scale + cx

    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="width:100%;height:auto;max-width:{width}px;background:#f8f9fa;border-radius:8px">'
    svg += f'<rect width="{width}" height="{height}" fill="#f8f9fa" rx="8"/>'

    for e in msp:
        try:
            color = e.dxf.color
        except:
            color = 7
        stroke = {1:'#ff0000',3:'#00aa00',7:'#000000',8:'#888888',10:'#ff0000',30:'#ff8800',40:'#cc6600',140:'#4488cc',252:'#555555'}.get(color,'#000000')
        lw = 1

        if e.dxftype() == 'LINE':
            x1,y1 = tx(e.dxf.start[0],e.dxf.start[1]), tx(e.dxf.start[0],e.dxf.start[1])
            x2,y2 = tx(e.dxf.end[0],e.dxf.end[1]), tx(e.dxf.end[0],e.dxf.end[1])
            svg += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{lw}"/>'
        elif e.dxftype() == 'CIRCLE':
            c = e.dxf.center
            xc,yc = tx(c[0],c[1])
            r = e.dxf.radius * scale
            svg += f'<circle cx="{xc:.1f}" cy="{yc:.1f}" r="{r:.1f}" fill="none" stroke="{stroke}" stroke-width="{lw}"/>'
        elif e.dxftype() == 'LWPOLYLINE':
            pts = [(tx(v[0],v[1]), tx(v[0],v[1])) for v in e.vertices()]
            if len(pts) > 1:
                d = ' '.join(f'M{x:.1f},{y:.1f}' if i==0 else f'L{x:.1f},{y:.1f}' for i,(x,y) in enumerate(pts))
                if e.closed:
                    d += ' Z'
                svg += f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{lw}"/>'

    svg += '</svg>'
    return svg

def make_svg(name, title, svg_content):
    path = os.path.join(WEB_IMG, name)
    with open(path, 'w') as f:
        f.write(svg_content)
    print(f"  {path}  ({len(svg_content)} bytes)")

if __name__ == "__main__":
    os.makedirs(WEB_IMG, exist_ok=True)
    print("Generando SVG previews...")
    dxfs = [
        ("plano_01_planta.dxf", "plano-planta.svg"),
        ("plano_02_lateral.dxf", "plano-lateral.svg"),
        ("plano_03_spider.dxf", "plano-spider.svg"),
        ("plano_04_termico.dxf", "plano-termico.svg"),
    ]
    for dxf, svg in dxfs:
        dxf_path = os.path.join(OUT, dxf)
        if os.path.exists(dxf_path):
            svg_content = dxf_to_svg_preview(dxf_path, svg)
            make_svg(svg, dxf.replace(".dxf", ""), svg_content)
    print("Listo.")
