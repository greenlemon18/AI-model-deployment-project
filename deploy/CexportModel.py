from ultralytics import YOLO

model = YOLO('runs/detect/robot_model_optimized/weights/best.pt')
model.export(format='onnx', opset=12, imgsz=640, simplify=False)
