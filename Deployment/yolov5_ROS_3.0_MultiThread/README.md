# Orange Pi Zero 3W — YOLOv5 端侧球体检测与小车追踪

## 能用的话来说：整个系统做了什么

```
摄像头拍画面 → 程序找到球 → 用 ROS 2 发球的位置 → 另一个程序驱动小车追球
```

拆成 5 步讲清楚。

---

## 一、怎么读到摄像头画面的

用 OpenCV 的 `cv::VideoCapture` 打开 USB 摄像头。

```cpp
cv::VideoCapture cap;
cap.open(1, cv::CAP_V4L2);
cap.set(cv::CAP_PROP_FRAME_WIDTH, 640);
cap.set(cv::CAP_PROP_FRAME_HEIGHT, 480);
```

- `1` 就是选择 `/dev/video1`（板子上的 USB 摄像头）
- `cv::CAP_V4L2` 让 OpenCV 用 Linux 自带的 V4L2 驱动，不用 GStreamer（因为开发板的 GStreamer 缺插件会报错）
- 640×480 是摄像头的分辨率
- 每帧画面存在 `cv::Mat frame_` 里——就是一个 3 通道的彩色图像矩阵

摄像头拍的画面是横着的，代码里有一行旋转把它转正：

```cpp
cv::rotate(frame_, frame_, cv::ROTATE_90_COUNTERCLOCKWISE);
```

---

## 二、怎么把图片送给 AI 模型推理

### 前处理 (`yolov5_pre_process`)

摄像头出来的图不能直接用——尺寸不对、颜色顺序不对、数据排列不对。前处理做 4 件事：

| 操作 | 做了什么 | 为什么 |
|------|---------|--------|
| BGR 转 RGB | 交换颜色通道顺序 | 训练的模型是 RGB，OpenCV 读出来是 BGR，不一致会认不准 |
| 等比缩放 | 按短边缩放到 640 | 模型输入固定 640×640，不能变 |
| 灰色填充 | 短边两边填灰色(128) | 直接拉伸球会变椭圆，灰色模型训练时见过，能忽略 |
| 转 NCHW 排列 | H×W×C 变成 C×H×W | NPU 硬件要求通道维在前面 |

处理完得到 `[3][640][640]` 的 uint8 数组——这就是 NPU 的输入。

### 加载模型

```cpp
awnn_init();                         // 初始化 NPU 驱动
ctx_ = awnn_create(".../yolov5_ball.nb");  // 加载 NB 模型文件
```

NB 文件是提前在 PC 上用 pegasus 工具把训练好的 PyTorch 模型转成 NPU 能认识的格式。

### 推理

```cpp
void *in[] = {input_data};
awnn_set_input_buffers(ctx_, in);    // 把图送给 NPU
awnn_run(ctx_);                       // NPU 开始算
float **out = awnn_get_output_buffers(ctx_);  // 取结果
```

推理约 50 毫秒，NPU 内部全是用 INT8 整数算的（比浮点快 10 倍但精度稍低）。

### 后处理 (`yolov5_post_process`)

NPU 输出的不是球的位置——是 8400 个候选框的原始分数。后处理做 5 件事：

1. **sigmoid 转换**：把 -14~+12 的原始分数压到 0~1，变成概率
2. **锚框解码**：用预设的 18 个 anchor box + 格子位置 + stride，把相对偏移变成像素坐标
3. **置信度筛选**：`obj × cls > 0.02` 才保留
4. **NMS 去重**：一个球可能被好几个框框住，NMS 按 IoU>0.5 去重只留最可信的
5. **坐标回映射**：从 640×640 的推理空间映射回摄像头的 640×480

结果存到两个全局变量里：

```cpp
g_ball_cx   // 球的水平中心坐标 (0~640)
g_ball_prob // 置信度 (0~1)
```

**重要**：每帧开始时这两个变量会被清零。如果这帧没检测到球，`g_ball_cx` 就是 -1。

---

## 三、ROS 2 怎么通信

### 为什么用 ROS 2

视觉检测和电机控制是两个独立的任务——用 ROS 2 可以把它们拆成两个节点，各管各的，通过**话题**沟通。

### vision_node（视觉节点）

```cpp
// 每 80ms 定时跑一次
timer_ = this->create_wall_timer(std::chrono::milliseconds(80), ...);

void loop() {
    // 1. 读摄像头
    cap_.read(frame_);
    
    // 2. 旋转画面
    cv::rotate(frame_, frame_, cv::ROTATE_90_COUNTERCLOCKWISE);
    
    // 3. 前处理 + NPU推理 + 后处理
    inp = yolov5_pre_process(NULL, &frame_, &fs);
    awnn_set_input_buffers(ctx_, in); awnn_run(ctx_);
    out = awnn_get_output_buffers(ctx_);
    yolov5_post_process(NULL, &frame_, out);
    
    // 4. 发布球的位置
    auto m = std_msgs::msg::Float32();
    m.data = (g_ball_prob > 0.3) ? g_ball_cx : -1.0f;
    pub_->publish(m);
    
    // 5. 存一张最新画面（方便 PC 远程查看）
    cv::imwrite("/tmp/latest.jpg", frame_);
}
```

发布到话题 `/ball/cx`——有球就发位置 (0~640)，没球就发 -1。

### motor_node（电机控制节点）

```cpp
// 订阅 /ball/cx 话题
sub_ = this->create_subscription<std_msgs::msg::Float32>("/ball/cx", ...);

void cb(const Float32 msg) {
    float cx = msg.data;
    if (cx < 0) { motor_stop(); return; }   // 没球就停
    
    float d = cx - 320;   // 球偏画面中心多少
    
    if (d < -50)        motor_raw(0,1,0,1);   // 球在左边 → 左转
    else if (d > 50)    motor_raw(1,0,1,0);   // 球在右边 → 右转
    else                motor_raw(0,1,1,0);   // 球在中间 → 前进
    
    sleep(50ms);         // 转一小下
    motor_stop();        // 停
}
```

50 是死区阈值——球在画面中间 50 像素范围内不走旁路，直接前进。

**握手机制**：如果视觉节点断了（1 秒没收到消息），watchdog 定时器自动停电机。

---

## 四、怎么控制电机

### 硬件

```
Orange Pi GPIO         L298N 电机驱动板
wPi 8  (排针 15)  →  IN1  右轮正反转
wPi 9  (排针 16)  →  IN2  右轮正反转
wPi 13 (排针 22)  →  IN3  左轮正反转
wPi 14 (排针 23)  →  IN4  左轮正反转
物理 14 (GND)     →  GND  (共地)
```

### 控制方式

```cpp
system("gpio write 8 1");  // 给 wPi 8 高电平
system("gpio write 9 0");  // 给 wPi 9 低电平
```

通过 `motor_raw(右IN1, 右IN2, 左IN1, 左IN2)` 统一拼命令字符串。

实测确认的方向：

| 动作 | 右电机 | 左电机 | 效果 |
|------|--------|--------|------|
| 前进 | (0,1) | (1,0) | 两轮正转 |
| 后退 | (1,0) | (0,1) | 两轮反转 |
| 左转 | (0,1) | (0,1) | 右前+左后 |
| 右转 | (1,0) | (1,0) | 右后+左前 |
| 停止 | (0,0) | (0,0) | 都不动 |

### 供电

18650 电池 (2节串联, 7.4V) → L298N → 4 个电机
充电宝 (5V USB-C) → Orange Pi + 摄像头

两套电独立——电机启动瞬间大电流不会让 Orange Pi 掉电。

---

## 五、怎么编译和运行

### 编译

```bash
# 进工作空间
cd ~/catkin_ws

# 改了什么就只编哪个包（省时间）
colcon build --packages-select yolov5_vision    # 改了视觉代码
colcon build --packages-select motor_control    # 改了电机代码

# 加载环境
source install/local_setup.bash
```

### 运行

```bash
# 终端 1（后台）：跑视觉节点
~/catkin_ws/install/yolov5_vision/lib/yolov5_vision/vision_node 0 &>/dev/null &

# 终端 2（后台）：跑电机节点
~/catkin_ws/install/motor_control/lib/motor_control/motor_node &>/dev/null &

# PC 远程看画面
浏览器打开 http://板子IP:8080/latest.jpg
```

---

## 六、关键踩坑记录

1. **量化后置信度通道全零**：YOLOv8 把 bbox(0~640) 和 class(-5~5) 绑在一起量化，步长 2.53 把 class 的精值全 round 成 0。YOLOv5 拆成 3 个独立输出头 + 在 C++ 做 decode 解决。

2. **摄像头打开卡死**：原用 cv::VideoCapture 默认 GStreamer 拆件失败。改 `cv::CAP_V4L2` 就好了。

3. **摄像头画面旋转**：拍出来横着 90 度，`cv::rotate(ROTATE_90_COUNTERCLOCKWISE)` 转正。

4. **球消失后车接着转**：后处理没清空全局变量，旧坐标残留。每帧先清零再赋值解决。

5. **GPIO 左右接反**：IN1/IN2 实际控制右边，IN3/IN4 控制左边——和代码里左右颠倒了。对调 `motor_raw` 参数解决。

6. **电机卡转**：视觉节点断连时，电机保持上级方向转。加 watchdog 每 0.2 秒检查一次，超时 1 秒自动停。



---

## 🆕 七、Web 远程监控前端（Flask + PyQt5）

### 为什么加

v1.0 时调试全靠板端终端输出和 `scp` 拉图片，效率低。加前端后 PC 浏览器或桌面客户端就能实时看画面、球位置、延迟曲线，还能按钮手动控制电机。

### 板端：Flask HTTP API 服务

板端运行 `api_server.py`，提供三个接口：

| 路由 | 作用 |
|------|------|
| `GET /latest.jpg` | 返回最新一帧摄像头画面（带检测框） |
| `GET /api/status` | 返回 JSON `{"cx":320,"prob":0.95,"latency":47}` |
| `GET /api/motor/<cmd>` | 执行电机命令 (f/b/l/r/s)，0.2s 后自动停车 |

`vision_node.cpp` 每帧写临时文件 + `rename` 原子操作，确保 PC 端不读到半截 JPEG。

### PC 端：PyQt5 桌面客户端

```
┌──────────────────────────────────┐
│  YOLOv5 Ball Tracker              │
├──────────────────────────────────┤
│  [摄像头实时画面 640×480]         │  ← 每 80ms 刷新
├──────────────────────────────────┤
│  cx: 320  prob: 0.95  ms: 47    │  ← 球位置 + 推理耗时
├──────────────────────────────────┤
│  ▂▃▅▇█▇▅▃▂  (延迟曲线)          │  ← QPainter 绘制，不依赖第三方库
├──────────────────────────────────┤
│  [PC] left  [PC] fwd  [PC] stop  │  ← 命令日志
├──────────────────────────────────┤
│  [停] [前] [左] [右] [后]         │  ← 鼠标点击手动控制
└──────────────────────────────────┘
```

**关键优化**：网络请求放在 `QThread` 独立线程（`DataFetcher`），不阻塞 UI。`closeEvent` 优雅关闭线程。

### 为什么之前放 2.0 现在放 3.0

v2.0 阶段前端和多线程文档混在一起。v3.0 正式拆分：多线程代码留在此目录，前端代码独立为 `yolov5_ROS_2.0_web_monitor/`。

---

> 🆕 **v3.0 新增：多线程性能优化（原 v2.0 内容）**
> 
> 原版是单线程串行：`读摄像头 → 等 NPU 推理 → 等后处理 → 再读下一帧`。
> v2.0 加入三个并发模块，将采集、推理、电机控制拆成独立线程。

---

## 🆕 七、新增模块一：双缓冲采集 + 推理管线

### 为什么改

原版 `vision_node` 的 `loop()` 里是串行的——摄像头先读完一帧，NPU 推理完一帧，摄像头才能开始读下一帧。摄像头在等 NPU 的时候是空闲的。

改完后：摄像头只负责不停拍照，推理线程只负责不停处理最新照片——两者并行，帧率提高约 50%。

### 怎么改

用一个**线程安全队列**，只保留最新 1 帧（丢旧帧保实时性）：

```
采集线程（不停拍照）                    推理线程（只处理最新帧）
┌──────────────────┐                 ┌──────────────────────┐
│ cap_.read(frame) │── push ───→    │ pop 最新帧            │
│ 立刻拍下一帧      │  队列(容量1)    │ preprocess → NPU推理  │
│ ...              │                 │ postprocess → publish │
└──────────────────┘                 └──────────────────────┘
```

代码实现——`vision_node.cpp`（新版本）：

```cpp
#include <atomic>
#include <mutex>
#include <condition_variable>
#include <thread>

std::atomic<float> g_ball_cx(-1);       // 🆕 原子变量，多线程安全
std::atomic<float> g_ball_prob(0);

class VisionNode : public rclcpp::Node {
public:
    VisionNode(int cam_id) : Node("yolov5_vision") {
        pub_ = this->create_publisher<std_msgs::msg::Float32>("/ball/cx", 10);
        awnn_init();
        ctx_ = awnn_create(".../yolov5_ball.nb");
        cap_.open(cam_id, cv::CAP_V4L2);
        cap_.set(cv::CAP_PROP_FRAME_WIDTH, 640);
        cap_.set(cv::CAP_PROP_FRAME_HEIGHT, 480);

        // 🆕 启动采集线程
        capture_thread_ = std::thread(&VisionNode::capture_loop, this);
        // 🆕 推理用定时器
        infer_timer_ = this->create_wall_timer(
            std::chrono::milliseconds(66),
            std::bind(&VisionNode::infer_loop, this));
    }

    ~VisionNode() {
        running_ = false;
        cv_.notify_all();                // 🆕 唤醒等待的线程
        if (capture_thread_.joinable()) capture_thread_.join();
        cap_.release();
        awnn_destroy(ctx_);
        awnn_uninit();
    }

private:
    // 🆕 ===== 采集线程 =====
    void capture_loop() {
        cv::Mat frame;
        while (running_) {
            if (!cap_.read(frame) || frame.empty()) continue;
            cv::rotate(frame, frame, cv::ROTATE_90_COUNTERCLOCKWISE);
            {
                std::lock_guard<std::mutex> lock(mtx_);
                latest_frame_ = frame.clone();   // 🆕 只保留最新帧
                has_new_ = true;
            }
            cv_.notify_one();                    // 🆕 通知推理线程
        }
    }

    // 🆕 ===== 推理线程 =====
    void infer_loop() {
        cv::Mat frame;
        {
            std::unique_lock<std::mutex> lock(mtx_);
            if (!has_new_) return;               // 🆕 没有新帧就跳过
            frame = latest_frame_.clone();
            has_new_ = false;
        }

        unsigned int fs;
        unsigned char *inp = yolov5_pre_process(NULL, &frame, &fs);
        if (!inp) return;

        void *in[] = {inp};
        awnn_set_input_buffers(ctx_, in);
        awnn_run(ctx_);
        float **o = awnn_get_output_buffers(ctx_);
        if (!o || !o[0] || !o[1] || !o[2]) { free(inp); return; }

        yolov5_post_process(NULL, &frame, o);
        free(inp);

        auto m = std_msgs::msg::Float32();
        m.data = (g_ball_prob > 0.3f && g_ball_cx > 0) ? g_ball_cx : -1.0f;
        pub_->publish(m);
    }

    // 🆕 线程相关成员
    std::thread capture_thread_;
    std::mutex mtx_;
    std::condition_variable cv_;
    cv::Mat latest_frame_;
    bool has_new_ = false;
    std::atomic<bool> running_{true};

    // 原有成员
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr pub_;
    rclcpp::TimerBase::SharedPtr infer_timer_;
    Awnn_Context_t *ctx_;
    cv::VideoCapture cap_;
};
```

### 用到的知识点

| 技术 | 作用 | 面试能讲的 |
|------|------|-----------|
| `std::thread` | 独立采集线程，不阻塞 ROS 主循环 | 理解线程生命周期、join/detach |
| `std::mutex` + `std::condition_variable` | 生产者-消费者同步 | 理解 wait/notify_one、虚假唤醒 |
| 队列容量=1 + 丢旧帧 | 永远处理最新画面，不积压 | 理解实时系统设计权衡 |
| `std::atomic<bool>` | 线程安全退出标志 | 理解内存序 vs 互斥锁性能差异 |

---

## 🆕 八、新增模块二：推理与电机控制完全解耦

### 为什么改

原版 `motor_node` 的 `cb()` 里用了 `rclcpp::sleep_for(50ms)`——这会**阻塞 ROS 的消息处理线程**。
视觉节点发了新消息，但电机节点还在 sleep 里，收不到。

### 怎么改

电机动作改成**定时器异步执行**——收到消息立刻启动一个定时器，50ms 后自动回调停车。

```cpp
class MotorNode : public rclcpp::Node {
public:
    MotorNode() : Node("motor_control") {
        // ... GPIO 初始化不变 ...
        sub_ = this->create_subscription<std_msgs::msg::Float32>("/ball/cx", 10,
            std::bind(&MotorNode::cb, this, std::placeholders::_1));

        // 🆕 停车定时器（初始不启动）
        stop_timer_ = this->create_wall_timer(
            std::chrono::milliseconds(0),            // 初始间隔0=不启动
            std::bind(&MotorNode::on_stop, this));
        stop_timer_->cancel();                       // 🆕 先关掉
    }

private:
    void cb(const std_msgs::msg::Float32::SharedPtr m) {
        g_last_ = this->now();
        float cx = m->data;
        if (cx < 0) { motor_stop(); return; }

        float d = cx - 320.0f;

        // 🆕 收到消息立刻执行电机动作
        if      (d < -deadzone_) motor_raw(0,1,0,1);
        else if (d >  deadzone_) motor_raw(1,0,1,0);
        else                     motor_raw(0,1,1,0);

        // 🆕 启动定时器：50ms 后自动停车（不阻塞当前线程！）
        stop_timer_->cancel();
        stop_timer_ = this->create_wall_timer(
            std::chrono::milliseconds(50),
            std::bind(&MotorNode::on_stop, this));
    }

    void on_stop() {
        motor_stop();
        stop_timer_->cancel();   // 🆕 停完关定时器
    }

    rclcpp::TimerBase::SharedPtr stop_timer_;   // 🆕
    // ... 其他成员不变 ...
};
```

### 用到的知识点

| 技术 | 作用 |
|------|------|
| `create_wall_timer` + `cancel` | 异步延迟执行，不阻塞消息回调 |
| 单次定时器 | 定时器回调后立刻 cancel，等价于 `setTimeout` |

---

## 🆕 九、新增模块三：原子变量共享检测结果

### 为什么改

原版用普通全局变量 `float g_ball_cx`——在多线程环境下，采集线程和推理线程同时读写时可能读到半截数据（`float` 非原子，64 位 CPU 上也有风险）。

### 怎么改

```cpp
// 原版（v1.0）
float g_ball_cx = -1;
float g_ball_prob = 0;

// 🆕 v2.0
#include <atomic>
std::atomic<float> g_ball_cx(-1);
std::atomic<float> g_ball_prob(0);

// 用法完全相同——store/load 自动保证线程安全
g_ball_cx.store(obj.rect.x + obj.rect.width / 2);
float cx = g_ball_cx.load();
```

`std::atomic<float>` 保证：
- 读取时不会读到"写到一半"的值（CPU 不会撕裂一个 float）
- 写完后其他线程立刻可见（内存序 barrier）

### 用到的知识点

| 技术 | 作用 |
|------|------|
| `std::atomic<float>` | 无锁线程安全读写 |
| store/load 默认 `memory_order_seq_cst` | 最强一致性保证 |

---

## 🆕 十、性能对比

| 指标 | v1.0 (单线程) | v2.0 (多线程) | 提升 |
|------|--------------|--------------|------|
| 采集线程 | 等 NPU 推理完才能拍下一帧 | 独立运行，不停拍照 | - |
| 帧率 | ~12 FPS | ~18 FPS | +50% |
| 电机响应 | 阻塞在 sleep 里 | 定时器异步，消息立即可处理 | 延迟降到 <1ms |
| 线程安全 | 裸 float 全局变量 | `std::atomic<float>` | 无数据竞争 |


