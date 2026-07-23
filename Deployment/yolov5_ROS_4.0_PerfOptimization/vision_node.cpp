#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float32.hpp>
#include <fstream>
#include <csignal>
#include <cstdio>
#include <opencv2/opencv.hpp>
#include <awnn_lib.h>
#include "yolov5_pre_process.h"
#include "yolov5_post_process.h"

#include <chrono>
using namespace std::chrono;

extern float g_ball_cx;
extern float g_ball_prob;
static volatile int g_shutdown_triggered = 0;
// 信号处理函数：仅通知ROS退出，不操作任何资源
void sigint_handler(int sig)
{
    (void)sig;
    // 已经触发过直接返回，不再重复执行
    if (g_shutdown_triggered)
    {
        return;
    }
    g_shutdown_triggered = 1;
    printf("\n[INFO] 收到终止信号，准备优雅退出...\n");
    rclcpp::shutdown();
}

class VisionNode : public rclcpp::Node {
private:
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr publisher;
    rclcpp::TimerBase::SharedPtr timer;
    Awnn_Context_t   *context;
    cv::VideoCapture  camera;
    cv::Mat           frame;

    void loop() {
        clock_t        start_clock = clock();
        unsigned int   file_size;
        unsigned char *input_data;
        float        **output_buffers;
        float          latency_ms;
        void          *input_pointer_array[1];
        std_msgs::msg::Float32 message;
        std::ofstream  status_file_temp;

        auto total_start = steady_clock::now();
        auto t1 = steady_clock::now();
        if (!camera.read(frame) || frame.empty()) {
            return;
        }
        auto t2 = steady_clock::now();
        
        input_data = yolov5_pre_process(NULL, &frame, &file_size);
        auto t3 = steady_clock::now();
        if (!input_data) {
            return;
        }

        input_pointer_array[0] = input_data;
        awnn_set_input_buffers(context, input_pointer_array);
        awnn_run(context);
        auto t4 = steady_clock::now();
        output_buffers = awnn_get_output_buffers(context);
        if (!output_buffers || !output_buffers[0]
                          || !output_buffers[1]
                          || !output_buffers[2])
        {
            return;
        }
        yolov5_post_process(NULL, &frame, output_buffers);
        auto t5 = steady_clock::now();

        double read_cost = duration<double, std::milli>(t2 - t1).count();
        double pre_cost = duration<double, std::milli>(t3 - t2).count();
        double infer_cost = duration<double, std::milli>(t4 - t3).count();
        double post_push_cost = duration<double, std::milli>(t5 - t4).count();
        double all_cost = duration<double, std::milli>(t5 - total_start).count();

        printf("[TIME] read:%.2f pre:%.2f infer:%.2f post_push:%.2f total:%.2f\n",
            read_cost, pre_cost, infer_cost, post_push_cost, all_cost);

        message.data = (0.3f < g_ball_prob && 0 < g_ball_cx)
                       ? g_ball_cx : -1.0f;
        publisher->publish(message);
    }

public:
    VisionNode(int camera_id) : Node("yolov5_vision") {
        publisher = this->create_publisher<std_msgs::msg::Float32>("/ball/cx", 10);
        awnn_init();
        context = awnn_create("/home/orangepi/ai-sdk/examples/yolov5/model/v3/yolov5_ball.nb");
        camera.open(camera_id, cv::CAP_V4L2);
        camera.set(cv::CAP_PROP_FRAME_WIDTH,  640);
        camera.set(cv::CAP_PROP_FRAME_HEIGHT, 480);

        // 1. 启动ffmpeg基础句柄
        ffmpeg_start();
        // 2. 启动异步推流子线程
        stream_thread_start();
        // 3. 启动预处理缓存队列
        pre_buf_init();

        timer = this->create_wall_timer(std::chrono::milliseconds(80),
            std::bind(&VisionNode::loop, this));
        printf("[INFO] VisionNode 初始化完成\n");
    }

    ~VisionNode() {
        printf("[INFO] 开始释放所有资源\n");
        // 通知推流线程退出循环
        stream_thread_stop();
        // 等待一小段时间让子线程收尾
        std::this_thread::sleep_for(std::chrono::milliseconds(50));

        camera.release();
        ffmpeg_stop();
        pre_buf_release();
        if(context) awnn_destroy(context);
        awnn_uninit();
        printf("[INFO] 全部资源释放完毕\n");
    }
};

int main(int argument_count, char **argument_values) {
    rclcpp::init(argument_count, argument_values);

    // 监听 Ctrl+C 和 kill 信号
    signal(SIGINT, sigint_handler);
    signal(SIGTERM, sigint_handler);

    int camera_id = (1 < argument_count) ? atoi(argument_values[1]) : 0;
    // 局部智能指针持有节点，spin退出后自动析构
    auto node = std::make_shared<VisionNode>(camera_id);

    rclcpp::spin(node);
    return 0;
}