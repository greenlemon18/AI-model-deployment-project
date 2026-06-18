import torch

# 加载训练好的模型
ckpt = torch.load(r'E:\Project_AIDeploy\Yolov5\runs\yolov5s_ball2\weights\best.pt', map_location='cpu',
                 weights_only=False)
model = ckpt['model'].float()
model.eval()

# 关键：把 Detect 层设成 training=True，ONNX 就不走内置 decode
for m in model.modules():
    if hasattr(m, 'stride'):  # 检测到 Detect 层
        m.training = True

# 导出 ONNX
dummy = torch.randn(1, 3, 640, 640)
torch.onnx.export(model, dummy,
                  r'E:\Project_AIDeploy\Yolov5\runs\yolov5s_ball2\weights\best_no_decode.onnx',
                  input_names=['images'],
                  output_names=['p8', 'p16', 'p32'],
                  opset_version=12)

print('Exported best_no_decode.onnx')

import onnx
m = onnx.load(r'E:\Project_AIDeploy\Yolov5\runs\yolov5s_ball2\weights\best_no_decode.onnx')
for o in m.graph.output:
    shape = [d.dim_value for d in o.type.tensor_type.shape.dim]
    print(f'{o.name}: {shape}')

