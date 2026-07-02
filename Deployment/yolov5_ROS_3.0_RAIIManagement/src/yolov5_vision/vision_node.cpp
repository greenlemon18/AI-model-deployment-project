#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float32.hpp>
#include <fstream>
#include <opencv2/opencv.hpp>
#include <awnn_lib.h>
#include "yolov5_pre_process.h"
#include "yolov5_post_process.h"

extern float g_ball_cx;
extern float g_ball_prob;

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

        if (!camera.read(frame) || frame.empty()) {
            return;
        }

        input_data = yolov5_pre_process(NULL, &frame, &file_size);
        if (!input_data) {
            return;
        }

        input_pointer_array[0] = input_data;
        awnn_set_input_buffers(context, input_pointer_array);
        awnn_run(context);
        output_buffers = awnn_get_output_buffers(context);
        if (!output_buffers || !output_buffers[0]
                          || !output_buffers[1]
                          || !output_buffers[2])
        {
            free(input_data);
            return;
        }
        yolov5_post_process(NULL, &frame, output_buffers);
        free(input_data);

        message.data = (0.3f < g_ball_prob && 0 < g_ball_cx)
                       ? g_ball_cx : -1.0f;
        publisher->publish(message);

        rename("/tmp/result.png", "/tmp/latest.jpg");

        latency_ms = (float)(clock() - start_clock) * 1000 / CLOCKS_PER_SEC;
        status_file_temp.open("/tmp/ball_status_tmp.json");
        status_file_temp << "{\"cx\":" << g_ball_cx
                         << ",\"prob\":" << g_ball_prob
                         << ",\"latency\":" << latency_ms << "}";
        status_file_temp.close();
        rename("/tmp/ball_status_tmp.json", "/tmp/ball_status.json");
    }

public:
    VisionNode(int camera_id) : Node("yolov5_vision") {
        publisher = this->create_publisher<std_msgs::msg::Float32>("/ball/cx", 10);
        awnn_init();
        context = awnn_create("/home/orangepi/ai-sdk/examples/yolov5/model/v3/yolov5_ball.nb");
        camera.open(camera_id, cv::CAP_V4L2);
        camera.set(cv::CAP_PROP_FRAME_WIDTH,  640);
        camera.set(cv::CAP_PROP_FRAME_HEIGHT, 480);
        timer = this->create_wall_timer(std::chrono::milliseconds(80),
            std::bind(&VisionNode::loop, this));
    }
    ~VisionNode() {
        camera.release();
        awnn_destroy(context);
        awnn_uninit();
    }
};

int main(int argument_count, char **argument_values) {
    rclcpp::init(argument_count, argument_values);
    int camera_id = (1 < argument_count) ? atoi(argument_values[1]) : 0;
    rclcpp::spin(std::make_shared<VisionNode>(camera_id));
    return 0;
}

