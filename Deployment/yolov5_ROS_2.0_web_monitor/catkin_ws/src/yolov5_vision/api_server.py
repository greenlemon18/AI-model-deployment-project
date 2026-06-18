"""Orange Pi 板端 HTTP API 服务"""
from flask import Flask, send_file, jsonify
import json, subprocess, os, time
import logging

app = Flask(__name__)
BALL_FILE = "/tmp/ball_status.json"
NAMES = {"f":"前进","b":"后退","l":"左转","r":"右转","s":"停止"}

@app.route('/api/status')
def status():
    if os.path.exists(BALL_FILE):
        with open(BALL_FILE) as f:
            return jsonify(json.load(f))
    return jsonify({"cx":-1,"prob":0,"latency":0})

@app.route('/latest.jpg')
def latest():
    return send_file('/tmp/latest.jpg', mimetype='image/jpeg')

@app.route('/api/motor/<cmd>')
def motor(cmd):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] PC 命令: {NAMES.get(cmd, cmd)}", flush=True)
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
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    print("API server started :8088", flush=True)
    app.run(host='0.0.0.0', port=8088)

