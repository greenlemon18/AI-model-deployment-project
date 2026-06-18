import json, glob, math, os

base = r"E:\Project_AIDeploy\Yolov5\datasets\ball"

for subset in ["train", "val"]:
    jsondir = os.path.join(base, "labels", subset)
    for jp in sorted(glob.glob(jsondir + "/*.json")):
        d = json.load(open(jp))
        iw, ih = d.get("imageWidth", 720), d.get("imageHeight", 1280)
        lines = []
        for s in d["shapes"]:
            if s["label"] != "ball": continue
            pts, st = s["points"], s["shape_type"]
            if st == "circle":
                cx, cy = pts[0]; px, py = pts[1]
                r = math.hypot(px-cx, py-cy)
                x, y, bw, bh = cx-r, cy-r, 2*r, 2*r
            elif st == "rectangle":
                x1,y1=pts[0]; x2,y2=pts[1]
                x=min(x1,x2); y=min(y1,y2)
                bw=abs(x2-x1); bh=abs(y2-y1)
            else:
                continue
            lines.append(f"0 {(x+bw/2)/iw:.6f} {(y+bh/2)/ih:.6f} {bw/iw:.6f} {bh/ih:.6f}")
        tp = jp.replace(".json", ".txt")
        open(tp, "w").write("\n".join(lines) + ("\n" if lines else ""))
        print(f"{subset}/{os.path.basename(tp)}: {len(lines)} ball(s)")
print("Done!")
