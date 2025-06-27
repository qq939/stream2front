# 屏幕录制推流系统

一个基于Python的屏幕录制推流系统，支持客户端向服务端推流，服务端提供Web界面和API接口。

## 项目结构

```
stream2front/
├── app.py              # 原始单机版应用（保留不变）
├── server.py           # 服务端程序
├── client.py           # 客户端程序
├── screen_recorder.py  # 屏幕录制核心类
├── requirements.txt    # 依赖包列表
├── templates/
│   └── index.html     # Web界面模板
└── README.md          # 说明文档
```

## 功能特性

### 服务端 (server.py)
- 🌐 Web主页面展示
- 📹 视频流API接口 (`/api/v1/video_feed`)
- 📸 截图API接口 (`/api/v1/screenshot`)
- 📡 接收客户端推流 (`/api/v1/push_frame`)
- 📊 服务状态查询 (`/api/v1/status`)
- 🔄 支持多客户端推流（最新帧覆盖）
- 🛡️ 错误处理和异常恢复

### 客户端 (client.py)
- 🖥️ 实时屏幕捕获
- 📤 向服务端推流
- ⚙️ 可配置帧率和图像质量
- 📈 实时统计信息
- 🔗 连接状态监控
- 🎛️ 命令行参数支持

## 安装依赖

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
uv pip install -r requirements.txt
```

## 使用方法

### 1. 启动服务端

```bash
# 基本启动
python server.py

# 或使用uv运行
uv run python server.py
```

服务端启动后会显示：
```
==================================================
屏幕录制服务端启动中...
启动时间: 2024-01-01 12:00:00
==================================================

可用接口:
  主页面:     http://localhost:8080/
  视频流:     http://localhost:8080/api/v1/video_feed
  截图:       http://localhost:8080/api/v1/screenshot
  推流接收:   http://localhost:8080/api/v1/push_frame
  状态查询:   http://localhost:8080/api/v1/status

按 Ctrl+C 停止服务
==================================================
```

### 2. 启动客户端推流

```bash
# 基本推流（默认连接localhost:8080）
python client.py

# 指定服务端地址
python client.py --server http://192.168.1.100:8080

# 自定义参数
python client.py --server http://192.168.1.100:8080 --fps 30 --quality 90

# 仅测试连接
python client.py --test
```

#### 客户端参数说明

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--server` | `-s` | `http://localhost:8080` | 服务端URL地址 |
| `--fps` | `-f` | `20` | 推流帧率 (1-60) |
| `--quality` | `-q` | `80` | JPEG压缩质量 (1-100) |
| `--test` | `-t` | - | 仅测试连接，不开始推流 |

### 3. 访问Web界面

打开浏览器访问：`http://localhost:8080`

## API接口文档

### GET /
主页面，显示视频流界面

### GET /api/v1/video_feed
获取MJPEG格式的视频流
- **响应格式**: `multipart/x-mixed-replace; boundary=frame`
- **用途**: 在网页中嵌入视频流

### GET /api/v1/screenshot
获取当前屏幕截图
- **响应格式**: `image/png`
- **用途**: 获取单张截图

### POST /api/v1/push_frame
接收客户端推送的帧数据
- **请求格式**: `multipart/form-data`
- **参数**: `frame` (图像文件)
- **响应格式**: `application/json`

**请求示例**:
```bash
curl -X POST -F "frame=@screenshot.jpg" http://localhost:8080/api/v1/push_frame
```

**响应示例**:
```json
{
  "status": "success",
  "message": "帧数据接收成功",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

### GET /api/v1/status
获取服务状态信息
- **响应格式**: `application/json`

**响应示例**:
```json
{
  "status": "running",
  "timestamp": "2024-01-01T12:00:00.000000",
  "has_client_stream": true,
  "server_info": {
    "host": "0.0.0.0",
    "port": 8080,
    "endpoints": {
      "home": "/",
      "video_feed": "/api/v1/video_feed",
      "screenshot": "/api/v1/screenshot",
      "push_frame": "/api/v1/push_frame",
      "status": "/api/v1/status"
    }
  }
}
```

## 使用场景

### 1. 本地测试
```bash
# 终端1: 启动服务端
python server.py

# 终端2: 启动客户端
python client.py

# 浏览器: 访问 http://localhost:8080
```

### 2. 远程推流
```bash
# 服务端机器 (IP: 192.168.1.100)
python server.py

# 客户端机器
python client.py --server http://192.168.1.100:8080
```

### 3. 高质量推流
```bash
# 30fps, 95%质量
python client.py --fps 30 --quality 95
```

### 4. 低带宽推流
```bash
# 10fps, 50%质量
python client.py --fps 10 --quality 50
```

## VSCode快捷键提示

在macOS的VSCode中开发时，可以使用以下快捷键提高效率：

| 功能 | 快捷键 | 说明 |
|------|--------|------|
| 代码补全 | `Tab` | 输入几个字母后按Tab自动补全 |
| 智能提示 | `Ctrl + Space` | 显示代码提示和补全选项 |
| 快速修复 | `Cmd + .` | 显示快速修复建议 |
| 格式化代码 | `Shift + Option + F` | 自动格式化当前文件 |
| 运行Python | `Cmd + F5` | 运行当前Python文件 |
| 打开终端 | `Ctrl + `` ` | 打开集成终端 |
| 文件搜索 | `Cmd + P` | 快速打开文件 |
| 全局搜索 | `Cmd + Shift + F` | 在项目中搜索 |
| 多光标编辑 | `Option + Click` | 在多个位置放置光标 |
| 复制行 | `Shift + Option + ↓` | 向下复制当前行 |

## 故障排除

### 1. 端口占用
如果8080端口被占用，可以修改server.py中的端口号：
```python
app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)
```

### 2. 权限问题
macOS可能需要授权屏幕录制权限：
- 系统偏好设置 → 安全性与隐私 → 隐私 → 屏幕录制
- 添加Terminal或Python到允许列表

### 3. 网络连接问题
检查防火墙设置，确保8080端口可以访问。

### 4. 依赖安装问题
```bash
# 升级pip
pip install --upgrade pip

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

## 技术架构

- **后端框架**: Flask
- **屏幕捕获**: mss + OpenCV
- **图像处理**: OpenCV (cv2)
- **HTTP客户端**: requests
- **视频流**: MJPEG over HTTP
- **并发处理**: Threading

## 性能优化建议

1. **调整帧率**: 根据网络带宽调整FPS
2. **压缩质量**: 平衡图像质量和传输速度
3. **网络优化**: 使用有线网络获得更稳定的传输
4. **硬件加速**: 使用性能更好的机器作为客户端

## 许可证

MIT License