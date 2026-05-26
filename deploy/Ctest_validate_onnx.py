import cv2
import numpy as np
import onnxruntime as ort

# ---------- 配置 ----------
MODEL_PATH = 'runs/detect/robot_model_optimized/weights/best.onnx'
CONF_THRESHOLD = 0.6          # 置信度阈值（调低到0.35）
IOU_THRESHOLD = 0.45           # NMS的IoU阈值（调低到0.45，合并重叠框更积极）
INPUT_SIZE = (640, 640)
# --------------------------

class YOLOv8ONNX:
    def __init__(self, model_path, conf=0.35, iou=0.45):
        self.conf = conf
        self.iou = iou
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [o.name for o in self.session.get_outputs()]

    def preprocess(self, frame):
        """BGR → RGB → resize → normalize → CHW → batch"""
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, INPUT_SIZE)
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)
        return img

    def nms(self, boxes, scores):
        """使用OpenCV NMS"""
        if len(boxes) == 0:
            return []
        indices = cv2.dnn.NMSBoxes(
            boxes.tolist(), scores.tolist(),
            score_threshold=self.conf,
            nms_threshold=self.iou
        )
        if len(indices) == 0:
            return []
        return indices.flatten()

    def postprocess(self, outputs, original_shape):
        """解析YOLOv8输出，坐标缩放回原图"""
        preds = outputs[0][0]               # (5, 8400)
        preds = preds.T                     # (8400, 5)

        # 先用置信度快速过滤一轮
        keep = preds[:, 4] > self.conf
        preds = preds[keep]

        if len(preds) == 0:
            return []

        # cx, cy, w, h → x1, y1, x2, y2（640尺度）
        cx, cy, w, h = preds[:, 0], preds[:, 1], preds[:, 2], preds[:, 3]
        x1 = cx - w / 2
        y1 = cy - h / 2
        x2 = cx + w / 2
        y2 = cy + h / 2

        boxes_640 = np.stack([x1, y1, x2, y2], axis=1)
        scores = preds[:, 4]

        # NMS
        keep_indices = self.nms(boxes_640, scores)

        # 坐标缩放回原图尺寸
        orig_h, orig_w = original_shape
        scale_x = orig_w / INPUT_SIZE[0]
        scale_y = orig_h / INPUT_SIZE[1]

        detections = []
        for i in keep_indices:
            bx1 = int(boxes_640[i][0] * scale_x)
            by1 = int(boxes_640[i][1] * scale_y)
            bx2 = int(boxes_640[i][2] * scale_x)
            by2 = int(boxes_640[i][3] * scale_y)
            detections.append({
                'bbox': [bx1, by1, bx2, by2],
                'confidence': float(scores[i])
            })
        return detections

    def run(self, frame):
        original_shape = frame.shape[:2]
        input_tensor = self.preprocess(frame)
        outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
        return self.postprocess(outputs, original_shape)


# ==================== 主程序 ====================
if __name__ == '__main__':
    detector = YOLOv8ONNX(MODEL_PATH, CONF_THRESHOLD, IOU_THRESHOLD)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("摄像头已开启，按 'q' 退出...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头画面")
            break

        detections = detector.run(frame)

        # 画框
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            conf = det['confidence']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'{conf:.2f}', (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow('ONNX Model Validation', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()