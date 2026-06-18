# ModelTraining - PC 端训练代码

## 目录

| 文件夹 | 说明 |
|--------|------|
| `Yolov5/` | YOLOv5 训练脚本、ONNX 导出（含去 decode 版本）、训练归档脚本 |
| `deploy/` | PC 端 ONNX 验证脚本、单张图测试、微调测试 |
| `docs/` | 训练流程文档 |
| `train/` | 数据集配置文件 (data.yml) |

## 关键文件

- `Yolov5/train_yolov5_ball_archive.py` - 完整训练归档脚本（可复现）
- `Yolov5/ModelExport_noDecode.py` - 导出无 decode 的 ONNX，避免 INT8 量化精度丢失
- `Yolov5/ball_deployment_guide.md` - 端侧部署完整流程文档
