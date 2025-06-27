#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的屏幕录制脚本
使用cv2录制屏幕，按'q'键停止录制
"""

import cv2
import numpy as np
import mss
import time
from datetime import datetime

def record_screen():
    # 创建mss对象
    with mss.mss() as sct:
        # 获取主显示器信息
        monitor = sct.monitors[1]  # 0是所有显示器，1是主显示器
        screen_size = (monitor['width'], monitor['height'])
        print(f"屏幕尺寸: {screen_size}")
        
        # 设置显示参数
        fps = 20.0
        
        print("开始屏幕实时显示")
        print("按 'q' 键停止显示")
        
        try:
            while True:
                # 使用mss截取屏幕
                screenshot = sct.grab(monitor)
                
                # 转换为numpy数组
                frame = np.array(screenshot)
                
                # mss返回的是BGRA格式，转换为BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # 不保存文件，只显示
                
                # 显示当前帧（可选，会影响性能）
                cv2.imshow('Screen Recording', cv2.resize(frame, (800, 600)))
                
                # 检查是否按下'q'键
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
                # 控制帧率
                time.sleep(1/fps)
                
        except KeyboardInterrupt:
            print("\n录制被中断")
        
        finally:
            # 释放资源
            cv2.destroyAllWindows()
            print("屏幕显示已停止")

if __name__ == "__main__":
    record_screen()