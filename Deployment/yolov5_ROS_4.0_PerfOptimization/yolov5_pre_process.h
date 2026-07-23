#ifndef __YOLOV5_PRE_PROCESS_H__
#define __YOLOV5_PRE_PROCESS_H__

#ifdef __cplusplus
extern "C" {
#endif

unsigned char* yolov5_pre_process(const char* imagepath, const cv::Mat* bgr, unsigned int *file_size);

int pre_buf_init();

void pre_buf_release();

// 模型输入固定尺寸 640*640*3
#define MODEL_W 640
#define MODEL_H 640
#define MODEL_CH 3

#ifdef __cplusplus
}
#endif

#endif
