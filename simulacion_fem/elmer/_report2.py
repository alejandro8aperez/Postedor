import os

base = r"C:\Postgres\Postedor\simulacion_fem\elmer"
cases = [
    ("caso_1_solo", "1×5kVA = 5kVA"),
    ("caso_2_paralelo2", "2×5kVA = 10kVA"),
    ("caso_3_paralelo3", "3×5kVA = 15kVA"),
    ("caso_4_paralelo4", "4×5kVA = 20kVA"),
]

print(f"{'Configuración':<22} {'T_max':>7} {'T_min':>7} {'T_avg':>7} {'h_secc':>7}")
print("-" * 55)

for base_name, label in cases:
    for spider in [False, True]:
        suffix = "_con_spider" if spider else "_sin_spider"
        case_dir = base_name + suffix
        ep_dir = os.path.join(base, case_dir, "results")
        ep_files = [f for f in os.listdir(ep_dir) if f.endswith(".ep")]
        if not ep_files:
            print(f"{label:<22}  NO FILE")
            continue

        fname = os.path.join(ep_dir, ep_files[0])
        with open(fname) as f:
            lines = f.readlines()

        header = lines[0].strip()
        nnodes = int(header.split()[0])

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
                tag = "CON" if spider else "SIN"
                print(f"{tag} spider {label:<10} {max(nodal):>7.1f} {min(nodal):>7.1f} {sum(nodal)/len(nodal):>7.1f}")
