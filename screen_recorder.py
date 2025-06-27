#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的屏幕录制脚本
使用cv2录制屏幕，按'q'键停止录制
"""

import cv2
import numpy as np
import pyautogui
import time
from datetime import datetime

def record_screen():
    # 获取屏幕尺寸
    screen_size = pyautogui.size()
    print(f"屏幕尺寸: {screen_size}")
    
    # 设置录制参数
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"screen_recording_{timestamp}.mp4"
    fps = 20.0
    
    # 创建VideoWriter对象
    out = cv2.VideoWriter(output_file, fourcc, fps, screen_size)
    
    print(f"开始录制屏幕，输出文件: {output_file}")
    print("按 'q' 键停止录制")
    
    try:
        while True:
            # 截取屏幕
            screenshot = pyautogui.screenshot()
            
            # 转换为numpy数组
            frame = np.array(screenshot)
            
            # 转换颜色格式 (RGB -> BGR)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # 写入视频文件
            out.write(frame)
            
            # 显示当前帧（可选，会影响性能）
            # cv2.imshow('Screen Recording', cv2.resize(frame, (800, 600)))
            
            # 检查是否按下'q'键
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
            # 控制帧率
            time.sleep(1/fps)
            
    except KeyboardInterrupt:
        print("\n录制被中断")
    
    finally:
        # 释放资源
        out.release()
        cv2.destroyAllWindows()
        print(f"录制完成，文件保存为: {output_file}")

if __name__ == "__main__":
    record_screen()