# ========== 环境保护（双保险） ==========
import os
os.environ['ULTRALYTICS_OFFLINE'] = '1'

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# ========== 开始导出 ==========
import torch

# 你的微调模型路径（请确认是否正确）
BEST_PT_PATH = r'E:\Project_AIDeploy\deploy\runs\detect\robot_model_finetuned_final4\weights\best.pt'

# 1. 用 torch.load 直接加载，ultralytics 的联网检查完全不会运行
checkpoint = torch.load(BEST_PT_PATH, map_location='cpu')

# 2. 从 checkpoint 中提取模型（已经是训练好的 DetectionModel）
model = checkpoint['model'].float()  # 转为 float 模式
model.eval()                         # 必须设置为评估模式

# 3. 导出一个假的输入尺寸（1, 3, 640, 640）
dummy_input = torch.randn(1, 3, 640, 640)

# 4. 导出 ONNX
output_path = BEST_PT_PATH.replace('.pt', '.onnx')
torch.onnx.export(
    model,
    dummy_input,
    output_path,
    opset_version=12,
    input_names=['images'],
    output_names=['output0'],
    dynamic_axes={'images': {0: 'batch'}, 'output0': {0: 'batch'}}
)

print(f'✅ ONNX 模型已保存至：{output_path}')
