#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <ros/ros.h>
#include <std_msgs/Float32MultiArray.h>
#include <opencv2/opencv.hpp>
#include <awnn_lib.h>
#include "yolov5_pre_process.h"
#include "yolov5_post_process.h"
#include <fcntl.h>

static volatile sig_atomic_t g_running = 1;
static void sig_handler(int) { g_running = 0; }

#define DETECTFRAMENUM  0xffffffff
int main(int argc, char **argv) {
    unsigned int fsize;                // 图片数据大小
    unsigned char *input = NULL;       // 输入数据指针（先初始化为 NULL）
    float **out = NULL;                // NPU 输出指针
    cv::Mat frame;                     // 当前帧
    int fcnt = 0;                      // 帧计数器
    void *in[1];                       // 输入缓冲区数组（稍后赋值）
    clock_t t0;                        // 计时起点
    float elapsed_ms;                  // 耗时（毫秒）
    int cam_id;                        // 摄像头ID
    Awnn_Context_t *ctx;

    /* ROS publisher */
    std_msgs::Float32MultiArray msg;
    ros::Rate rate(15);
    ros::NodeHandle nh;
    ros::Publisher  pub;

    /*if (argc < 3) {
        DEBUG("Usage: %s <nbg> <camera_id>\n", argv[0]);
        return -1;
    }*/

    //const char *nbg = argv[1];
    // cam_id = atoi(argv[2]);
    const char *nbg = "../model/v3/yolov5_ball.nb";
    cam_id = 0;

    signal(SIGINT,  sig_handler);
    signal(SIGTERM, sig_handler);

    ros::init(argc, argv, "yolov5_vision");
    pub = nh.advertise<std_msgs::Float32MultiArray>("/ball/position", 10);

    DEBUG("INIT");
    awnn_init();
    DEBUG("CREATE");
    ctx = awnn_create(nbg);
    if (ctx == NULL) {
        DEBUG("awnn_create failed!\n");
        awnn_uninit();
        return -1;
    }
    DEBUG("OPEN CAMERA");
    /* 初始化摄像头并定义分辨率 */
    cv::VideoCapture cap(cam_id, cv::CAP_V4L2);
    cap.set(cv::CAP_PROP_FRAME_WIDTH,  640);
    cap.set(cv::CAP_PROP_FRAME_HEIGHT, 480);
    if (!cap.isOpened()) {
        DEBUG("Camera %d open failed\n", cam_id);
        awnn_destroy(ctx);
        awnn_uninit();
        return -1;
    }

    while (ros::ok() && g_running && cap.read(frame) && fcnt < DETECTFRAMENUM) {
        if (frame.empty()) continue;
        clock_t t0 = clock();

        // 前处理（复用現有逻辑）
        input = yolov5_pre_process(NULL, &frame, &fsize);
        if (input == NULL)
        {
            DEBUG("get valid photo!");
            continue;
        }
        // 设置输入缓冲区并推理
        in[0] = input;                     // 此时 input 已有效
        // NPU 推理
        awnn_set_input_buffers(ctx, in);
        awnn_run(ctx);
        out = awnn_get_output_buffers(ctx);

        // 后处理（和图片版本完全相同）
        yolov5_post_process(NULL, &frame, out);  // ← 需新增：直接画到 cv::Mat 上的版本
        out = awnn_get_output_buffers(ctx);
        if (out == NULL || out[0] == NULL || out[1] == NULL || out[2] == NULL) {
            DEBUG("no output!\n");
            free(input);
            break;
        }
        
        free(input);
        input = NULL;

        elapsed_ms = (float)(clock() - t0) * 1000.0f / CLOCKS_PER_SEC;
        DEBUG("Frame %4d | %.1f ms\n", fcnt++, elapsed_ms);

        /* publishment */
        if (g_ball_prob > 0.3 && g_ball_cx > 0)
        {
            msg.data = {g_ball_cx, g_ball_prob};
        } else {
            msg.data = {-1, 0};
        }
        pub.publish(msg);
        ros::spinOnce();
        rate.sleep();
    }

    cap.release();
    awnn_destroy(ctx);
    awnn_uninit();
     
    return 0;
}