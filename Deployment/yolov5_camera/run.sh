#!/bin/sh
cd /home/orangepi/ai-sdk/examples/yolov5/build

while true; do
    echo "[WATCHDOG] Starting yolov5 at $(date)"
    ./yolov5
    echo "[WATCHDOG] Crashed, restarting in 3s..."
    sleep 3
done
