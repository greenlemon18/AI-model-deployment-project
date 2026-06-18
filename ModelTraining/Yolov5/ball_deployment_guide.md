# YOLOv5 Ball Detection - Full Pipeline from Training to NPU Deployment

> Project: E:\Project_AIDeploy\Yolov5
> Target: Orange Pi Zero 3W (Allwinner H618, NPU v3)
> Model: YOLOv5s Single Class (ball)

## 1. Environment

| Component | Version |
|-----------|---------|
| Python | 3.10.8 (conda: pytorch1_12) |
| PyTorch | 2.7.1+cu118 (CUDA 11.8, RTX 3050) |
| YOLOv5 | master (2026-06-03) |
| OpenCV | 4.13.0 |

## 2. Dataset Construction

### 2.1 Video Frame Extraction
16-second video -> 164 frames via OpenCV evenly spaced seeking.

### 2.2 Train/Val Split (random shuffle)
- Train: 131 images (80%), 70 with ball annotations
- Val: 33 images (20%), 21 with ball annotations

### 2.3 Labeling (labelMe)
Circles or rectangles drawn around balls. Saved as JSON.

### 2.4 JSON -> YOLO Format Conversion
Custom script handles both shape types:
- circle: center + radius -> bounding square
- rectangle: two corners -> bounding box
- All coordinates normalized to [0,1]

## 3. Training

### 3.1 Command
```
python train.py --img 640 --batch 16 --epochs 100 \
    --data ball.yaml --weights yolov5s.pt --device 0
```

### 3.2 Metrics (24 epochs)

| Metric | Value |
|--------|-------|
| GIoU loss | 0.021 |
| cls loss | 0.078 |
| Precision | 0.997 |
| Recall | 0.875 |
| mAP@0.5 | 0.874 |
| mAP@0.5:0.95 | 0.465 |

## 4. ONNX Export + Node ID Discovery

```
python export.py --weights best.pt --include onnx --img 640
```

Detection head node IDs (for separate quantization):
| Head | Stride | Grid | Node ID |
|------|--------|------|---------|
| P8 | 8 | 80x80 | 219 |
| P16 | 16 | 40x40 | 240 |
| P32 | 32 | 20x20 | 261 |

## 5. NPU Model Conversion (SDK)

inputs_outputs.txt:
```
--inputs images --input-size-list '3,640,640' --outputs '219 240 261'
```

```bash
source env.sh v3
./convert_export.sh ball_yolov5 uint8 t536
```
Pipeline: import -> channel_mean -> quantize -> export (NB)

## 6. Board Deployment

### 6.1 C Code Flow
```c
awnn_init();
awnn_create(nbg);
pre_process(input);  // BGR->RGB, resize, letterbox, HWC->NCHW
awnn_set_input_buffers(context);
awnn_run(context);
outputs = awnn_get_output_buffers(context);  // 3 tensors
post_process();  // anchor decode + NMS + draw
```

## 7. Key Technical Challenges

### 7.1 Quantization of Concat Outputs
YOLOv8 outputs [bbox(4ch), class(1ch)]=concat=[1,5,8400].
Single quantization scale dominated by bbox (0-640), clas (-5~5) zeroed out.
Fix: Use YOLOv5 with 3 independent output heads, each quantized separately.

### 7.2 Standard YOLOv5 Export Also Concat
Default export.py produces concat. Use --outputs with node IDs to keep heads separate.

### 7.3 Input Normalization
SDK inputmeta.yml bakes in scale=1/255. Board code sends uint8 0-255.
Do NOT manually divide by 255 in C preprocess.

## 8. File Structure

```
E:\Project_AIDeploy\Yolov5\
- datasets/ball/          Dataset (images + labels + ball.yaml)
- runs/yolov5s_ball2/     Training results (best.pt, best.onnx)
- yolov5/                 YOLOv5 source
- train_yolov5_ball.py    Training archive script
- ball_deployment_guide.md  This document
```