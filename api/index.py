# -*- coding: utf-8 -*-
"""
Vercel serverless function entry point
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入Flask应用
from server import app

# 导出app供Vercel使用
# Vercel会自动处理WSGI应用