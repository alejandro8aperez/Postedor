# POSTEDOR — Simulación FEM Transformador Toroidal 5 kVA

## Objetivo
Simular el comportamiento electromagnético y térmico del transformador toroidal de 5 kVA
con devanados de aluminio, instalado dentro del poste metálico (Parte C), para 4 configuraciones:

| Caso | Configuración | Potencia Total |
|------|--------------|----------------|
| 1    | 1 transformador | 5 kVA |
| 2    | 2 en paralelo | 10 kVA |
| 3    | 3 en paralelo | 15 kVA |
| 4    | 4 en paralelo | 20 kVA |

## Requisitos
- **SALOME 9+** (geometría y mallado 3D)
- **Elmer FEM 9.0+** (solvers electromagnético y térmico)
- Python 3.8+

## Estructura
```
simulacion_fem/
├── README.md
├── design/                  # Cálculos eléctricos del transformador
├── salome/                  # Scripts Python para SALOME
│   ├── geometria.py         # Geometría paramétrica 3D
│   └── mallado.py           # Mallado hexaédrico
├── elmer/
│   ├── case_template/       # Plantillas SIF
│   ├── caso_1_solo/         # 1 transformador
│   ├── caso_2_paralelo2/    # 2 en paralelo
│   ├── caso_3_paralelo3/    # 3 en paralelo
│   └── caso_4_paralelo4/    # 4 en paralelo
└── resultados/              # Resultados y gráficas
```

## Flujo de trabajo
1. Ejecutar `salome geometria.py` para generar geometría 3D
2. Ejecutar `salome mallado.py` para mallar
3. Exportar malla a formato Elmer (.unv o .msh)
4. Ejecutar `ElmerSolver case.sif` para cada caso
5. Post-procesar en resultados/

## Materiales
| Componente | Material | ρ (kg/m³) | k (W/m·K) | σ (S/m) |
|-----------|----------|-----------|-----------|---------|
| Núcleo toroidal | Acero silicio M4 | 7650 | 20 | 2×10⁶ |
| Devanados | Aluminio | 2700 | 237 | 3.5×10⁷ |
| Aislamiento | Clase B (poliéster) | 1400 | 0.2 | 0 |
| Poste | Acero galvanizado | 7850 | 50 | 6×10⁶ |
| Aire interior | Aire seco | 1.2 | 0.026 | 0 |
