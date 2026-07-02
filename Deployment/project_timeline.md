# YOLOv5 端侧部署项目 — 版本演进与节点管理

## 项目时间线

| 版本 | 文件夹 | 完成时间 | 新增特性 |
|------|--------|---------|---------|
| v0.1 | yolov5_static | 2026-05 | 静态图片 NPU 推理，C 语言，无摄像头无电机 |
| v0.2 | yolov5_camera | 2026-05 | USB 摄像头实时采集，V4L2 裸驱动，C++ 前后处理 |
| v1.0 | yolov5_ROS | 2026-06 | ROS 1 Noetic 集成，catkin_make，视觉+电机单文件 |
| v2.0 | yolov5_ROS_1.0 | 2026-06 | ROS 2 Humble 双节点架构，colcon build，watchdog 电机控制 |
| v2.5 | yolov5_ROS_2.0_web_monitor | 2026-06 | Flask HTTP API + PyQt5 桌面客户端，QThread 非阻塞网络，远程监控 |
| v3.0 | yolov5_ROS_3.0_RAIIManagement | 2026-07 | C++ RAII 重构：Gpio/Motor 类封装，sysfs 替代 system()，编码规范统一 |

## 各版本 README 状态

| 文件夹 | 状态 | 内容概要 |
|--------|------|---------|
| yolov5_static | 未填写 | 仅模板 |
| yolov5_camera | 未填写 | 仅模板 |
| yolov5_ROS | 未填写 | 仅模板 |
| yolov5_ROS_1.0 | 完整 | 6 部分：摄像头采集→前处理→NPU推理→后处理→ROS 2通信→电机控制 |
| yolov5_ROS_2.0_web_monitor | 完整 | 1-6 部分（同上）+ 新增第 7 部分：Flask API + PyQt5 桌面客户端，mermaid 流程图 |
| yolov5_ROS_3.0_RAIIManagement | 待更新 | 编码规范 + Gpio/Motor RAII + vision_node 语义命名 |

---

## 开发日记

### 2026-07-02 C++ RAII 重构

- 制定 C++ 编码规范 cpp_style_guide.md：变量全英文单词+下划线、RAII、花括号同行、常量在左、snprintf 格式串不换行
- vision_node.cpp 重构：cam_id→camera_id, ctx_→context, inp→input_data, o→output_buffers, t0→start_clock, ms→latency_ms；所有变量声明移到函数顶部；status_file_temp 改为先声明后 open() 防止提前创建垃圾文件；成员变量移到 private 区域最前
- motor_node.cpp 重构：Gpio 类封装 sysfs export/direction/value/unexport；Motor 类封装四个方向（stop/forward/left/right），raw() 私有实现；Gpio 构造/析构用 system("sudo ...") 解决权限问题，write() 高频调用走 ofstream 零 fork
- Motor 类左右转方向修正：left() 用 raw(1,0,1,0)，right() 用 raw(0,1,0,1)，经板端实测确认

### 2026-06-30

- 板端部署测试：小车成功追球，前后端通信正常，点动转向控制 + 冷却期解决转弯过多问题
- 摄像头驱动问题定位：进程异常退出时 ~VisionNode() 未执行 → cap.release() 未跑 → V4L2 驱动状态残留 → 下次 cap.open() 卡死。证据：dmesg 显示 -110 ETIMEDOUT

### 2026-06-28

- 4WD 小车组装完成：TT 金属齿轮电机 + C25 铝合金底盘 + L298N 驱动板 + 18650 3S 电池
- IMX219 MIPI 摄像头到货，官方 SDK 测试通过 V4L2Camera 类
