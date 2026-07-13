import os

base = r"C:\Postgres\Postedor\simulacion_fem\elmer"
cases = [
    ("caso_1_solo", "1", "1x5kVA = 5kVA"),
    ("caso_2_paralelo2", "2", "2x5kVA = 10kVA"),
    ("caso_3_paralelo3", "3", "3x5kVA = 15kVA"),
    ("caso_4_paralelo4", "4", "4x5kVA = 20kVA"),
]

print(f"{'Caso':<18} {'Max T':>8} {'Min T':>8} {'Avg T':>8} {'Nodes':>6}")
print("-" * 50)

for case_dir, _, label in cases:
    ep_dir = os.path.join(base, case_dir, "results")
    ep_files = [f for f in os.listdir(ep_dir) if f.endswith(".ep")]
    if not ep_files:
        print(f"{label:<18}  NO FILE")
        continue
    
    fname = os.path.join(ep_dir, ep_files[0])
    with open(fname) as f:
        lines = f.readlines()
    
    header = lines[0].strip()
    nnodes = int(header.split()[0])
    
    # Find scalar section
    scalar_start = None
    for i, line in enumerate(lines):
        if "#time" in line and i > len(lines) // 2:
            scalar_start = i + 1
            break
    
    if scalar_start:
        vals = []
        for i in range(scalar_start, len(lines)):
            for v in lines[i].strip().split():
                try:
                    vals.append(float(v))
                except:
                    pass
        
        if len(vals) >= nnodes:
            nodal = vals[:nnodes]
            print(f"{label:<18} {max(nodal):>8.1f} {min(nodal):>8.1f} {sum(nodal)/len(nodal):>8.1f} {nnodes:>6}")
    
    # Also check solver output for convergence info
    sol_file = os.path.join(base, case_dir, "solver_output.txt")
    if os.path.exists(sol_file):
        with open(sol_file) as f:
            content = f.read()
        for line in content.split("\n"):
            if "Result Norm" in line:
                print(f"  {'Result Norm:':<15} {line.split(':')[-1].strip()}")
                break

print("\nDone.")
