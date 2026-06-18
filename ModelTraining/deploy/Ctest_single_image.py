import cv2
import numpy as np
import onnxruntime as ort

MODEL_PATH = 'runs/detect/robot_model_optimized/weights/best.onnx'
CONF_THRESHOLD = 0.1

session = ort.InferenceSession(MODEL_PATH, providers=['CPUExecutionProvider'])
input_name = session.get_inputs()[0].name
output_names = [o.name for o in session.get_outputs()]

# 读取一张训练图片（比如 dataset/images/train/ 里随便选一张）
img = cv2.imread('dataset/images/train/frame_000046.jpg')
orig_h, orig_w = img.shape[:2]

# 预处理
blob = cv2.resize(img, (640, 640))
blob = cv2.cvtColor(blob, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
blob = np.transpose(blob, (2, 0, 1))[np.newaxis, ...]

# 推理
outputs = session.run(output_names, {input_name: blob})[0][0]  # (5, 8400)
preds = outputs.T                                              # (8400, 5)

# 打印最大置信度
print("最大置信度:", preds[:, 4].max())

# 过滤并画框
mask = preds[:, 4] > CONF_THRESHOLD
preds = preds[mask]
if len(preds):
    boxes_xywh = preds[:, :4]
    boxes = np.zeros_like(boxes_xywh)
    boxes[:, 0] = boxes_xywh[:, 0] - boxes_xywh[:, 2] / 2
    boxes[:, 1] = boxes_xywh[:, 1] - boxes_xywh[:, 3] / 2
    boxes[:, 2] = boxes_xywh[:, 0] + boxes_xywh[:, 2] / 2
    boxes[:, 3] = boxes_xywh[:, 1] + boxes_xywh[:, 3] / 2
    for box, conf in zip(boxes, preds[:, 4]):
        x1, y1, x2, y2 = box * [orig_w/640, orig_h/640, orig_w/640, orig_h/640]
        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0,255,0), 2)
        print(f"框: ({x1:.0f},{y1:.0f}) -> ({x2:.0f},{y2:.0f}), 置信度: {conf:.2f}")
    cv2.imshow('test', img)
    cv2.waitKey(0)
else:
    print("无检测结果")
