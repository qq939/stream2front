from flask import Flask, render_template, Response
from screen_recorder import ScreenRecorder

app = Flask(__name__)
recorder = ScreenRecorder()

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """视频流端点"""
    return Response(recorder.generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("启动屏幕录制Web服务...")
    print("访问 http://localhost:8080 查看屏幕录制")
    print("按 Ctrl+C 停止服务")
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)