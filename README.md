# AI-model-deployment-project

Orange Pi Zero 3W 端侧 YOLOv5 球体检测与小车追踪。

## 目录结构

| 文件夹 | 内容 |
|--------|------|
| `ModelTraining/` | PC 端 Python 代码：模型训练、ONNX 导出、数据集配置、验证脚本 |
| `Deployment/`    | 板端 C++/ROS 2 代码：NPU 推理、摄像头采集、电机控制、RTSP推流、远程监控 |

## 版式演进

- v1.0 — 静态图片推理 (yolov5_static)
- v1.5 — 摄像头实时推理 (yolov5_camera)
- v2.0 — ROS 2 + 电机控制 (yolov5_ROS_1.0)
- v3.0 — Web 远程监控 (yolov5_ROS_2.0_web_monitor)
- v3.5 — C++ RAII 重构 (yolov5_ROS_3.0_RAIIManagement)
- **v4.0 — RTSP推流 + 全链路性能优化** (yolov5_ROS_4.0_PerfOptimization)

## 硬件

- Orange Pi Zero 3W (Allwinner H618, NPU v3 VIP9000)
- 4WD 小车底盘 + L298N 电机驱动 + TT 金属齿轮电机
- USB 摄像头 640x480 YUYV

## 模型

YOLOv5s 单类 (ball)，mAP@0.5=0.995，INT8 量化部署，推理 ~30ms/帧。

## v4.0 核心升级

- FFmpeg RTSP推流集成进后处理：`push_image_to_stream()` → `stream_worker()` 独立线程
- 全链路性能优化：临界区最小化、双缓冲copyTo、YOLO预处理向量化、条件变量
- 单帧耗时从 300ms+ 降至 20~50ms
