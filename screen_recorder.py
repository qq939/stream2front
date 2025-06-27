#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
屏幕实时显示类
使用cv2和mss进行屏幕捕获和显示，按'q'键停止显示
"""

import cv2
import numpy as np
import mss
import time
from datetime import datetime


class ScreenRecorder:
    """屏幕实时显示类"""
    
    def __init__(self, fps=20.0, display_size=(800, 600), monitor_index=1, window_name='Screen Display'):
        """
        初始化屏幕录制器
        
        Args:
            fps (float): 帧率，默认20.0
            display_size (tuple): 显示窗口大小，默认(800, 600)
            monitor_index (int): 显示器索引，0为所有显示器，1为主显示器，默认1
            window_name (str): 显示窗口名称，默认'Screen Display'
        """
        self.fps = fps
        self.display_size = display_size
        self.monitor_index = monitor_index
        self.window_name = window_name
        self.is_running = False
        
        # 初始化mss对象
        self.sct = None
        self.monitor = None
        self.screen_size = None
        
    def _initialize_capture(self):
        """初始化屏幕捕获"""
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[self.monitor_index]
        self.screen_size = (self.monitor['width'], self.monitor['height'])
        print(f"屏幕尺寸: {self.screen_size}")
        
    def start_display(self):
        """开始屏幕实时显示"""
        if self.is_running:
            print("屏幕显示已在运行中")
            return
            
        try:
            self._initialize_capture()
            self.is_running = True
            
            print("开始屏幕实时显示")
            print(f"显示窗口大小: {self.display_size}")
            print(f"帧率: {self.fps} FPS")
            print("按 'q' 键停止显示")
            
            while self.is_running:
                # 使用mss截取屏幕
                screenshot = self.sct.grab(self.monitor)
                
                # 转换为numpy数组
                frame = np.array(screenshot)
                
                # mss返回的是BGRA格式，转换为BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # 调整显示大小
                resized_frame = cv2.resize(frame, self.display_size)
                
                # 显示当前帧
                cv2.imshow(self.window_name, resized_frame)
                
                # 检查是否按下'q'键
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop_display()
                    break
                    
                # 控制帧率
                time.sleep(1/self.fps)
                
        except KeyboardInterrupt:
            print("\n显示被中断")
            self.stop_display()
        except Exception as e:
            print(f"发生错误: {e}")
            self.stop_display()
            
    def stop_display(self):
        """停止屏幕显示"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # 释放资源
        if self.sct:
            self.sct.close()
        cv2.destroyAllWindows()
        print("屏幕显示已停止")
        
    def set_fps(self, fps):
        """设置帧率"""
        self.fps = fps
        print(f"帧率已设置为: {fps} FPS")
        
    def set_display_size(self, width, height):
        """设置显示窗口大小"""
        self.display_size = (width, height)
        print(f"显示窗口大小已设置为: {width}x{height}")
        
    def get_screen_info(self):
        """获取屏幕信息"""
        if not self.sct:
            temp_sct = mss.mss()
            monitor = temp_sct.monitors[self.monitor_index]
            temp_sct.close()
            return {
                'width': monitor['width'],
                'height': monitor['height'],
                'left': monitor['left'],
                'top': monitor['top']
            }
        else:
            return {
                'width': self.monitor['width'],
                'height': self.monitor['height'],
                'left': self.monitor['left'],
                'top': self.monitor['top']
            }
    
    def screenshot(self):
        """获取当前屏幕截图
        
        Returns:
            numpy.ndarray: BGR格式的图像数组，如果失败返回None
        """
        try:
            # 如果没有初始化mss对象，临时创建一个
            if not self.sct:
                temp_sct = mss.mss()
                monitor = temp_sct.monitors[self.monitor_index]
                
                # 截取屏幕
                screenshot = temp_sct.grab(monitor)
                temp_sct.close()
            else:
                # 使用已有的mss对象
                screenshot = self.sct.grab(self.monitor)
            
            # 转换为numpy数组
            frame = np.array(screenshot)
            
            # mss返回的是BGRA格式，转换为BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            return frame
            
        except Exception as e:
            print(f"截图失败: {e}")
            return None
    
    def save_screenshot(self, filename=None):
        """保存当前屏幕截图到文件
        
        Args:
            filename (str, optional): 保存的文件名，如果不提供则自动生成
            
        Returns:
            str: 保存的文件路径，如果失败返回None
        """
        frame = self.screenshot()
        if frame is None:
            return None
            
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            
        try:
            cv2.imwrite(filename, frame)
            print(f"截图已保存: {filename}")
            return filename
        except Exception as e:
            print(f"保存截图失败: {e}")
            return None


if __name__ == "__main__":
    # 创建屏幕录制器实例，可以自定义参数
    recorder = ScreenRecorder(
        fps=25.0,                    # 设置帧率为25 FPS
        display_size=(1024, 768),    # 设置显示窗口大小
        monitor_index=1,             # 使用主显示器
        window_name='我的屏幕显示'     # 自定义窗口名称
    )
    
    # 显示屏幕信息
    screen_info = recorder.get_screen_info()
    print(f"屏幕信息: {screen_info}")
    
    # # 开始显示
    recorder.start_display()