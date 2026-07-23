/*
 * Company:    AW
 * Author:     Penng
 * Date:    2022/06/28
 */

#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <iostream>
#include <stdio.h>
#include <vector>
#include <cmath>
#include "yolov5_post_process.h"
#include "yolov5_pre_process.h"
using namespace std;


static const size_t INPUT_BUF_SIZE = MODEL_W * MODEL_H * MODEL_CH;

// 全局复用buffer，只分配一次
static unsigned char* g_input_buffer = nullptr;

// 全局预分配letterbox画布，只初始化1次，避免循环内频繁分配释放
static cv::Mat g_letterbox_buf(MODEL_H, MODEL_W, CV_8UC3, cv::Scalar(127, 127, 127));

void get_input_data(const char* image_file, const cv::Mat* sampleinput, unsigned char* input_data, int letterbox_rows, int letterbox_cols,
		const float* mean, const float* scale)
{
    cv::Mat img;
    cv::Mat sample;
    if (image_file != NULL)
    {
        sample = cv::imread(image_file, 1);
        if (sample.empty()) {
            DEBUG("Failed to load image: %s\n", image_file);
            return;
        }
    }
    else if (sampleinput != nullptr) {
        sample = *sampleinput;
    } else {
        DEBUG("No input source provided.\n");
        return;
    }

    if (sample.channels() == 1)
        cv::cvtColor(sample, img, cv::COLOR_GRAY2RGB);
    else
        cv::cvtColor(sample, img, cv::COLOR_BGR2RGB);

    /* letterbox process to support different letterbox size */
    float scale_letterbox;
    int resize_rows;
    int resize_cols;
    if ((letterbox_rows * 1.0 / img.rows) < (letterbox_cols * 1.0 / img.cols))
    {
        scale_letterbox = letterbox_rows * 1.0 / img.rows;
    }
    else
    {
        scale_letterbox = letterbox_cols * 1.0 / img.cols;
    }
    resize_cols = int(scale_letterbox * img.cols);
    resize_rows = int(scale_letterbox * img.rows);

    // 优化1：使用最快邻近插值，替代默认双线性
    cv::resize(img, img, cv::Size(resize_cols, resize_rows), 0, 0, cv::INTER_NEAREST);

    // 复用全局画布，每次重置填充灰色边框
    g_letterbox_buf.setTo(cv::Scalar(127, 127, 127));
    int top = (letterbox_rows - resize_rows) / 2;
    int left = (letterbox_cols - resize_cols) / 2;
    img.copyTo(g_letterbox_buf(cv::Rect(left, top, resize_cols, resize_rows)));

    // 优化2：删除三重for循环，split分离通道 + memcpy批量拷贝（硬件加速）
    std::vector<cv::Mat> chs;
    cv::split(g_letterbox_buf, chs);
    size_t plane_size = (size_t)MODEL_W * MODEL_H;
    memcpy(input_data, chs[0].data, plane_size);
    memcpy(input_data + plane_size, chs[1].data, plane_size);
    memcpy(input_data + plane_size * 2, chs[2].data, plane_size);
}

int pre_buf_init()
{
    if (g_input_buffer != nullptr)
        return 0;
    g_input_buffer = (unsigned char*)malloc(INPUT_BUF_SIZE);
    if (!g_input_buffer)
    {
        printf("pre buffer malloc failed\n");
        return -1;
    }
    return 0;
}

void pre_buf_release()
{
    if (g_input_buffer)
    {
        free(g_input_buffer);
        g_input_buffer = nullptr;
    }
}

extern "C"{
unsigned char *yolov5_pre_process(const char* imagepath, const cv::Mat* bgr, unsigned int *file_size)
{
    DEBUG("preprocess start.");

    const float mean[3] = {0, 0, 0};
    const float scale[3] = {0.0039216, 0.0039216, 0.0039216};

    if (!g_input_buffer)
    {
        printf("pre buffer not init!\n");
        return nullptr;
    }
    *file_size = INPUT_BUF_SIZE;

    if (imagepath == NULL && bgr == NULL)
    {
        DEBUG("No valid input , stop preprocess.\n");
        return NULL;
    }
    
    get_input_data(imagepath, bgr, g_input_buffer, MODEL_H, MODEL_W, mean, scale);

    return g_input_buffer;
}
}

