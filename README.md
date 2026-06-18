# AI-model-deployment-project

Orange Pi Zero 3W 端侧 YOLOv5 球体检测与小车追踪。

## 目录结构

| 文件夹 | 内容 |
|--------|------|
| `ModelTraining/` | PC 端 Python 代码：模型训练、ONNX 导出、数据集配置、验证脚本 |
| `Deployment/`    | 板端 C++/ROS 2 代码：NPU 推理管线、摄像头采集、电机控制、远程监控 |

## 硬件

- Orange Pi Zero 3W (Allwinner H618, NPU v3 VIP9000)
- 4WD 小车底盘 + L298N 电机驱动 + MG310 金属齿轮电机
- USB 摄像头 640x480 YUYV

## 模型

YOLOv5s 单类 (ball)，mAP@0.5=0.995，INT8 量化部署，推理 ~50ms/帧。
