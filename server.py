#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
屏幕录制服务端
提供Web界面和API接口，接收客户端推流
"""

from flask import Flask, Response, render_template, jsonify, request
import cv2
import io
import threading
import time
import queue
import numpy as np
from datetime import datetime

app = Flask(__name__)

# 全局变量
frame_queue = queue.Queue(maxsize=10)  # 帧队列，用于存储客户端推送的帧
current_frame = None
frame_lock = threading.Lock()

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/v1/video_feed')
def video_feed():
    """视频流API接口
    
    Returns:
        Response: MJPEG格式的视频流
    """
    def generate():
        """生成视频流帧"""
        global current_frame
        
        while True:
            with frame_lock:
                if current_frame is not None:
                    # 使用客户端推送的帧
                    frame = current_frame.copy()
                else:
                    # 如果没有客户端推流，返回黑屏或等待
                    frame = np.zeros((600, 800, 3), dtype=np.uint8)
                    # 在黑屏上添加提示文字
                    cv2.putText(frame, 'Waiting for client stream...', (200, 300), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # 调整帧大小
            frame = cv2.resize(frame, (800, 600))
            
            # 编码为JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                time.sleep(0.1)
                continue
                
            frame_bytes = buffer.tobytes()
            
            # 返回MJPEG流格式
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(1/20)  # 20 FPS
    
    return Response(generate(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/v1/screenshot', methods=['GET'])
def screenshot():
    """截图API接口
    
    Returns:
        Response: PNG格式的截图
    """
    global current_frame
    
    try:
        with frame_lock:
            if current_frame is not None:
                # 使用客户端推送的最新帧
                img_array = current_frame.copy()
            else:
                # 如果没有客户端推流，返回黑屏
                img_array = np.zeros((600, 800, 3), dtype=np.uint8)
                cv2.putText(img_array, 'No client stream available', (200, 300), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # 将numpy数组编码为PNG格式
        ret, buffer = cv2.imencode('.png', img_array)
        if not ret:
            return Response("截图编码失败", status=500)
        
        # 转换为字节数据
        img_bytes = buffer.tobytes()
        
        return Response(img_bytes, mimetype='image/png')
        
    except Exception as e:
        print(f"截图API错误: {e}")
        return Response(f"截图失败: {str(e)}", status=500)

@app.route('/api/v1/push_frame', methods=['POST'])
def push_frame():
    """接收客户端推送的帧数据
    
    Returns:
        dict: 响应状态
    """
    global current_frame
    
    try:
        # 获取上传的图像数据
        if 'frame' not in request.files:
            return jsonify({'error': '没有找到帧数据'}), 400
            
        file = request.files['frame']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        # 读取图像数据
        file_bytes = file.read()
        nparr = np.frombuffer(file_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': '无法解码图像'}), 400
        
        # 更新当前帧
        with frame_lock:
            current_frame = frame
        
        return jsonify({
            'status': 'success',
            'message': '帧数据接收成功',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"推流接收错误: {e}")
        return jsonify({'error': f'处理失败: {str(e)}'}), 500

@app.route('/api/v1/status')
def status():
    """服务状态API
    
    Returns:
        dict: 服务状态信息
    """
    global current_frame
    
    with frame_lock:
        has_client_stream = current_frame is not None
    
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'has_client_stream': has_client_stream,
        'server_info': {
            'host': '0.0.0.0',
            'port': 8080,
            'endpoints': {
                'home': '/',
                'video_feed': '/api/v1/video_feed',
                'screenshot': '/api/v1/screenshot',
                'push_frame': '/api/v1/push_frame',
                'status': '/api/v1/status'
            }
        }
    })

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({'error': '接口不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    print("="*50)
    print("屏幕录制服务端启动中...")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    print("\n可用接口:")
    print("  主页面:     http://localhost:8080/")
    print("  视频流:     http://localhost:8080/api/v1/video_feed")
    print("  截图:       http://localhost:8080/api/v1/screenshot")
    print("  推流接收:   http://localhost:8080/api/v1/push_frame")
    print("  状态查询:   http://localhost:8080/api/v1/status")
    print("\n按 Ctrl+C 停止服务")
    print("="*50)
    
    try:
        app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"服务启动失败: {e}")