from ultralytics import YOLO


def main():
    from ultralytics import YOLO

    if __name__ == '__main__':
        # 1. 加载预训练模型（迁移学习，收敛快效果好）
        model = YOLO('yolov8n.pt')  # 'n' 就是 nano 版本，首次运行会自动下载

        results = model.train(
            data='data.yml',
            epochs=300,
            imgsz=640,
            batch=16,
            patience=0,  # 关闭早停，跑满300轮
            cos_lr=True,  # 余弦学习率
            lr0=0.007,  # 降低初始学习率
            lrf=0.007,  # 降低最终学习率
            close_mosaic=15,  # 最后15轮关闭mosaic
            name='robot_model_optimized',

            # 增强的数据增强
            mosaic=1.0,
            mixup=0.2,
            copy_paste=0.05,
            degrees=5.0,
            translate=0.15,
            scale=0.5,
            shear=2.0,
            perspective=0.0008,
            hsv_h=0.02,
            hsv_s=0.8,
            hsv_v=0.5,
            erasing=0.5,
        )


if __name__ == '__main__':
    main()
