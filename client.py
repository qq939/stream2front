#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
屏幕录制客户端
向服务端推送屏幕录制流
"""

import cv2
import requests
import time
import threading
from screen_recorder import ScreenRecorder
from datetime import datetime
import argparse
import sys
import io

class StreamClient:
    """推流客户端类"""
    
    def __init__(self, server_url="http://localhost:8080", fps=20, quality=80):
        """
        初始化推流客户端
        
        Args:
            server_url (str): 服务端URL地址
            fps (int): 推流帧率
            quality (int): JPEG压缩质量 (1-100)
        """
        self.server_url = server_url.rstrip('/')
        self.push_url = f"{self.server_url}/push"
        self.status_url = f"{self.server_url}/status"
        self.health_url = f"{self.server_url}/health"
        self.fps = fps
        self.quality = quality
        self.is_streaming = False
        self.recorder = ScreenRecorder(fps=fps)
        self.session = requests.Session()
        self.stats = {
            'frames_sent': 0,
            'frames_failed': 0,
            'start_time': None,
            'last_success': None
        }
        
    def test_connection(self, retries=3):
        """测试与服务端的连接
        
        Args:
            retries (int): 重试次数
            
        Returns:
            bool: 连接是否成功
        """
        for attempt in range(retries):
            try:
                print(f"尝试连接服务端... (第 {attempt + 1}/{retries} 次)")
                
                # 增加超时时间，适应 Vercel 冷启动
                response = self.session.get(self.status_url, timeout=15)
                
                if response.status_code == 200:
                    try:
                        server_info = response.json()
                        print(f"✓ 服务端连接成功")
                        print(f"  服务端状态: {server_info.get('status', 'unknown')}")
                        print(f"  服务端时间: {server_info.get('timestamp', 'unknown')}")
                        return True
                    except ValueError:
                        print(f"✗ 服务端响应格式错误，可能是认证页面")
                        print(f"  响应内容: {response.text[:200]}...")
                        return False
                else:
                    print(f"✗ 服务端响应错误: {response.status_code}")
                    if attempt < retries - 1:
                        print(f"等待 3 秒后重试...")
                        time.sleep(3)
                    
            except requests.exceptions.Timeout:
                print(f"✗ 连接超时 (可能是 Vercel 冷启动)")
                if attempt < retries - 1:
                    print(f"等待 5 秒后重试...")
                    time.sleep(5)
                    
            except requests.exceptions.RequestException as e:
                print(f"✗ 无法连接到服务端: {e}")
                if attempt < retries - 1:
                    print(f"等待 3 秒后重试...")
                    time.sleep(3)
                    
        return False
    
    def diagnose_server(self):
        """诊断服务端部署问题"""
        print("\n=== 服务端诊断 ===")
        
        # 检查基本连接
        try:
            response = self.session.get(self.server_url, timeout=10)
            print(f"基本连接: HTTP {response.status_code}")
            
            # 检查是否是 Vercel 认证页面
            if "vercel.com/sso-api" in response.text:
                print("⚠️  检测到 Vercel SSO 认证页面")
                print("   问题: 项目可能被设置为私有或需要认证")
                print("   解决方案:")
                print("   1. 登录 Vercel Dashboard")
                print("   2. 进入项目设置 -> Functions")
                print("   3. 确保项目访问权限设置为 Public")
                return False
                
        except Exception as e:
            print(f"基本连接失败: {e}")
            
        # 检查健康检查接口
        try:
            response = self.session.get(self.health_url, timeout=10)
            print(f"健康检查: HTTP {response.status_code}")
            if response.status_code == 200:
                print("✓ 健康检查通过")
            else:
                print(f"✗ 健康检查失败: {response.text[:100]}")
        except Exception as e:
            print(f"健康检查失败: {e}")
            
        # 检查状态接口
        try:
            response = self.session.get(self.status_url, timeout=10)
            print(f"状态接口: HTTP {response.status_code}")
            if response.status_code == 200:
                print("✓ 状态接口正常")
                try:
                    data = response.json()
                    print(f"  服务状态: {data}")
                except:
                    print(f"  响应内容: {response.text[:100]}")
            else:
                print(f"✗ 状态接口失败: {response.text[:100]}")
        except Exception as e:
            print(f"状态接口失败: {e}")
            
        print("=== 诊断完成 ===\n")
        return True
     
    def start_streaming(self):
        """开始推流"""
        if self.is_streaming:
            print("推流已在进行中")
            return
        
        print("正在测试服务端连接...")
        if not self.test_connection():
            print("无法连接到服务端，推流终止")
            return
        
        self.is_streaming = True
        self.stats['start_time'] = datetime.now()
        self.stats['frames_sent'] = 0
        self.stats['frames_failed'] = 0
        
        print("="*50)
        print("开始推流到服务端")
        print(f"服务端地址: {self.server_url}")
        print(f"推流帧率: {self.fps} FPS")
        print(f"图像质量: {self.quality}%")
        print("按 Ctrl+C 停止推流")
        print("="*50)
        
        # 启动统计线程
        stats_thread = threading.Thread(target=self._stats_reporter, daemon=True)
        stats_thread.start()
        
        try:
            self._streaming_loop()
        except KeyboardInterrupt:
            print("\n用户中断推流")
        except Exception as e:
            print(f"\n推流过程中发生错误: {e}")
        finally:
            self.stop_streaming()
    
    def _streaming_loop(self):
        """推流主循环"""
        frame_interval = 1.0 / self.fps
        
        while self.is_streaming:
            start_time = time.time()
            
            # 获取屏幕截图
            frame = self.recorder.screenshot()
            if frame is None:
                print("获取屏幕截图失败")
                time.sleep(frame_interval)
                continue
            
            # 发送帧到服务端
            success = self._send_frame(frame)
            
            if success:
                self.stats['frames_sent'] += 1
                self.stats['last_success'] = datetime.now()
            else:
                self.stats['frames_failed'] += 1
            
            # 控制帧率
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _send_frame(self, frame):
        """发送单帧到服务端
        
        Args:
            frame (numpy.ndarray): 图像帧
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 编码为JPEG
            ret, buffer = cv2.imencode('.jpg', frame, 
                                     [cv2.IMWRITE_JPEG_QUALITY, self.quality])
            if not ret:
                return False
            
            # 准备文件数据
            files = {
                'frame': ('frame.jpg', buffer.tobytes(), 'image/jpeg')
            }
            
            # 发送POST请求，增加超时时间适应 Vercel
            response = self.session.post(self.push_url, files=files, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                print(f"服务端响应错误: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {e}")
            return False
        except Exception as e:
            print(f"发送帧失败: {e}")
            return False
    
    def _stats_reporter(self):
        """统计信息报告线程"""
        while self.is_streaming:
            time.sleep(10)  # 每10秒报告一次
            if self.is_streaming:
                self._print_stats()
    
    def _print_stats(self):
        """打印统计信息"""
        if self.stats['start_time'] is None:
            return
        
        elapsed = datetime.now() - self.stats['start_time']
        total_frames = self.stats['frames_sent'] + self.stats['frames_failed']
        success_rate = (self.stats['frames_sent'] / total_frames * 100) if total_frames > 0 else 0
        avg_fps = self.stats['frames_sent'] / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
        
        print(f"\n📊 推流统计 (运行时间: {str(elapsed).split('.')[0]})")
        print(f"   成功帧数: {self.stats['frames_sent']}")
        print(f"   失败帧数: {self.stats['frames_failed']}")
        print(f"   成功率: {success_rate:.1f}%")
        print(f"   平均FPS: {avg_fps:.1f}")
        if self.stats['last_success']:
            last_success_ago = datetime.now() - self.stats['last_success']
            print(f"   最后成功: {last_success_ago.total_seconds():.1f}秒前")
    
    def stop_streaming(self):
        """停止推流"""
        if not self.is_streaming:
            return
        
        self.is_streaming = False
        print("\n正在停止推流...")
        
        # 打印最终统计
        self._print_stats()
        
        # 关闭会话
        self.session.close()
        
        print("推流已停止")
    
    def set_quality(self, quality):
        """设置图像质量
        
        Args:
            quality (int): JPEG质量 (1-100)
        """
        self.quality = max(1, min(100, quality))
        print(f"图像质量已设置为: {self.quality}%")
    
    def set_fps(self, fps):
        """设置帧率
        
        Args:
            fps (int): 目标帧率
        """
        self.fps = max(1, min(60, fps))
        self.recorder.set_fps(self.fps)
        print(f"帧率已设置为: {self.fps} FPS")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='屏幕录制推流客户端')
    parser.add_argument('--server', '-s', default='http://localhost:8080',
                       help='服务端URL地址 (默认: http://localhost:8080)')
    parser.add_argument('--fps', '-f', type=int, default=20,
                       help='推流帧率 (默认: 20)')
    parser.add_argument('--quality', '-q', type=int, default=80,
                       help='JPEG压缩质量 1-100 (默认: 80)')
    parser.add_argument('--test', '-t', action='store_true',
                       help='仅测试连接，不开始推流')
    parser.add_argument('-d', '--diagnose', action='store_true', help='诊断服务端问题')
    
    args = parser.parse_args()
    
    # 参数验证
    if args.fps < 1 or args.fps > 60:
        print("错误: 帧率必须在1-60之间")
        sys.exit(1)
    
    if args.quality < 1 or args.quality > 100:
        print("错误: 质量必须在1-100之间")
        sys.exit(1)
    
    # 创建客户端
    client = StreamClient(
        server_url=args.server,
        fps=args.fps,
        quality=args.quality
    )
    
    # 如果是诊断模式
    if args.diagnose:
        client.diagnose_server()
        return
    
    if args.test:
        # 仅测试连接
        print("测试服务端连接...")
        if client.test_connection():
            print("连接测试成功！")
            sys.exit(0)
        else:
            print("连接测试失败！")
            client.diagnose_server()
            sys.exit(1)
    else:
        # 开始推流
        client.start_streaming()

if __name__ == '__main__':
    main()