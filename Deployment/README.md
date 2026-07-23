# Deployment - Orange Pi Zero 3W 板端部署代码

C++ / ROS 2 推理与电机控制代码合集。

## 项目演进路线

```
yolov5_static → yolov5_camera → yolov5_ROS_1.0 → yolov5_ROS_2.0_web_monitor → yolov5_ROS_3.0_RAIIManagement → yolov5_ROS_4.0_PerfOptimization
   静态图片        摄像头实时        ROS 2双节点        远程监控桌面端                C++ RAII重构                    RTSP推流+多线程性能优化
```

## 项目一览

| 项目 | 功能 | 说明 |
|------|------|------|
| `yolov5_static` | 读取静态图片进行 NPU 推理 | 无摄像头循环，无电机控制。C 语言 |
| `yolov5_camera` | USB 摄像头实时推理 | V4L2 + NPU，无 ROS，无电机。C++ |
| `yolov5_ROS_1.0` | ROS 2 双节点 + 电机控制 | vision_node → /ball/cx → motor_node 点动式控制+watchdog |
| `yolov5_ROS_2.0_web_monitor` | HTTP API + PyQt5 桌面客户端 | Flask 状态/画面接口，PC PyQt5 客户端实时查看+手动控制电机 |
| `yolov5_ROS_3.0_RAIIManagement` | C++ RAII 重构 | Gpio sysfs RAII、Motor 语义抽象、变量全单词命名、代码规范文档 |
| `yolov5_ROS_4.0_PerfOptimization` | RTSP推流 + 全链路性能优化 | ffmpeg推流集成进后处理、stream_worker独立线程、双缓冲copyTo消除堆碎片、YOLO预处理向量化、条件变量替代sleep轮询。全链路耗时300ms+→20~50ms |

## 编译方式

- `yolov5_static`、`yolov5_camera`：`cmake .. && make`
- `yolov5_ROS_1.0`~`yolov5_ROS_4.0_PerfOptimization`：`colcon build --packages-select <包名>` (ROS 2 Humble)
