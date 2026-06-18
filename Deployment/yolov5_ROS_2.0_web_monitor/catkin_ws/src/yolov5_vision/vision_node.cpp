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
public:
    VisionNode(int cam_id) : Node("yolov5_vision") {
        pub_ = this->create_publisher<std_msgs::msg::Float32>("/ball/cx", 10);
        awnn_init();
        ctx_ = awnn_create("/home/orangepi/ai-sdk/examples/yolov5/model/v3/yolov5_ball.nb");
        cap_.open(cam_id, cv::CAP_V4L2);
        cap_.set(cv::CAP_PROP_FRAME_WIDTH,640); cap_.set(cv::CAP_PROP_FRAME_HEIGHT,480);
        timer_ = this->create_wall_timer(std::chrono::milliseconds(80), std::bind(&VisionNode::loop,this));
    }
    ~VisionNode() { cap_.release(); awnn_destroy(ctx_); awnn_uninit(); }
private:
    void loop() 
    {
        clock_t t0 = clock();
        
        if (!cap_.read(frame_) || frame_.empty()) return;
        unsigned int fs; 
        unsigned char *inp = yolov5_pre_process(NULL, &frame_, &fs);
        if(!inp) return;
        void *in[]={inp}; 
        awnn_set_input_buffers(ctx_, in); awnn_run(ctx_);
        float **o = awnn_get_output_buffers(ctx_);
        if(!o||!o[0]||!o[1]||!o[2]){free(inp);return;}
        yolov5_post_process(NULL, &frame_, o); free(inp);
        
        auto m = std_msgs::msg::Float32();
        m.data = (g_ball_prob > 0.3f && g_ball_cx > 0) ? g_ball_cx : -1.0f;
        pub_->publish(m);
        
        // 临时文件+改名（原子操作）
        rename("/tmp/result.png", "/tmp/latest.jpg");
        
        float ms = (float)(clock() - t0) * 1000 / CLOCKS_PER_SEC;
        std::ofstream js("/tmp/ball_status_tmp.json");
        js << "{\"cx\":" << g_ball_cx << ",\"prob\":" << g_ball_prob << ",\"latency\":" << ms << "}";
        js.close();
        rename("/tmp/ball_status_tmp.json", "/tmp/ball_status.json");
    }
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr pub_;
    rclcpp::TimerBase::SharedPtr timer_;
    Awnn_Context_t *ctx_; cv::VideoCapture cap_; cv::Mat frame_;
};

int main(int argc, char**argv) {
    rclcpp::init(argc,argv);
    int cam_id = (argc > 1) ? atoi(argv[1]) : 0;
    rclcpp::spin(std::make_shared<VisionNode>(cam_id));
    return 0;
}
