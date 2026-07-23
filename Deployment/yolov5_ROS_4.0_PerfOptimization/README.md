# Orange Pi Zero 3W — YOLOv5 v4.0 PerfOptimization

## 数据流架构
更新了整个数据流框架，新增了FFmpeg数据流分支，使用VLC连接串流就可以实时看到NPU推理的结果
```
CV采集 → 前处理(letterbox/NCHW) → NPU推理(INT8,~30ms) → 后处理(sigmoid+NMS)
                                                              │
                                          ┌───────────────────┴───────────────────┐
                                          │                                       │
                                    ROS2 /ball/cx                         push_image_to_stream()
                                          │                                       │
                                    motor_node                           stream_worker()
                                      (电机控制)                          (独立推流线程)
                                                                                │
                                                                         ffmpeg stdin
                                                                         (H.264 zerolatency)
                                                                                │
                                                                           mediamtx :8554
                                                                                │
                                                                              VLC
```

后处理结果有两条独立流向：
- **电机控制**：球坐标通过 ROS2 /ball/cx 话题发给 motor_node，驱动小车追球
- **RTSP推流**：`push_image_to_stream()` 将画框后的帧推入队列，独立线程 `stream_worker()` 消费队列通过 ffmpeg 管道推送 H.264 流到 mediamtx，VLC 远程观看

## 关键函数说明

| 函数 | 位置 | 作用 |
|------|------|------|
| `stream_thread_start()` | yolov5_post_process | 启动推流线程 |
| `stream_worker()` | yolov5_post_process | 推流线程主循环，从队列消费帧，resize 后写入 ffmpeg stdin |
| `ffmpeg_start()` | yolov5_post_process | 启动 ffmpeg 子进程，创建 stdin 管道，等待视频帧输入 |
| `push_image_to_stream(src)` | yolov5_post_process | 后处理画完框后调用，将帧推入推流队列 |



## 全链路性能优化

### 优化前故障现象

| 现象 | 指标 |
|------|------|
| 画面周期性严重卡顿 | 单帧总耗时峰值达到 300ms 以上 |
| 多线程读写推理队列</br>锁等待耗时巨大 | lock=100~260ms，post_push 成为性能黑洞 |
| 随机耗时毛刺 | 长时间运行出现随机 10~15ms 耗时尖峰 |
| YOLO 预处理瓶颈 | 预处理峰值耗时 90ms，全链路最大瓶颈 |
| 图像异常 | 偶发画面撕裂、色块错乱，堆内存碎片持续累积 |

### 四大核心优化

#### 优化1：缩小临界区

**问题**：`stream_worker()` 原始代码持锁 sleep、持锁执行 ffmpeg fwrite IO，`push_image_to_stream()` 锁内执行 clone 深拷贝。日志锁等待峰值 260ms。

**修复**：锁仅保护队列存取操作。sleep、resize、ffmpeg IO 全部移到锁外。`push_image_to_stream()` 的 clone 移到锁外执行。

**收益**：锁等待耗时稳定 0ms，彻底消除数百 ms 锁阻塞尖峰。

#### 优化2：clone → 全局双缓冲 copyTo

**问题**：每帧 clone 产生频繁 malloc/free，在 AI 推理和 FFmpeg 编码抢占 DDR 带宽时，内存分配触发内核缺页和页表映射，产生 10~15ms 随机毛刺。

**修复**：`push_image_to_stream()` 启动时一次性分配两块固定画布 bufA/bufB，每帧 `src.copyTo(bufA)` 写预分配内存（无 malloc），队列 push 使用 Mat 浅拷贝（仅复制头部指针）。

**收益**：图像拷贝耗时稳定 0.1~1ms，消除 10~15ms 随机尖峰，堆碎片停止增长。

#### 优化3：YOLO 预处理向量化

**问题**：原始三嵌套像素循环做 HWC→NCHW 转换，大量随机内存寻址 ARM 缓存命中率极低；冗余浮点转换产生额外抖动。峰值 80~90ms。

**修复**：
- 改用 `INTER_NEAREST` 最快插值（AI 检测无损精度）
- 复用全局 letterbox 画布不新建矩阵
- `split` 通道分离 + `memcpy` 批量连续拷贝（底层调用 NEON 向量化指令）

**收益**：预处理耗时从峰值 90ms 降至稳定 1~9ms。

#### 优化4：单缓冲 → 双缓冲交替写入

**问题**：单块全局缓冲所有帧共用一块内存，`stream_worker()` 读取旧帧同时 `push_image_to_stream()` 覆盖同一块内存，Mat 引用计数只管理释放不管覆盖保护，导致画面撕裂。

**修复**：双缓冲 bufA/bufB 交替写入，配合无锁预判队列长度——队列满时直接丢帧，主线程永远不会覆盖子线程正在读取的缓冲区。

**收益**：彻底消除画面撕裂，长时间运行图像输出稳定完整。

#### 进阶：条件变量替代 sleep 轮询

**问题**：`stream_worker()` 原始用 1ms sleep 轮询空队列，无帧时定时唤醒占用 CPU，最小延迟 1ms。

**修复**：`std::condition_variable` 的 `wait()` 在空队列时自动释放 mutex 并休眠；`push_image_to_stream()` 入队时 `notify_one()` 立即唤醒 `stream_worker()`。

**收益**：无固定轮询延迟，空队列时零 CPU 占用。

### 优化前后量化对比

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 互斥锁等待峰值 | 260ms | 稳定 0ms |
| YOLO 预处理峰值 | 90ms | 1~9ms |
| 图像拷贝毛刺 | 10~15ms 随机尖峰 | 0.1~1ms 稳定 |
| 单帧全链路最大耗时 | 300ms+ | 20~50ms |
| 画面稳定性 | 周期性卡顿、偶发撕裂 | 全程流畅无撕裂 |
| 内存碎片 | 持续累积，越跑越卡 | 无新增堆碎片 |

## 编译与运行

```bash
# 编译
cd ~/catkin_ws && colcon build --packages-select yolov5_vision motor_control && source install/setup.bash

# T1: RTSP 服务器
cd ~/mediamtx && ./mediamtx

# T2: 视觉节点(内置推流)
~/catkin_ws/install/yolov5_vision/lib/yolov5_vision/vision_node 0

# T3: 电机节点
~/catkin_ws/install/motor_control/lib/motor_control/motor_node
```

VLC: `rtsp://192.168.1.48:8554/cam?tcp`
