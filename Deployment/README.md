# Deployment - Orange Pi Zero 3W 板端部署代码

C++ / ROS 2 推理与电机控制代码合集。

## 项目演进路线

```
yolov5_static → yolov5_camera → yolov5_ROS_1.0 → yolov5_ROS_2.0_web_monitor → yolov5_ROS_3.0_MultiThread
   静态图片        摄像头实时        ROS 2双节点        远程监控桌面端                 多线程优化
```

## 项目一览

| 项目 | 功能 | 说明 |
|------|------|------|
| `yolov5_static` | 读取静态图片进行 NPU 推理 | 无摄像头循环，无电机控制。用于快速验证模型精度和推理管线。C 语言编写 |
| `yolov5_camera` | USB 摄像头实时推理 | 摄像头 + NPU 推理循环，无 ROS，无电机。V4L2 裸驱动 + C++ |
| `yolov5_ROS_1.0` | ROS 2 双节点 + 电机控制 | vision_node 发布球坐标话题，motor_node 订阅后驱动小车。点动式控制+watchdog。已测试通过 |
| `yolov5_ROS_2.0_web_monitor` | HTTP API + PyQt5 桌面客户端 | Flask 服务跑在板端提供状态/画面接口，PC 端 PyQt5 客户端实时查看画面、延迟曲线和手动控制电机。QThread 非阻塞网络 |
| `yolov5_ROS_3.0_MultiThread` | 多线程性能优化版 | 双缓冲采集+推理管线、原子变量共享检测结果、电机异步控制。文档已完成，待硬件测试 |

## 编译方式

- `yolov5_static`、`yolov5_camera`：`make` 或 `cmake .. && make`
- `yolov5_ROS_1.0`、`yolov5_ROS_3.0_MultiThread`：`colcon build --packages-select <包名>` (ROS 2 Humble)
- `yolov5_ROS_2.0_web_monitor`：`python3 api_server.py` (板端) + `python desktop_client.py` (PC端)
