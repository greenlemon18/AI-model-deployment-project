# AI Model Deployment Project

> Orange Pi Zero 3W 端侧 YOLOv5 球体检测与实时追踪 — 从模型训练到 NPU 量化的完整工程化部署方案

## Overview

本项目实现了一套完整的嵌入式 AI 视觉部署流水线：

- **训练端**：Python + PyTorch，YOLOv5s 模型训练、ONNX 导出、INT8 量化
- **部署端**：C++ ROS 2 节点，NPU VIP9000 推理、USB 摄像头采集、GPIO 电机控制、Web 远程监控
- **量化效果**：模型体积压缩 75%，单帧推理 ~50ms（15fps），mAP@0.5 = 0.995

## 目录结构

```text
├── ModelTraining/         # PC 端：训练、导出、量化、验证
│   ├── dataset/           # 数据集准备
│   ├── training/          # YOLOv5s 训练配置与权重
│   ├── export/            # ONNX 导出
│   └── quantize/          # INT8 量化脚本
├── Deployment/            # 板端：C++ 推理管线
│   ├── yolov5_ROS_3.0_RAIIManagement/  # 最新版本（RAII 资源管理）
│   ├── yolov5_ROS_2.0_web_monitor/     # 带 Web 监控的版本
│   ├── yolov5_ROS/                     # ROS 基础版本
│   ├── yolov5_camera/                  # 摄像头直连版
│   └── yolov5_static/                  # 静态图片推理版
└── README.md
```

## 硬件平台

| 组件 | 型号 | 说明 |
|------|------|------|
| 主板 | Orange Pi Zero 3W | Allwinner H618, 1.5GHz A53 x4 |
| NPU | VIP9000 (3.2 TOPS) | 集成在 H618 中 |
| 摄像头 | USB 640x480 YUYV | V4L2 |
| 底盘 | 4WD 小车 + L298N | MG310 电机 |
| 运行内存 | 1GB LPDDR4 | |

## 性能

| 指标 | 值 |
|------|-----|
| 模型 | YOLOv5s (单类 ball) |
| 精度 | mAP@0.5 = 0.995 |
| 推理速度 | ~50ms/帧 (15fps) |
| 模型体积 | 压缩 75%（INT8 vs FP16） |
| 量化后 Confidence | ~0.95 → ~0.80 |

## 快速开始

```bash
# ModelTraining 环境
pip install -r ModelTraining/requirements.txt

# 部署端（Orange Pi）
# 烧录 Armbian / Orange Pi OS → 安装 ROS 2 → 编译部署代码
```

详细文档见各子目录 README。

## 适用场景

- 端侧 AI 视觉方案验证
- YOLO 模型 NPU 量化部署教学
- 嵌入式 AI 产品原型开发

## 许可

本项目代码采用 MIT 协议。
模型训练基于 YOLOv5（AGPL-3.0）迁移至 YOLOX（Apache-2.0），部署代码独立于训练框架。
