import cv2, os, random, shutil

src = r"E:\Project_AIDeploy\Yolov5\AGetDate\input_video.mp4"
out = r"E:\Project_AIDeploy\Yolov5\datasets\ball"
N = 164

for d in ["images/train", "images/val", "labels/train", "labels/val"]:
    os.makedirs(out + "/" + d, exist_ok=True)

cap = cv2.VideoCapture(src)
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
interval = max(1, total // N)

frames = []
for i in range(N):
    cap.set(cv2.CAP_PROP_POS_FRAMES, min(i * interval, total - 1))
    ret, f = cap.read()
    if not ret:
        break
    name = f"img_{i:04d}.jpg"
    cv2.imwrite(out + "/images/" + name, f)
    frames.append(name)
cap.release()
print(f"Extracted {len(frames)} frames")

random.seed(42)
random.shuffle(frames)
split = int(len(frames) * 0.8)
for s, names in [("train", frames[:split]), ("val", frames[split:])]:
    for fn in names:
        shutil.move(out + "/images/" + fn, out + f"/images/{s}/" + fn)
    print(f"{s}: {len(names)}")

yaml = "train: ./images/train\nval: ./images/val\nnc: 1\nnames: [\"ball\"]\n"
open(out + "/ball.yaml", "w").write(yaml)
print("Done!")
