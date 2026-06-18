#ifndef __YOLOV5_POST_PROCESS_H__
#define __YOLOV5_POST_PROCESS_H__

#define DEBUG_POST_SWITCH 1

#ifdef DEBUG_POST_SWITCH
#define DEBUG(fmt, ...) fprintf(stderr, "[DEBUG] %s:%d: " fmt "\n", __func__, __LINE__, ##__VA_ARGS__)
#else
#define DEBUG(fmt, ...) ((void)0)   // 编译期消除
#endif

#ifdef __cplusplus
extern "C" {
#endif

int yolov5_post_process(const char *imagepath, const cv::Mat* image_camera, float **output);

#ifdef __cplusplus
}
#endif

#endif
