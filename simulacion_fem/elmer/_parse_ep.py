import os

# Find the .ep file
ep_files = []
for root, dirs, files in os.walk(r"C:\Postgres\Postedor\simulacion_fem\elmer\caso_1_solo\results"):
    for f in files:
        if f.endswith(".ep"):
            ep_files.append(os.path.join(root, f))

if not ep_files:
    print("No .ep files found")
    exit(1)

fname = ep_files[0]
print(f"Reading: {fname}")

with open(fname) as f:
    lines = f.readlines()

# Find the scalar: line and count total lines
header = lines[0].strip()
print(f"Header: {header}")
parts = header.split()
nnodes = int(parts[0])

# Find scalar start
scalar_start = None
for i, line in enumerate(lines):
    if "#time" in line and i > 3000:
        scalar_start = i + 1
        break

if scalar_start is None:
    print("Could not find scalar section")
    exit(1)

print(f"Scalar data starts at line {scalar_start}")

# Parse scalar values
scalar_values = []
for i in range(scalar_start, len(lines)):
    line = lines[i].strip()
    for val in line.split():
        if val:
            scalar_values.append(float(val))

# Check if we have at least nnodes values
if len(scalar_values) >= nnodes:
    nodal_vals = scalar_values[:nnodes]
    print(f"\nNodal temperatures ({len(nodal_vals)} values):")
    print(f"  Max: {max(nodal_vals):.1f}")
    print(f"  Min: {min(nodal_vals):.1f}")
    print(f"  Avg: {sum(nodal_vals)/len(nodal_vals):.1f}")
    sv = sorted(nodal_vals)
    print(f"  Median: {sv[len(sv)//2]:.1f}")
    top10 = sorted(nodal_vals, reverse=True)[:10]
    print(f"  Top 10: {[f'{v:.0f}' for v in top10]}")
    bot5 = sorted(nodal_vals)[:5]
    print(f"  Bottom 5: {[f'{v:.1f}' for v in bot5]}")
else:
    print(f"Found {len(scalar_values)} values (expected {nnodes}+)")
    print(f"  Max: {max(scalar_values):.1f}")
    print(f"  Min: {min(scalar_values):.1f}")
