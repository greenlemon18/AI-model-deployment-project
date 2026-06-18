"""Orange Pi 板端 HTTP API 服务
提供: /api/status (球位置+耗时), /latest.jpg (摄像头画面), /api/motor/<cmd> (电机控制)
运行: python3 api_server.py
"""
from flask import Flask, send_file, jsonify
import json, subprocess, os

app = Flask(__name__)
BALL_FILE = "/tmp/ball_status.json"

@app.route('/api/status')
def status():
    if os.path.exists(BALL_FILE):
        with open(BALL_FILE) as f:
            return jsonify(json.load(f))
    return jsonify({"cx":-1,"prob":0,"fps":0,"latency":0})

@app.route('/latest.jpg')
def latest():
    return send_file('/tmp/latest.jpg', mimetype='image/jpeg')

@app.route('/api/motor/<cmd>')
def motor(cmd):
    cmds = {
        'f': 'gpio write 8 0;gpio write 9 1;gpio write 13 1;gpio write 14 0',
        'b': 'gpio write 8 1;gpio write 9 0;gpio write 13 0;gpio write 14 1',
        'l': 'gpio write 8 0;gpio write 9 1;gpio write 13 0;gpio write 14 1',
        'r': 'gpio write 8 1;gpio write 9 0;gpio write 13 1;gpio write 14 0',
        's': 'gpio write 8 0;gpio write 9 0;gpio write 13 0;gpio write 14 0',
    }
    cmd_str = cmds.get(cmd, "")
    if cmd_str:
        subprocess.run(f"({cmd_str}) & sleep 0.2;gpio write 8 0;gpio write 9 0;gpio write 13 0;gpio write 14 0",
                       shell=True, timeout=1)
    return 'ok'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8088)
