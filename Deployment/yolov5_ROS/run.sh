#!/bin/sh
cd /home/orangepi/ai-sdk/examples/yolov5/build

#rm -rf * && cmake ..  && make -j4 && ./yolov5
echo "[INFO] Starting yolov5 at $(date)"
./yolov5
echo "[INFO] yolov5 exited at $(date)"
