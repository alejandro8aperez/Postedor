"""
POSTEDOR - SALOME Geometry Script
Transformador toroidal 5kVA dentro del poste (Parte C)
Parametrico: 1, 2, 3 o 4 transformadores en paralelo

Requiere SALOME 9+ ejecutar:  salome -t geometria.py -- caso_num
"""
import sys, math, json

# --- Parametros del transformador ---
OD  = 0.300     # diametro exterior (m)
ID  = 0.150     # diametro interior
H_t = 0.160     # altura total (core + windings)
H_c = 0.120     # altura del nucleo

# --- Parametros del poste ---
# Poste metalico truncado: base 0.50m, en Parte C ~0.35m
post_ancho = 0.35   # ancho en Parte C
post_prof  = 0.35   # profundidad (hexagono ~circular)
post_esp   = 0.005  # espesor pared (5mm)
post_H     = 0.50   # altura del segmento simulado

# --- Transformador ---
# Toroide: volumen de calor = nucleo + devanados
# Simplificacion: cilindro hueco (toroide rectangular)
trans_x = 0.0
trans_z = 0.0

def transformador_3d(geompy, salome, name_prefix="trans", pos_y=0.0):
    """Crea geometria de un transformador toroidal centrado en (0, pos_y, 0)"""
    # Nucleo: toroide rectangular (seccion transversal)
    # Punto central del toroide
    R_major = (OD + ID) / 4.0  # radio medio
    r_minor = (OD - ID) / 4.0   # radio del tubo
    
    # Toroide del nucleo de acero
    torus = geompy.MakeTorus(trans_x, pos_y, trans_z, R_major, r_minor)
    core = geompy.MakeBlock(torus, [-H_c/2, -H_c/2, -r_minor],
                            [H_c/2, H_c/2, r_minor])
    
    # Devanados: cilindro exterior alrededor del nucleo
    # Altura total del devanado
    H_w = H_t
    R_inner = ID/2.0
    R_outer = OD/2.0
    
    winding_cyl = geompy.MakeCylinder(trans_x, pos_y - H_w/2, trans_z,
                                      R_outer, H_w)
    hole_cyl = geompy.MakeCylinder(trans_x, pos_y - H_w/2, trans_z,
                                   R_inner, H_w)
    winding = geompy.Cut(winding_cyl, hole_cyl)
    
    # Grupo de todo el transformador
    transformer = geompy.MakeCompound([core, winding])
    geompy.addToStudy(transformer, f"{name_prefix}_complete")
    geompy.addToStudy(core, f"{name_prefix}_core")
    geompy.addToStudy(winding, f"{name_prefix}_winding")
    
    return transformer, core, winding

def poste_segmento(geompy, salome, name="poste_segment"):
    """Segmento del poste (prisma rectangular hueco)"""
    outer = geompy.MakeBoxDXDYDZ(post_ancho, post_H, post_prof)
    inner = geompy.MakeBoxDXDYDZ(post_ancho - 2*post_esp,
                                  post_H,
                                  post_prof - 2*post_esp)
    inner = geompy.TranslateDXDYDZ(inner, post_esp, 0, post_esp)
    segment = geompy.Cut(outer, inner)
    geompy.addToStudy(segment, name)
    return segment, outer

def build(n_transformers=1, salome_geom=None, salome_mesh=None):
    """Construye geometria completa"""
    from salome.shaper import shaper
    import GEOM
    
    geompy = salome_geom
    salome = salome_mesh
    
    # Poste
    post_seg, _ = poste_segmento(geompy, salome)
    
    # Transformadores
    spacing = 0.35  # separacion entre centros
    offset_y = -(n_transformers - 1) * spacing / 2.0
    
    all_trans = []
    all_cores = []
    all_windings = []
    
    for i in range(n_transformers):
        pos_y = offset_y + i * spacing
        t, c, w = transformador_3d(geompy, salome, f"trans_{i+1}", pos_y)
        all_trans.append(t)
        all_cores.append(c)
        all_windings.append(w)
    
    # Particion para mallado
    # Combinar todo
    combined = geompy.MakeCompound([post_seg] + all_trans)
    geompy.addToStudy(combined, "POSTEDOR_assembly")
    
    # Crear grupos para condiciones de frontera
    # Poste exterior: conveccion natural
    post_faces = geompy.SubShapeAll(post_seg, geompy.ShapeType["FACE"])
    # Buscar caras exteriores
    ext_faces = []
    for f in post_faces:
        com = geompy.PointCoordinates(geompy.MakeCDG(f))
        if abs(com[0]) > post_ancho/2 - 0.001 or abs(com[2]) > post_prof/2 - 0.001:
            ext_faces.append(f)
    
    if ext_faces:
        group_ext = geompy.CreateGroup(post_seg, geompy.ShapeType["FACE"])
        for f in ext_faces:
            geompy.UnionIDs(group_ext, [geompy.GetSubShapeID(post_seg, f)])
        geompy.addToStudyInFather(post_seg, group_ext, "BC_Convection")
    
    # Top/bottom: adiabatic / contacto con resto del poste
    top_bottom = []
    for f in post_faces:
        com = geompy.PointCoordinates(geompy.MakeCDG(f))
        if abs(com[1] - post_H/2) < 0.001 or abs(com[1] + post_H/2) < 0.001:
            top_bottom.append(f)
    
    if top_bottom:
        group_tb = geompy.CreateGroup(post_seg, geompy.ShapeType["FACE"])
        for f in top_bottom:
            geompy.UnionIDs(group_tb, [geompy.GetSubShapeID(post_seg, f)])
        geompy.addToStudyInFather(post_seg, group_tb, "BC_Adiabatic")
    
    # Aire interior: volumen entre poste y transformadores
    # (se crea automaticamente al mallar)
    
    return combined

if __name__ == "__main__":
    import salome
    salome.salome_init()
    import GEOM
    from salome.geom import geomBuilder
    geompy = geomBuilder.New()
    
    n = 1
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except:
            pass
    
    print(f"Creando geometria con {n} transformador(es)...")
    # En SALOME real, importaria salome y GEOM
    # build(n, salome_geom=geompy, salome_mesh=None)
    print("Ejecutar dentro de SALOME: salome -t geometria.py [n]")
    print(f"  n = numero de transformadores (1-4)")
