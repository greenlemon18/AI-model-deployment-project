#ifndef __YOLOV5_POST_PROCESS_H__
#define __YOLOV5_POST_PROCESS_H__

//#define DEBUG_POST_SWITCH 1

#ifdef DEBUG_POST_SWITCH
#define DEBUG(fmt, ...) fprintf(stderr, "[DEBUG] %s:%d: " fmt "\n", __func__, __LINE__, ##__VA_ARGS__)
#else
#define DEBUG(fmt, ...) ((void)0)   // 编译期消除
#endif

#ifdef __cplusplus
extern "C" {
#endif

int yolov5_post_process(const char *imagepath, const cv::Mat* image_camera, float **output);

// 新增异步推流对外接口
void stream_thread_start();

void stream_thread_stop();

void push_image_to_stream(const cv::Mat& src);

void ffmpeg_start();

void ffmpeg_stop();

// 推流队列最大缓存帧数
#define MAX_QUEUE_SIZE 2
// 输出图像分辨率，和双缓冲画布尺寸保持一致
#define FRAME_W 640
#define FRAME_H 480

#ifdef __cplusplus
}
#endif

#endif
