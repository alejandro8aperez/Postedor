# -*- coding: utf-8 -*-
import math, json, sys

S      = 5000.0   # VA
V1     = 13200.0  # V
V2     = 240.0    # V
f      = 60.0     # Hz
B_op   = 1.4      # T
rho_al = 2.82e-8  # ohm.m Al 20C
J      = 2.5e6    # A/m2

OD = 0.300   # m
ID = 0.150   # m
Hc = 0.120   # m

Ac = ((OD - ID) / 2.0) * Hc
Aw = math.pi * (ID/2.0)**2.0

V_core = math.pi * Hc * ((OD/2.0)**2.0 - (ID/2.0)**2.0)
m_core = V_core * 7650.0

N1 = round(V1 / (4.44 * f * B_op * Ac))
N2 = round(V2 / (4.44 * f * B_op * Ac))

I1 = S / V1
I2 = S / V2

A1 = I1 / J
A2 = I2 / J
d1 = math.sqrt(4.0*A1/math.pi)*1000.0
d2 = math.sqrt(4.0*A2/math.pi)*1000.0

MTL = math.pi * (OD + ID) / 2.0
R1 = rho_al * N1 * MTL / A1
R2 = rho_al * N2 * MTL / A2

P_cu = I1**2.0 * R1 + I2**2.0 * R2

loss_per_kg = 1.2
P_fe = m_core * loss_per_kg

P_total = P_cu + P_fe
eff = S / (S + P_total) * 100.0

loss_density_cu_Wm3 = P_cu / V_core
loss_density_fe_Wm3 = P_fe / V_core
loss_density_total_Wm3 = P_total / V_core

print("="*70)
print("DISE#O TRANSFORMADOR TOROIDAL 5 kVA - POSTEDOR")
print("="*70)
print(f"  Nucleo: OD={OD*1000:.0f}mm  ID={ID*1000:.0f}mm  H={Hc*1000:.0f}mm")
print(f"  Ac={Ac*1e4:.2f} cm2   Aw={Aw*1e4:.2f} cm2")
print(f"  Producto area: {Ac*Aw*1e4:.1f} cm4")
print(f"  Volumen nucleo: {V_core*1e6:.0f} cm3  Masa: {m_core:.1f} kg")
print()
print(f"  N1 = {N1} vueltas   I1 = {I1:.3f} A   Cond: {A1*1e6:.3f} mm2  d={d1:.2f} mm")
print(f"  N2 = {N2} vueltas   I2 = {I2:.2f} A   Cond: {A2*1e6:.2f} mm2  d={d2:.2f} mm")
print(f"  Longitud media espira: {MTL*1000:.0f} mm")
print(f"  R1 (20C) = {R1:.1f} ohm   R2 (20C) = {R2*1000:.1f} mohm")
print()
print(f"  Perdidas Cu: P1={I1**2*R1:.1f}W  P2={I2**2*R2:.1f}W  Total Cu={P_cu:.1f}W")
print(f"  Perdidas Fe (M4 @ 1.4T): {P_fe:.1f} W")
print(f"  Perdidas totales: {P_total:.1f} W  Eficiencia: {eff:.1f}%")
print()
print(f"  Densidad perdidas Cu: {loss_density_cu_Wm3/1e3:.1f} kW/m3")
print(f"  Densidad perdidas Fe: {loss_density_fe_Wm3/1e3:.1f} kW/m3")
print(f"  Densidad perdidas total: {loss_density_total_Wm3/1e3:.1f} kW/m3")

# 4 configuraciones
configs = {
    1: {"n": 1, "S_kVA": 5,  "P_cu_W": round(P_cu,1),      "P_fe_W": round(P_fe,1),      "P_total_W": round(P_total,1)},
    2: {"n": 2, "S_kVA": 10, "P_cu_W": round(2*P_cu,1),    "P_fe_W": round(2*P_fe,1),    "P_total_W": round(2*P_total,1)},
    3: {"n": 3, "S_kVA": 15, "P_cu_W": round(3*P_cu,1),    "P_fe_W": round(3*P_fe,1),    "P_total_W": round(3*P_total,1)},
    4: {"n": 4, "S_kVA": 20, "P_cu_W": round(4*P_cu,1),    "P_fe_W": round(4*P_fe,1),    "P_total_W": round(4*P_total,1)},
}

print()
print("="*70)
print("CONFIGURACIONES EN PARALELO")
print("="*70)
for k, v in configs.items():
    print(f"  Caso {k}: {v['n']} transf x 5 kVA = {v['S_kVA']:>2} kVA  |"
          f"  Cu={v['P_cu_W']:.0f}W  Fe={v['P_fe_W']:.0f}W  Total={v['P_total_W']:.0f}W")

data = {
    "OD_m": OD, "ID_m": ID, "Hc_m": Hc,
    "Ac_m2": Ac, "Aw_m2": Aw, "V_core_m3": V_core,
    "N1": N1, "N2": N2,
    "R1_ohm": R1, "R2_ohm": R2,
    "P_cu_W": round(P_cu,1), "P_fe_W": round(P_fe,1), "P_total_W": round(P_total,1),
    "loss_density_cu_kWm3": round(loss_density_cu_Wm3/1e3,2),
    "loss_density_fe_kWm3": round(loss_density_fe_Wm3/1e3,2),
    "loss_density_total_kWm3": round(loss_density_total_Wm3/1e3,2),
}
with open("design_params.json", "w") as f:
    json.dump(data, f, indent=2)

with open("configs.json", "w") as f:
    json.dump(configs, f, indent=2)
print(f"\nArchivos guardados: design_params.json, configs.json")
