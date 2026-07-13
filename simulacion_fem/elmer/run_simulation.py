#!/usr/bin/env python3
"""
POSTEDOR — Thermal FEM simulation of 5kVA toroidal transformer inside post
Creates Elmer mesh files and SIF, runs ElmerSolver
4 cases: 1, 2, 3, 4 transformers in parallel
"""
import os, sys, json, shutil, subprocess

ELMER_BIN = r"C:\Program Files\Elmer 9.0-Release\bin"
os.environ["PATH"] = ELMER_BIN + ";" + os.environ.get("PATH", "")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
DESIGN = os.path.join(ROOT, "design")

with open(os.path.join(DESIGN, "configs.json")) as f:
    CONFIGS = json.load(f)

# --- Geometry parameters (1/4 symmetry) ---
WALL_T = 0.005     # post wall thickness (m)
BOX_W = 0.175      # half-width of post = 0.350/2 (symmetry)
BOX_D = 0.175      # half-depth
TRANS_OD = 0.150   # transformer outer radius
TRANS_ID = 0.075   # transformer inner radius
TRANS_H = 0.160    # transformer total height (core 0.12 + winding overhang)
TRANS_H_CORE = 0.120  # core height only (for volume calc)
GAP_Y = 0.040      # gap between transformers
MARGIN = 0.050     # margin above/below

HEAT_CAPACITY = 32.6e3  # W/m3 per transformer (from calculator)

# --- Post section ---
# Wall in X: x=0..BOX_INNER is air, x=BOX_INNER..BOX_W is steel
# Wall in Z: same
BOX_INNER = BOX_W - WALL_T

# --- Mesh divisions ---
NX_AIR = 6
NX_WALL = 2
NY_PER_TRANS = 8
NY_GAP = 3
NY_MARGIN = 3

def get_x_coords():
    """Returns X coordinates from 0 to BOX_W"""
    xs = []
    for i in range(NX_AIR + 1):
        xs.append(BOX_INNER * i / NX_AIR)
    for i in range(1, NX_WALL + 1):
        xs.append(BOX_INNER + WALL_T * i / NX_WALL)
    return xs

def get_y_coords(n_trans):
    """Returns Y coordinates with transformers placed"""
    ys = [0.0]
    # bottom margin
    for i in range(1, NY_MARGIN + 1):
        ys.append(MARGIN * i / NY_MARGIN)
    # transformers with gaps
    for t in range(n_trans):
        for i in range(1, NY_PER_TRANS + 1):
            ys.append(ys[-1] + TRANS_H / NY_PER_TRANS)
        if t < n_trans - 1:
            for i in range(1, NY_GAP + 1):
                ys.append(ys[-1] + GAP_Y / NY_GAP)
    # top margin
    top_y = n_trans * TRANS_H + (n_trans - 1) * GAP_Y + 2 * MARGIN
    total_h = top_y
    for i in range(1, NY_MARGIN + 1):
        ys.append(MARGIN + n_trans * TRANS_H + (n_trans - 1) * GAP_Y + MARGIN * i / NY_MARGIN)
    return [round(y, 6) for y in ys], total_h

def create_mesh(case_dir, n_trans, use_spider=False):
    """Create Elmer mesh files"""
    xs = get_x_coords()
    zs = xs  # same profile in Z (1/4 symmetry)
    ys, total_h = get_y_coords(n_trans)
    nx, ny, nz = len(xs), len(ys), len(zs)

    assert ny > 1, "Need at least 2 y-coords"

    # --- mesh.header ---
    nelem = (nx - 1) * (ny - 1) * (nz - 1)
    nbound = 0
    # Count boundary faces
    nbound += (nx - 1) * (ny - 1)  # z=0
    nbound += (nx - 1) * (ny - 1)  # z=nz-1
    nbound += (nz - 1) * (ny - 1)  # x=0
    nbound += (nz - 1) * (ny - 1)  # x=nx-1
    nbound += (nz - 1) * (nx - 1)  # y=0
    nbound += (nz - 1) * (nx - 1)  # y=ny-1
    # But some faces are interior (contact between different materials)
    # For simplicity, all exterior faces are counted

    nnodes = nx * ny * nz

    with open(os.path.join(case_dir, "mesh.header"), "w") as f:
        f.write(f"{nnodes} {nelem} {nbound}\n")
        f.write("1\n")
        f.write("808 808\n")
        # Actually the format per the example has multiple types
        # Let me use the format from the cube example

    # Actually, looking at the cube example header more carefully:
    # Line 1: nnodes nelem nboundary
    # Line 2: num_element_types (2 if both bulk and boundary types differ)
    # Line 3+: type_id count
    # 
    # In the cube example: type 404 (boundary quad) count 96, type 808 (hex) count 64

    # For my mesh, all volume elements are hex 808, boundary are quad 404
    # Let me use the same format

    with open(os.path.join(case_dir, "mesh.header"), "w") as f:
        f.write(f"{nnodes} {nelem} {nbound}\n")
        f.write("2\n")
        f.write(f"404 {nbound}\n")
        f.write(f"808 {nelem}\n")

    # --- mesh.nodes ---
    with open(os.path.join(case_dir, "mesh.nodes"), "w") as f:
        nid = 0
        for iy in range(ny):
            for iz in range(nz):
                for ix in range(nx):
                    nid += 1
                    f.write(f"{nid} -1 {xs[ix]:.6f} {ys[iy]:.6f} {zs[iz]:.6f}\n")

    # --- mesh.elements ---
    # Determine if element is in transformer toroid
    def in_transformer_toroid(x, z, y, n_trans):
        r2 = x*x + z*z
        in_annulus = (TRANS_ID**2 <= r2) and (r2 <= TRANS_OD**2)
        if not in_annulus:
            return False
        margin = MARGIN
        for t in range(n_trans):
            y_start = margin + t * (TRANS_H + GAP_Y)
            y_end = y_start + TRANS_H
            if y_start <= y <= y_end:
                return True
        return False

    # Determine if element is in the spider bridge zone (gap between trans OD and wall)
    def in_spider_zone(x, z, y, n_trans):
        r2 = x*x + z*z
        # Annular region between TRANS_OD and BOX_INNER
        in_gap = (TRANS_OD**2 < r2) and (r2 <= BOX_INNER**2)
        if not in_gap:
            return False
        # Same y-range as transformer
        margin = MARGIN
        for t in range(n_trans):
            y_start = margin + t * (TRANS_H + GAP_Y)
            y_end = y_start + TRANS_H
            if y_start <= y <= y_end:
                return True
        return False

    with open(os.path.join(case_dir, "mesh.elements"), "w") as f:
        eid = 0
        for iy in range(ny - 1):
            y_mid = (ys[iy] + ys[iy + 1]) / 2.0
            for iz in range(nz - 1):
                z_mid = (zs[iz] + zs[iz + 1]) / 2.0
                for ix in range(nx - 1):
                    x_mid = (xs[ix] + xs[ix + 1]) / 2.0
                    eid += 1

                    # Determine body
                    is_wall = (x_mid >= BOX_INNER - 1e-10) or (z_mid >= BOX_INNER - 1e-10)
                    if is_wall:
                        body = 2  # steel wall
                    elif in_transformer_toroid(x_mid, z_mid, y_mid, n_trans):
                        body = 3  # transformer (heat source)
                    elif use_spider and in_spider_zone(x_mid, z_mid, y_mid, n_trans):
                        body = 4  # aluminum spider
                    else:
                        body = 1  # air

                    # Node numbering
                    # Node at (ix, iz, iy) index: n = iy*nz*nx + iz*nx + ix + 1
                    n1 = iy * nz * nx + iz * nx + ix + 1
                    n2 = iy * nz * nx + iz * nx + ix + 2
                    n3 = iy * nz * nx + (iz + 1) * nx + ix + 2
                    n4 = iy * nz * nx + (iz + 1) * nx + ix + 1
                    n5 = (iy + 1) * nz * nx + iz * nx + ix + 1
                    n6 = (iy + 1) * nz * nx + iz * nx + ix + 2
                    n7 = (iy + 1) * nz * nx + (iz + 1) * nx + ix + 2
                    n8 = (iy + 1) * nz * nx + (iz + 1) * nx + ix + 1

                    f.write(f"{eid} {body} 808 {n1} {n2} {n3} {n4} {n5} {n6} {n7} {n8}\n")

    # --- mesh.boundary ---
    # Format: elem_id bc_id body_id 0 elem_type n1 n2 n3 n4
    def adjacent_body(x_mid, z_mid):
        """Determine which body is adjacent to a boundary face"""
        if x_mid >= BOX_INNER - 1e-10 or z_mid >= BOX_INNER - 1e-10:
            return 2  # steel
        r2 = x_mid*x_mid + z_mid*z_mid
        if use_spider and TRANS_OD**2 < r2 and r2 <= BOX_INNER**2:
            return 4  # spider
        return 1  # air

    with open(os.path.join(case_dir, "mesh.boundary"), "w") as f:
        bid = 0

        # BC 3: Symmetry at x=0 (ix=0)
        ix = 0
        for iy in range(ny - 1):
            for iz in range(nz - 1):
                bid += 1
                z_mid = (zs[iz] + zs[iz+1]) / 2.0
                body = adjacent_body(0, z_mid)
                n1 = iy * nz * nx + iz * nx + ix + 1
                n2 = iy * nz * nx + (iz + 1) * nx + ix + 1
                n3 = (iy + 1) * nz * nx + (iz + 1) * nx + ix + 1
                n4 = (iy + 1) * nz * nx + iz * nx + ix + 1
                f.write(f"{bid} 3 {body} 0 404 {n1} {n2} {n3} {n4}\n")

        # BC 3: Symmetry at z=0 (iz=0)
        iz = 0
        for iy in range(ny - 1):
            for ix in range(nx - 1):
                bid += 1
                x_mid = (xs[ix] + xs[ix+1]) / 2.0
                body = adjacent_body(x_mid, 0)
                n1 = iy * nz * nx + iz * nx + ix + 1
                n2 = iy * nz * nx + iz * nx + ix + 2
                n3 = (iy + 1) * nz * nx + iz * nx + ix + 2
                n4 = (iy + 1) * nz * nx + iz * nx + ix + 1
                f.write(f"{bid} 3 {body} 0 404 {n1} {n2} {n3} {n4}\n")

        # BC 1: Convection at x = nx-1 (exterior wall)
        ix = nx - 1
        for iy in range(ny - 1):
            for iz in range(nz - 1):
                bid += 1
                body = 2  # always steel on exterior
                n1 = iy * nz * nx + iz * nx + ix + 1
                n2 = iy * nz * nx + (iz + 1) * nx + ix + 1
                n3 = (iy + 1) * nz * nx + (iz + 1) * nx + ix + 1
                n4 = (iy + 1) * nz * nx + iz * nx + ix + 1
                f.write(f"{bid} 1 {body} 0 404 {n1} {n2} {n3} {n4}\n")

        # BC 1: Convection at z = nz-1 (exterior wall)
        iz = nz - 1
        for iy in range(ny - 1):
            for ix in range(nx - 1):
                bid += 1
                body = 2
                n1 = iy * nz * nx + iz * nx + ix + 1
                n2 = iy * nz * nx + iz * nx + ix + 2
                n3 = (iy + 1) * nz * nx + iz * nx + ix + 2
                n4 = (iy + 1) * nz * nx + iz * nx + ix + 1
                f.write(f"{bid} 1 {body} 0 404 {n1} {n2} {n3} {n4}\n")

        # BC 2: Adiabatic at y=0 (bottom)
        iy = 0
        for iz in range(nz - 1):
            for ix in range(nx - 1):
                bid += 1
                x_mid = (xs[ix] + xs[ix+1]) / 2.0
                z_mid = (zs[iz] + zs[iz+1]) / 2.0
                body = adjacent_body(x_mid, z_mid)
                n1 = iy * nz * nx + iz * nx + ix + 1
                n2 = iy * nz * nx + iz * nx + ix + 2
                n3 = iy * nz * nx + (iz + 1) * nx + ix + 2
                n4 = iy * nz * nx + (iz + 1) * nx + ix + 1
                f.write(f"{bid} 2 {body} 0 404 {n1} {n2} {n3} {n4}\n")

        # BC 2: Adiabatic at y = ny-1 (top)
        iy = ny - 1
        for iz in range(nz - 1):
            for ix in range(nx - 1):
                bid += 1
                x_mid = (xs[ix] + xs[ix+1]) / 2.0
                z_mid = (zs[iz] + zs[iz+1]) / 2.0
                body = adjacent_body(x_mid, z_mid)
                n1 = iy * nz * nx + iz * nx + ix + 1
                n2 = iy * nz * nx + iz * nx + ix + 2
                n3 = iy * nz * nx + (iz + 1) * nx + ix + 2
                n4 = iy * nz * nx + (iz + 1) * nx + ix + 1
                f.write(f"{bid} 2 {body} 0 404 {n1} {n2} {n3} {n4}\n")

    return total_h

def write_sif(case_dir, n_trans, total_h, cfg, use_spider=False):
    """Write Elmer SIF file for thermal simulation"""
    P_total = cfg["P_total_W"]
    V_one = 3.14159 * (TRANS_OD**2 - TRANS_ID**2) * TRANS_H
    q_dot_vol = P_total / (n_trans * V_one)
    q_dot_mass = q_dot_vol / 5000.0

    h_conv = 7.5
    T_amb = 30.0

    mat4 = ""
    body4 = ""
    if use_spider:
        mat4 = """
Material 4  ! Aluminum spider (brazos al poste)
  Name = "Aluminum spider"
  Density = 2700.0
  Heat Conductivity = 200.0
  Heat Capacity = 900.0
End
"""
        body4 = """
Body 4  ! Aluminum spider bridge to wall
  Equation = 1
  Material = 4
End
"""

    sif = f"""Header
  Mesh DB "." "mesh"
  Include Path ""
  Results Directory "./results"
End

!===========================================================
! MATERIALS
!===========================================================

Material 1  ! Air (inside post, effective k for nat convection)
  Name = "Air (eff)"
  Density = 1.2
  Heat Conductivity = 10.0  ! W/mK (eff, chimney effect ~400x molecular)
  Heat Capacity = 1005.0
End

Material 2  ! Steel (post wall)
  Name = "Steel (galvanized)"
  Density = 7850.0
  Heat Conductivity = 50.0  ! W/mK
  Heat Capacity = 490.0
End

Material 3  ! Transformer (windings+core average)
  Name = "Transformer 5kVA"
  Density = 5000.0
  Heat Conductivity = 100.0  ! Al+Fe weighted avg
  Heat Capacity = 600.0
End
{mat4}
!===========================================================
! SOLVERS
!===========================================================

Solver 1
  Equation = "Heat Equation"
  Variable = Temperature
  Variable DOFs = 1
  Procedure = "HeatSolve" "HeatSolver"
  Exec Solver = Always
  Steady State = Logical True
  Nonlinear System Max Iterations = 50
  Nonlinear System Convergence Tolerance = 1.0e-8
  Nonlinear System Relaxation Factor = 1.0
  Linear System Solver = Iterative
  Linear System Iterative Method = CG
  Linear System Preconditioning = ILU0
  Linear System Max Iterations = 500
  Linear System Convergence Tolerance = 1.0e-8
End

!===========================================================
! EQUATION
!===========================================================

Equation 1
  Name = "Heat Equation"
  Active Solvers = 1
End

!===========================================================
! BOUNDARY CONDITIONS
!===========================================================

! BC 1: Natural convection on post exterior
! h = 7.5 W/m2K, T_inf = 30 C
Boundary Condition 1
  Target Boundaries(1) = 1
  Name = "Exterior_Convection"
  Heat Transfer Coefficient = {h_conv}
  External Temperature = {T_amb}
End

! BC 2: Adiabatic (top/bottom ends of simulated section)
Boundary Condition 2
  Target Boundaries(1) = 2
  Name = "Adiabatic_Ends"
  Heat Flux = 0.0
End

! BC 3: Symmetry planes (x=0, z=0)
Boundary Condition 3
  Target Boundaries(1) = 3
  Name = "Symmetry"
  Heat Flux = 0.0
End

!===========================================================
! BODY FORCE - Heat source in transformer
!===========================================================

Body Force 1
  Name = "Transformer_Heat"
  Heat Source = {q_dot_mass:.4f}
End

!===========================================================
! BODIES
!===========================================================

Body 1  ! Air inside post
  Equation = 1
  Material = 1
End

Body 2  ! Post wall (steel)
  Equation = 1
  Material = 2
End

Body 3  ! Transformer (generates heat)
  Equation = 1
  Material = 3
  Body Force = 1
End
{body4}
!===========================================================
! SIMULATION CONTROL
!===========================================================

Simulation
  Max Output Level = 5
  Coordinate System = Cartesian 3D
  Coordinate Scaling = 1.0
  Simulation Type = Steady
  Steady State Max Iterations = 1
  Post File = "postedor.ep"
End
"""
    with open(os.path.join(case_dir, "case.sif"), "w") as f:
        f.write(sif)

def run_case(n_trans, use_spider=False):
    """Full simulation for one case"""
    cfg = CONFIGS[str(n_trans)]
    suffix = "_con_spider" if use_spider else "_sin_spider"
    base_name = f"caso_{n_trans}_paralelo{n_trans}" if n_trans > 1 else "caso_1_solo"
    case_name = base_name + suffix
    case_dir = os.path.join(HERE, "..", "elmer", case_name)
    case_dir = os.path.normpath(case_dir)

    # Clean and recreate
    if os.path.exists(case_dir):
        shutil.rmtree(case_dir)
    os.makedirs(os.path.join(case_dir, "mesh"))
    os.makedirs(os.path.join(case_dir, "results"))

    label = f"{cfg['n']}x5kVA = {cfg['S_kVA']}kVA"
    print(f"\n{'='*60}")
    print(f"{'CON SPIDER' if use_spider else 'SIN SPIDER'} — CASO {n_trans}: {label}")
    print(f"  Lost: Cu={cfg['P_cu_W']:.0f}W  Fe={cfg['P_fe_W']:.0f}W  Total={cfg['P_total_W']:.0f}W")
    print(f"{'='*60}")

    # Create mesh in 'mesh' subdirectory
    mesh_dir = os.path.join(case_dir, "mesh")
    total_h = create_mesh(mesh_dir, n_trans, use_spider)
    print(f"  Total height: {total_h:.3f}m")
    print(f"  Mesh: {mesh_dir}")

    # Write SIF
    write_sif(case_dir, n_trans, total_h, cfg, use_spider)
    print(f"  SIF: {os.path.join(case_dir, 'case.sif')}")

    # Run ElmerSolver
    print("  Running ElmerSolver...")
    orig = os.getcwd()
    os.chdir(case_dir)
    try:
        r = subprocess.run(
            [os.path.join(ELMER_BIN, "ElmerSolver.exe"), "case.sif"],
            capture_output=True, text=True, timeout=300
        )
        with open(os.path.join(case_dir, "solver_output.txt"), "w") as f:
            f.write(r.stdout)
            if r.stderr:
                f.write("\nSTDERR:\n" + r.stderr)
        if r.returncode == 0:
            print("  OK - simulation completed")
        else:
            print(f"  ERROR code {r.returncode}")
    except subprocess.TimeoutExpired:
        print("  TIMEOUT (5 min)")
    except Exception as e:
        print(f"  ERROR: {e}")
    finally:
        os.chdir(orig)

if __name__ == "__main__":
    casos = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else [1, 2, 3, 4]
    for spider in [False, True]:
        for n in casos:
            run_case(n, spider)
    print("\nDone. Check results/ directories for outputs.")
