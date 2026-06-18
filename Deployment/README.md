# Deployment - 板端部署代码

Orange Pi Zero 3W 上的 C++ / ROS 2 推理与电机控制代码。

## 项目一览

| 项目 | 功能 | 特点 |
|------|------|------|
| `yolov5_static` | 读取静态图片进行 NPU 推理 | 无摄像头循环，无电机控制。用于快速验证模型精度和推理管线 |
| `yolov5_camera` | USB 摄像头实时推理 | 摄像头 + NPU 推理循环，无 ROS，无电机。用于验证实时帧率和前后处理 |
| `yolov5_ROS_1.0` | 摄像头 + NPU + ROS 2 + 电机控制 | 视觉节点发布球坐标话题，电机节点订阅后驱动小车。点动式控制+watchdog。已测试通过 |
| `yolov5_ROS_2.0` | v1.0 的多线程升级版 | 双缓冲采集+推理管线、原子变量共享检测结果、电机异步控制。文档已完成，待硬件测试 |
| `web_monitor` | HTTP API + PyQt5 桌面客户端 | Flask 服务跑在板端提供状态/画面接口，PC 端 PyQt5 客户端实时查看画面、球位置曲线、延迟仪表和手动控制电机 |

## 编译方式

板端统一使用 `colcon build --packages-select <包名>`（ROS 2 Humble），详见各项目的 `CMakeLists.txt`。

## 关键技术点

1. **INT8 量化通道精度丢失**：YOLOv8 Concat 后 bbox(0~640) 和 class(-5~5) 共享量化步长，class 被压零。改为 YOLOv5 三头输出 + C++ 解码解决。
2. **摄像头 V4L2 阻塞**：部分 USB 摄像头不响应 OpenCV 内部 UVC 控制查询，改用 V4L2 裸驱动 + select 超时。
3. **电机失控**：视觉节点断连时电机保持上次方向，加入 watchdog 定时器 1 秒超时自动停车。
4. **ROS 2 话题通信**：`/ball/cx` (Float32) 传输球中心 x 坐标，无球时发 -1.0。
