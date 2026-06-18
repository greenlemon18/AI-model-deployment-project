"""PC 端桌面客户端 — YOLOv5 球体检测监控面板
需要: pip install pyqt5 requests pyqtgraph
"""
import sys, requests
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap
import pyqtgraph as pg

PI_IP = "orangepizero3w.local"  # 改成板子IP

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLOv5 Ball Tracker - Monitor")

        # ===== 摄像头画面 =====
        self.cam_label = QLabel("等待连接...")
        self.cam_label.setFixedSize(640, 480)
        self.cam_label.setStyleSheet("background:black;color:gray;")

        # ===== 状态栏 =====
        self.status_bar = QLabel("cx: --  prob: --  FPS: --  延迟: --ms")
        self.status_bar.setStyleSheet("font-size:14px;padding:5px;")

        # ===== 推理耗时曲线 =====
        self.plot = pg.PlotWidget()
        self.plot.setLabel('left', '延迟', units='ms')
        self.plot.setLabel('bottom', '帧')
        self.plot.setYRange(0, 200)
        self.curve = self.plot.plot(pen='y')
        self.history = []

        # ===== 电机控制按钮 =====
        btn_layout = QHBoxLayout()
        btns = [("⏹ 停止","s","red"),("▲ 前进","f","green"),("◀ 左转","l","blue"),
                ("▶ 右转","r","blue"),("▼ 后退","b","orange")]
        for name, cmd, color in btns:
            btn = QPushButton(name)
            btn.setStyleSheet(f"font-size:18px;padding:15px;background:{color};color:white;")
            btn.clicked.connect(lambda _, c=cmd: requests.get(f"http://{PI_IP}:8088/api/motor/{c}", timeout=1))
            btn_layout.addWidget(btn)

        # ===== 布局 =====
        layout = QVBoxLayout()
        layout.addWidget(self.cam_label)
        layout.addWidget(self.status_bar)
        layout.addWidget(self.plot)
        layout.addLayout(btn_layout)

        w = QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)

        # ===== 定时刷新每 200ms =====
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(200)

    def refresh(self):
        try:
            # 摄像头
            r = requests.get(f"http://{PI_IP}:8088/latest.jpg", timeout=1)
            pix = QPixmap()
            pix.loadFromData(r.content)
            self.cam_label.setPixmap(pix.scaled(640, 480))

            # 状态
            s = requests.get(f"http://{PI_IP}:8088/api/status", timeout=1).json()
            self.status_bar.setText(
                f"cx: {s['cx']:.0f}  prob: {s['prob']:.2f}  FPS: {s.get('fps','--')}  延迟: {s.get('latency',0):.0f}ms")

            # 曲线
            self.history.append(s.get('latency', 0))
            if len(self.history) > 100: self.history.pop(0)
            self.curve.setData(self.history)
        except:
            self.status_bar.setText("连接失败...")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
