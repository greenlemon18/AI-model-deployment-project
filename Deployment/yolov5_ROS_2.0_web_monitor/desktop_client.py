"""PC monitor for YOLOv5 ball tracker"""
import sys, requests, warnings
warnings.filterwarnings('ignore')
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor

IP = "192.168.1.48"

class DataFetcher(QThread):
    data_ready = pyqtSignal(dict)
    def __init__(self, ip):
        super().__init__()
        self.ip = ip
        self.running = True
    def run(self):
        while self.running:
            try:
                r = requests.get(f"http://{self.ip}:8088/api/status", timeout=1)
                data = r.json()
                r2 = requests.get(f"http://{self.ip}:8088/latest.jpg", timeout=1)
                data["_img"] = r2.content
                self.data_ready.emit(data)
            except:
                pass
            self.msleep(80)

class LatencyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.history = [0]
        self.setFixedHeight(100)
    def add(self, v):
        self.history.append(v)
        if len(self.history) > 100: self.history.pop(0)
        self.update()
    def paintEvent(self, _):
        if len(self.history) < 2: return
        try:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            p.fillRect(self.rect(), QColor(30,30,30))
            w, h = self.width(), self.height()
            mm = max(self.history) or 1
            pen = QPen(QColor(0,255,0), 2)
            p.setPen(pen)
            for i in range(1, len(self.history)):
                x1 = (i-1)*w//100; y1 = h - int(self.history[i-1]*h/mm)
                x2 = i*w//100;     y2 = h - int(self.history[i]*h/mm)
                p.drawLine(x1,y1,x2,y2)
            p.setPen(QPen(QColor(100,100,100), 1))
            p.drawText(5,15,f"max: {mm:.0f}ms  now: {self.history[-1]:.0f}ms")
            p.end()
        except: pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLOv5 Ball Tracker")
        self.cam_label = QLabel("Waiting...")
        self.cam_label.setFixedSize(640, 480)
        self.cam_label.setStyleSheet("background:black;color:gray;")
        self.status_bar = QLabel("cx: --  prob: --")
        self.status_bar.setStyleSheet("font-size:14px;padding:5px;")
        self.latency = LatencyWidget()
        self.cmd_log = QTextEdit()
        self.cmd_log.setReadOnly(True)
        self.cmd_log.setMaximumHeight(80)
        self.cmd_log.setStyleSheet("background:#1a1a1a;color:#0f0;font-size:12px;")
        btn_layout = QHBoxLayout()
        for name, cmd, color in [("stop","s","red"),("fwd","f","green"),("left","l","blue"),("right","r","blue"),("back","b","orange")]:
            btn = QPushButton(name)
            btn.setStyleSheet(f"font-size:18px;padding:15px;background:{color};color:white;")
            btn.clicked.connect(lambda _,c=cmd: self.send(c))
            btn_layout.addWidget(btn)
        layout = QVBoxLayout()
        layout.addWidget(self.cam_label)
        layout.addWidget(self.status_bar)
        layout.addWidget(self.latency)
        layout.addWidget(self.cmd_log)
        layout.addLayout(btn_layout)
        w = QWidget(); w.setLayout(layout); self.setCentralWidget(w)
        self.fetcher = DataFetcher(IP)
        self.fetcher.data_ready.connect(self.handle_data)
        self.fetcher.start()

    def send(self, cmd):
        names = {"f":"fwd","b":"back","l":"left","r":"right","s":"stop"}
        try:
            requests.get(f"http://{IP}:8088/api/motor/{cmd}", timeout=1)
            self.cmd_log.append(f"[PC] {names.get(cmd,cmd)}")
        except: pass

    def handle_data(self, data):
        try:
            pix = QPixmap(); pix.loadFromData(data.get("_img", b""))
            if not pix.isNull(): self.cam_label.setPixmap(pix.scaled(640, 480))
        except: pass
        try:
            self.status_bar.setText(
                f"cx: {data.get('cx',0):.0f}  prob: {data.get('prob',0):.2f}  "
                f"ms: {data.get('latency',0):.0f}")
            self.latency.add(data.get("latency", 0))
        except: pass

    def closeEvent(self, e):
        self.fetcher.running = False
        self.fetcher.wait(2000)
        e.accept()

if __name__ == '__main__':
    import traceback
    try:
        app = QApplication(sys.argv)
        w = MainWindow()
        w.show()
        app.exec_()
    except:
        traceback.print_exc()
        input("Press Enter to close")
