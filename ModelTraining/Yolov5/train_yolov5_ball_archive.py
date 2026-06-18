"""
=================================================================
YOLOv5 单类球体检测 — 完整训练 + 导出 + 转换流程
=================================================================

环境: pytorch1_12 (Python 3.10.8, torch 2.7.1+cu118, CUDA 11.8)
数据集: E:\Project_AIDeploy\Yolov5\datasets\ball
         ├── images/train/   ← 训练图 (131张, 含86张有球)
         ├── images/val/     ← 验证图 (33张, 含21张有球)
         ├── labels/train/   ← YOLO标注 (labelMe圆/矩形→脚本转)
         ├── labels/val/     ← YOLO标注
         └── ball.yaml       ← 数据集配置文件
         
标注工具: labelMe (画圆/矩形均可, 统一用 convert_json2yolo.py 转)
训练输出: E:\Project_AIDeploy\Yolov5\runs\yolov5s_ball2\weights\best.pt
ONNX导出: best.onnx → pegasus转换 → NB → 板端部署

C代码修改: yolov5_post_process.cpp 中 draw_objects 的 class_names
          static const char* class_names[] = {"ball"};
"""

import subprocess, sys, os

# ================ 数据集路径 ================
DATASET_DIR = r"E:\Project_AIDeploy\Yolov5\datasets\ball"
YOLOV5_DIR  = r"E:\Project_AIDeploy\Yolov5\yolov5"
PROJECT_DIR = r"E:\Project_AIDeploy\Yolov5\runs"

def step_train():
    """Step 1: 训练模型"""
    cmd = [
        sys.executable, "train.py",
        "--img", "640",
        "--batch", "16",
        "--epochs", "100",
        "--data", os.path.join(DATASET_DIR, "ball.yaml"),
        "--weights", os.path.join(YOLOV5_DIR, "yolov5s.pt"),
        "--project", PROJECT_DIR,
        "--name", "yolov5s_ball",
        "--device", "0",      # GPU=0, CPU=cpu
    ]
    subprocess.run(cmd, cwd=YOLOV5_DIR)

def step_export_onnx():
    """Step 2: 导出ONNX"""
    weights = os.path.join(PROJECT_DIR, "yolov5s_ball", "weights", "best.pt")
    cmd = [
        sys.executable, "export.py",
        "--weights", weights,
        "--include", "onnx",
        "--img", "640",
        "--batch", "1",
    ]
    subprocess.run(cmd, cwd=YOLOV5_DIR)
    print("ONNX saved to:", weights.replace(".pt", ".onnx"))

def step_find_output_nodes():
    """Step 3: 查ONNX节点ID (给inputs_outputs.txt用)"""
    import onnx
    onnx_path = os.path.join(PROJECT_DIR, "yolov5s_ball", "weights", "best.onnx")
    m = onnx.load(onnx_path)
    out_names = [o.name for o in m.graph.output]
    node_ids = []
    for i, node in enumerate(m.graph.node):
        for o in node.output:
            if o in out_names:
                node_ids.append(str(i))
                print(f"  output node: id={i} name={o} op={node.op_type}")
    print(f"\n在 inputs_outputs.txt 中写入:")
    print(f"--inputs images --input-size-list '3,640,640' --outputs '{" ".join(node_ids)}'")

def convert_json2yolo():
    """将labelMe JSON转YOLO txt"""
    import json, glob, math
    for subset in ["train", "val"]:
        for jp in glob.glob(os.path.join(DATASET_DIR, "labels", subset, "*.json")):
            d = json.load(open(jp))
            iw, ih = d["imageWidth"], d["imageHeight"]
            lines = []
            for s in d["shapes"]:
                if s["label"] != "ball": continue
                pts, st = s["points"], s["shape_type"]
                if st == "circle":
                    cx, cy = pts[0]; px, py = pts[1]
                    r = math.hypot(px-cx, py-cy)
                    x, y, bw, bh = cx-r, cy-r, 2*r, 2*r
                elif st in ("rectangle", "polygon"):
                    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                    x = min(xs); y = min(ys)
                    bw = max(xs)-x; bh = max(ys)-y
                else: continue
                lines.append(f"0 {(x+bw/2)/iw:.6f} {(y+bh/2)/ih:.6f} {bw/iw:.6f} {bh/ih:.6f}")
            open(jp.replace(".json", ".txt"), "w").write("\n".join(lines) + "\n" * bool(lines))

if __name__ == "__main__":
    print("1. 训练")  # step_train()
    print("2. 导出ONNX")  # step_export_onnx()
    print("3. 查节点ID")  # step_find_output_nodes()
