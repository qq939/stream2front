#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
屏幕录制服务端
提供Web界面和API接口，接收客户端推流
"""

from flask import Flask, Response, render_template, jsonify, request
import io
import threading
import time
import queue
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import base64
import argparse
import os

app = Flask(__name__)

# 全局变量
frame_queue = queue.Queue(maxsize=10)  # 帧队列，用于存储客户端推送的帧
current_frame = None
frame_lock = threading.Lock()

def create_placeholder_image(width, height, text):
    """创建占位符图像"""
    # 创建RGB图像
    img = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(img)
    
    # 尝试使用默认字体，如果失败则使用内置字体
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # 计算文字位置（居中）
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # 绘制文字
    draw.text((x, y), text, fill='white', font=font)
    
    # 直接返回PIL Image对象
    return img

def encode_frame_to_jpeg(frame, size=None):
    """将PIL Image编码为JPEG字节"""
    try:
        # 确保frame是PIL Image对象
        if not isinstance(frame, Image.Image):
            return None
            
        img = frame
        
        # 调整大小
        if size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        
        # 编码为JPEG
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=80)
        return buffer.getvalue()
    except Exception as e:
        print(f"JPEG编码错误: {e}")
        return None

def encode_frame_to_png(frame):
    """将PIL Image编码为PNG字节"""
    try:
        # 确保frame是PIL Image对象
        if not isinstance(frame, Image.Image):
            return None
            
        img = frame
        
        # 编码为PNG
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    except Exception as e:
        print(f"PNG编码错误: {e}")
        return None

def decode_image_bytes(image_bytes):
    """解码图像字节为PIL Image"""
    try:
        # 使用PIL解码图像
        img = Image.open(io.BytesIO(image_bytes))
        
        # 确保是RGB模式
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 直接返回PIL Image对象
        return img
    except Exception as e:
        print(f"图像解码错误: {e}")
        return None

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
                    frame = create_placeholder_image(800, 600, 'Waiting for client stream...')
            
            # 调整帧大小并编码为JPEG
            try:
                frame_bytes = encode_frame_to_jpeg(frame, (800, 600))
                if frame_bytes is None:
                    time.sleep(0.1)
                    continue
            except Exception as e:
                print(f"帧编码错误: {e}")
                time.sleep(0.1)
                continue
            
            # 返回MJPEG流格式
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(1/20)  # 20 FPS
    
    return Response(generate(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/health')
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

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
                img_array = create_placeholder_image(800, 600, 'No client stream available')
        
        # 将PIL Image编码为PNG格式
        try:
            img_bytes = encode_frame_to_png(img_array)
            if img_bytes is None:
                return Response("截图编码失败", status=500)
        except Exception as e:
            print(f"截图编码错误: {e}")
            return Response(f"截图编码失败: {str(e)}", status=500)
        
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
        try:
            file_bytes = file.read()
            frame = decode_image_bytes(file_bytes)
            
            if frame is None:
                return jsonify({'error': '无法解码图像'}), 400
        except Exception as e:
            print(f"图像解码错误: {e}")
            return jsonify({'error': f'图像解码失败: {str(e)}'}), 400
        
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

# Vercel serverless function entry point
app.config['ENV'] = 'production'

# Export the Flask app for Vercel
# This is required for Vercel to recognize the WSGI application
def handler(request):
    return app(request.environ, request.start_response)

# For Vercel deployment
vercel_app = app

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='屏幕录制服务端')
    parser.add_argument('--port', '-p', type=int, default=8080,
                       help='服务端监听端口 (默认: 8080)')
    args = parser.parse_args()

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
        app.run(host='0.0.0.0', port=args.port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"服务启动失败: {e}")