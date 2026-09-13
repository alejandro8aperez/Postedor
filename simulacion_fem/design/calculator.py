# -*- coding: utf-8 -*-
"""
POSTEDOR — Diseño transformador toroidal MONOFÁSICO 7 kVA base
V1 = 7620 V (MT)  |  V2 = 240/120 V (con tap central)
4 toroidales IDÉNTICOS en paralelo -> modelos 7/14/21/28 kVA
Montaje HORIZONTAL -> ancho del poste = OD + holgura de montaje
"""
import math, json, sys

# ---------- Entrada ----------
S      = 7000.0   # VA (base)
V1     = 7620.0   # V primario (MT)
V2     = 240.0    # V secundario (referido; 240 V con tap central 120 V)
f      = 60.0     # Hz
B_op   = 1.4      # T (M4 grano orientado @60Hz)
J      = 2.5e6    # A/m2 corriente admisible
rho_cu = 1.72e-8  # ohm.m cobre a 20C
Ku     = 0.30     # factor de llenado ventana (bobinado + Nomex) - margen
p_core = 7650.0   # kg/m3 densidad núcleo acero silicio
loss_per_kg = 1.2 # W/kg @1.4T 60Hz

# ---------- Área producto (derivación) ----------
# Ley de Faraday: N = V/(4.44 f B Ac)
# Amperios-vuelta: N1·I1 + N2·I2 = J·Aw·Ku
#   N1·I1 = N2·I2 = S/(4.44 f B Ac)
# => 2·S/(4.44 f B Ac) = J·Aw·Ku
# => Ap = Ac·Aw = 2·S / (4.44·f·B·J·Ku)
Ap = 2.0 * S / (4.44 * f * B_op * J * Ku)

# ---------- Geometría toroidal ----------
# Proporciones estándar toroidal: r = ID/OD (0.45..0.65), c = Hc/OD
# Ac = ((OD-ID)/2)·Hc = (OD(1-r)/2)·(c·OD)
# Aw = π/4 · ID² = π/4 · r²·OD²
# Ap = (π/8)·r²·(1-r)·c·OD⁴
def solve_od(r, c):
    return (Ap / ((math.pi/8) * r*r * c * (1-r))) ** 0.25

# OD FIJADO por decisión de diseño: tamaño final tras estudio térmico FEM
# (OD=208 -> T~172°C Clase H sin margen; OD=260 -> ~100-125°C en Clase F).
# Con OD fijo la ventana queda holgada (fill<<1) => núcleo sobredimensionado
# a propósito: más superficie de disipación, transformador más frío.
OD_TARGET = 0.260   # m  (OD elegido)
r = 0.55
c = 0.50
OD = OD_TARGET
ID = r * OD
Hc = c * OD
W  = (OD - ID) / 2.0     # ancho del anillo

Ac = W * Hc
Aw = math.pi/4 * ID*ID
V_core = math.pi * Hc * ((OD/2)**2 - (ID/2)**2)
m_core = V_core * p_core

# ---------- Espiras ----------
N1 = round(V1 / (4.44 * f * B_op * Ac))
N2 = round(V2 / (4.44 * f * B_op * Ac))
N2_120 = N2 // 2  # tap central 120 V

# ---------- Corrientes ----------
I1 = S / V1
I2 = S / V2

A1 = I1 / J
A2 = I2 / J
d1 = math.sqrt(4*A1/math.pi)*1000.0
d2 = math.sqrt(4*A2/math.pi)*1000.0

# ---------- Longitud media de espira y resistencias ----------
MTL = math.pi * (OD + ID) / 2.0
R1 = rho_cu * N1 * MTL / A1
R2 = rho_cu * N2 * MTL / A2

P_cu = I1**2 * R1 + I2**2 * R2
P_fe = m_core * loss_per_kg
P_total = P_cu + P_fe
eff = S / (S + P_total) * 100.0

loss_density_cu_Wm3  = P_cu  / V_core
loss_density_fe_Wm3  = P_fe  / V_core
loss_density_total   = P_total / V_core

# ---------- Llenado de ventana (verificación) ----------
sec_cu_area = N1*A1 + N2*A2
fill = sec_cu_area / (Aw * Ku)  # <1 => cabe holgado

# ---------- Salida ----------
print("="*70)
print(f"DISEÑO TRANSFORMADOR TOROIDAL {S/1000:.0f} kVA - POSTEDOR")
print(f"  V1 = {V1:.0f} V (MT)   V2 = {V2:.0f}/120 V (tap central)   f = {f:.0f} Hz")
print("="*70)
print(f"  Área producto requerida Ap = {Ap*1e4:.1f} cm4   (B={B_op} T, J={J/1e6:.1f} A/mm2, Ku={Ku})")
print()
print(f"  OD = {OD*1000:.0f} mm   ID = {ID*1000:.0f} mm   Hc = {Hc*1000:.0f} mm   anillo W = {W*1000:.0f} mm")
print(f"  Ac = {Ac*1e4:.1f} cm2    Aw = {Aw*1e4:.1f} cm2")
print(f"  V_core = {V_core*1e6:.0f} cm3    Masa = {m_core:.1f} kg")
print()
print(f"  N1 = {N1} espiras   I1 = {I1:.3f} A   cond {A1*1e6:.2f} mm2  d={d1:.2f} mm")
print(f"  N2 = {N2} espiras   (tap 120V = {N2_120})  I2 = {I2:.2f} A   cond {A2*1e6:.1f} mm2  d={d2:.2f} mm")
print(f"  MTL = {MTL*1000:.0f} mm   R1 = {R1:.1f} ohm   R2 = {R2*1000:.1f} mohm")
print(f"  Llenado ventana: {fill*100:.0f}% de la ventana útil  {'OK' if fill<=1 else 'REVISAR'}")
print()
print(f"  P_cu = {P_cu:.1f} W   P_fe = {P_fe:.1f} W   P_total = {P_total:.1f} W")
print(f"  Eficiencia = {eff:.2f}%")
print()
print(f"  Densidad pésima volumétrica = {loss_density_total/1e3:.1f} kW/m3")
print()
print("="*70)
print("CONFIGURACIONES EN PARALELO (toroidales IDÉNTICOS)")
print("="*70)
configs = {}
for k, n in [(1,1),(2,2),(3,3),(4,4)]:
    cfg = {"n": n, "S_kVA": round(n*S/1000.0, 1),
           "P_cu_W": round(n*P_cu,1), "P_fe_W": round(n*P_fe,1),
           "P_total_W": round(n*P_total,1)}
    configs[str(k)] = cfg
    print(f"  Modelo {n*S/1000:>2.0f} kVA: {n} x {S/1000:.0f} kVA |"
          f"  Cu={cfg['P_cu_W']:.0f}W  Fe={cfg['P_fe_W']:.0f}W  Total={cfg['P_total_W']:.0f}W")

# ---------- Ancho del poste (montaje horizontal) ----------
# Toroidal acostado: diámetro exterior define el ancho interior útil.
# + 2 x clearance montaje/fijación LV + espesor pared.
clear  = 0.035       # m holgura montaje/aislamiento por lado
wall   = 0.005       # m espesor pared metálica
post_inner_w = OD + 2*clear
post_outer_w = post_inner_w + 2*wall
print()
print("="*70)
print("MONTAJE HORIZONTAL — ANCHO DEL POSTE")
print("="*70)
print(f"  OD toroidal       = {OD*1000:.0f} mm")
print(f"  + 2×holgura montaje = {2*clear*1000:.0f} mm")
print(f"  Ancho interior     = {post_inner_w*1000:.0f} mm")
print(f"  + 2×pared          = {2*wall*1000:.0f} mm")
print(f"  ANCHO EXTERNO POSTE = {post_outer_w*1000:.0f} mm")
print(f"  Sección hexagonal inscrita = {post_outer_w*1000:.0f} mm (diámetro circunscrito)")
print(f"  Altura pila 4 toroidales: 4x({Hc*1000:.0f} mm) + 3x40 mm gap + soportes = "
      f"{int(4*Hc*1000 + 3*40 + 100)} mm")

# ---------- Guardar JSON ----------
data = {
    "S_kVA": round(S/1000,1), "V1_V": V1, "V2_V": V2, "f_Hz": f, "B_T": B_op,
    "J_A_m2": round(J,0),
    "OD_m": round(OD,5), "ID_m": round(ID,5), "Hc_m": round(Hc,5), "W_m": round(W,5),
    "Ac_m2": round(Ac,6), "Aw_m2": round(Aw,6), "V_core_m3": round(V_core,7),
    "N1": N1, "N2": N2, "N2_120": N2_120,
    "I1_A": round(I1,3), "I2_A": round(I2,2),
    "R1_ohm": round(R1,2), "R2_ohm": round(R2,5),
    "P_cu_W": round(P_cu,1), "P_fe_W": round(P_fe,1), "P_total_W": round(P_total,1),
    "loss_density_total_kWm3": round(loss_density_total/1e3,2),
    "Ap_cm4": round(Ap*1e4,1), "fill_ventana": round(fill,3),
    "post_inner_mm": round(post_inner_w*1000,1), "post_outer_mm": round(post_outer_w*1000,1),
}
with open("design_params.json", "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
with open("configs.json", "w") as f:
    json.dump(configs, f, indent=2, ensure_ascii=False)
print("\nArchivos guardados: design_params.json, configs.json")