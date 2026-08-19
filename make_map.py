# Generates a 7-field city_map.csv as a grid graph. 
import argparse

def gen(cols, rows, spacing, weight, out):
    def nid(c, r):
        return f"N{c}_{r}"
    lines = ["# start_id,start_x,start_y,end_id,end_x,end_y,weight"]
    for c in range(cols):
        for r in range(rows):
            x, y = c * spacing, r * spacing
            # east neighbor
            if c + 1 < cols:
                x2, y2 = (c + 1) * spacing, y
                lines.append(f"{nid(c,r)},{x:.1f},{y:.1f},{nid(c+1,r)},{x2:.1f},{y2:.1f},{weight}")
            # south neighbor
            if r + 1 < rows:
                x2, y2 = x, (r + 1) * spacing
                lines.append(f"{nid(c,r)},{x:.1f},{y:.1f},{nid(c,r+1)},{x2:.1f},{y2:.1f},{weight}")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    span = (cols - 1) * spacing
    print(f"Wrote {out}: {cols}x{rows} grid, {len(lines)-1} edges, extent 0..{span}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cols", type=int, default=10)
    ap.add_argument("--rows", type=int, default=10)
    ap.add_argument("--spacing", type=float, default=100.0)
    ap.add_argument("--weight", type=float, default=1.0)
    ap.add_argument("--out", default="city_map.csv")
    a = ap.parse_args()
    gen(a.cols, a.rows, a.spacing, a.weight, a.out)
