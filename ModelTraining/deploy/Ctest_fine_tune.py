# ========== 1. 环境保护 ==========
import os

os.environ['ULTRALYTICS_OFFLINE'] = '1'  # 强制离线
import ssl

ssl._create_default_https_context = ssl._create_unverified_context  # 修复SSL

# ========== 2. 配置参数 ==========
BEST_PT_PATH = r'E:\Project_AIDeploy\runs\detect\robot_model_optimized\weights\best.pt'
DATA_YAML = r'E:\Project_AIDeploy\train\data.yml'  # 注意现在 data.yml 在 train/ 下

# 微调参数
EPOCHS = 50
BATCH = 16
IMG_SIZE = 640
LR = 0.001
PATIENCE = 20
PROJECT_NAME = 'robot_model_finetuned_final'

# ========== 3. 主程序保护 ==========
if __name__ == '__main__':  # ★ 必须这样保护 ★
    # 检查文件存在
    if not os.path.exists(BEST_PT_PATH):
        raise FileNotFoundError(f"模型文件不存在：{BEST_PT_PATH}")
    if not os.path.exists(DATA_YAML):
        raise FileNotFoundError(f"数据集配置文件不存在：{DATA_YAML}")

    print(f"✅ 模型路径：{BEST_PT_PATH}")
    print(f"✅ 数据集配置：{DATA_YAML}")

    from ultralytics import YOLO

    model = YOLO(BEST_PT_PATH)

    results = model.train(
        data=DATA_YAML,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH,
        lr0=LR,
        lrf=LR,
        patience=PATIENCE,
        cos_lr=True,
        close_mosaic=5,
        name=PROJECT_NAME,
        mosaic=1.0,
        mixup=0.1,
        degrees=5.0,
        translate=0.1,
        scale=0.5,
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.3,
        erasing=0.3,
        device='cuda' if __import__('torch').cuda.is_available() else 'cpu',
        workers=4,
    )
    print("🎉 微调完成！")
