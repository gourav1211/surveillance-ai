# 🔍 Surveillance AI System

An intelligent on-premise surveillance system that uses AI-powered person detection with real-time alerts and monitoring capabilities. This project demonstrates how to build a complete surveillance solution using mobile cameras as video sources.

## 📋 Table of Contents

- [Features](#-features)
- [How It Works](#-how-it-works)
- [Prerequisites](#-prerequisites)
- [Setup Guide](#-setup-guide)
  - [1. Mobile Camera Setup](#1-mobile-camera-setup)
  - [2. MediaMTX RTMP Server Setup](#2-mediamtx-rtmp-server-setup)
  - [3. Backend Setup](#3-backend-setup)
  - [4. Frontend Setup](#4-frontend-setup)
- [Usage](#-usage)
- [Troubleshooting](#-troubleshooting)
- [Technical Stack](#-technical-stack)
- [Contributing](#-contributing)

## ✨ Features

- **Real-time Person Detection**: Uses YOLOv8 for accurate human detection
- **Live Video Streaming**: RTMP to HLS conversion for web-based viewing
- **Smart Alerts**: Instant notifications when people are detected
- **Analytics Dashboard**: View detection trends and statistics
- **Multi-platform Support**: Works on Windows, macOS, and Linux
- **On-premise Solution**: No cloud dependency, works entirely on local network
- **Mobile Camera Integration**: Use your smartphone as a security camera
- **Real-time Monitoring**: Live dashboard with detection overlays

## 🔧 How It Works

1. **Mobile App** streams video via RTMP protocol
2. **MediaMTX Server** receives RTMP stream and makes it available
3. **Backend AI System** processes the video stream for person detection
4. **Frontend Dashboard** displays live video with detection overlays and alerts
5. **Real-time Alerts** notify users when people are detected

## 📋 Prerequisites

- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.8 or higher
- **Node.js**: Version 16 or higher
- **FFmpeg**: For video processing
- **Mobile Device**: Android or iOS smartphone
- **Network**: WiFi network connecting all devices

## 🚀 Setup Guide

### 1. Mobile Camera Setup

Transform your smartphone into a security camera using these apps:

#### For Android:
- **App Name**: RTMP Camera
- **Download**: [Google Play Store]([https://play.google.com/store/apps/details?id=com.shenyaocn.android.WebCam](https://play.google.com/store/apps/details?id=video.surveillance.rtmp.camera&pcampaignid=web_share))

#### For iOS:
- **App Name**: IP Camera Lite
- **Download**: [App Store](https://apps.apple.com/app/ip-camera-lite/id1013455241)

#### Configuration Steps:

1. Install the appropriate app on your mobile device
2. Connect your mobile device to the same WiFi network as your computer
3. Open the app and configure RTMP streaming:
   - **Server URL**: `rtmp://[YOUR_COMPUTER_IP]:1935/input/1`
   - **Resolution**: 720p or 1080p (recommended)
   - **Frame Rate**: 15-30 fps

![WhatsApp Image 2025-08-11 at 22 14 08_ea076011](https://github.com/user-attachments/assets/e678b719-0318-4874-a7f7-ea023d301276)


### 2. MediaMTX RTMP Server Setup

MediaMTX acts as the RTMP server that receives video from your mobile camera.

#### Installation:

1. **Download MediaMTX**:
   ```bash
   # For Windows
   wget https://github.com/bluenviron/mediamtx/releases/latest/download/mediamtx_v1.0.0_windows_amd64.zip
   
   # For macOS
   wget https://github.com/bluenviron/mediamtx/releases/latest/download/mediamtx_v1.0.0_darwin_amd64.tar.gz
   
   # For Linux
   wget https://github.com/bluenviron/mediamtx/releases/latest/download/mediamtx_v1.0.0_linux_amd64.tar.gz
   ```

2. **Extract the files** to a folder (e.g., `C:\mediamtx` on Windows)

3. **Find your computer's IP address**:
   ```bash
   # Windows
   ipconfig
   
   # macOS/Linux
   ifconfig
   ```

4. **Configure MediaMTX**:
   - Open `mediamtx.yml` in a text editor
   - Find the `rtmpAddress` setting and update it:
   ```yaml
   rtmpAddress: [YOUR_COMPUTER_IP]:1935
   ```

5. **Start MediaMTX**:
   ```bash
   # Windows
   ./mediamtx.exe
   
   # macOS/Linux
   ./mediamtx
   ```

The server should start and listen on port 1935 for RTMP connections.

### 3. Backend Setup

The backend handles AI detection and video processing.

#### Installation:

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg**:
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg` (Ubuntu/Debian)

5. **Configure the RTMP URL**:
   - Open `main.py`
   - Update the `RTMP_URL` variable with your MediaMTX server address:
   ```python
   RTMP_URL = "rtmp://[YOUR_COMPUTER_IP]:1935/input/1"
   ```

6. **Start the backend server**:
   ```bash
   python main.py
   ```

The backend will start on `http://localhost:8000`

### 4. Frontend Setup

The frontend provides the web dashboard for monitoring.

#### Installation:

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

The frontend will start on `http://localhost:5173`

## 🎯 Usage

1. **Start all services** in this order:
   - MediaMTX server
   - Backend API server
   - Frontend development server

2. **Start mobile streaming**:
   - Open the camera app on your mobile device
   - Start RTMP streaming to your server

3. **Access the dashboard**:
   - Open your web browser
   - Navigate to `http://localhost:5173`
   - You should see the live video feed with detection capabilities

4. **Monitor detections**:
   - View live video with person detection overlays
   - Check the alerts panel for recent detections
   - Monitor analytics and trends

## 🔧 Troubleshooting

### Common Issues:

**Mobile app can't connect to server:**
- Verify all devices are on the same WiFi network
- Check firewall settings (allow port 1935)
- Ensure MediaMTX is running and configured correctly
- If you are using Mobile Hotspot it won't work, so switch to a WIFI network 

**No video in dashboard:**
- Check if FFmpeg is properly installed
- Verify RTMP stream is being received by MediaMTX
- Check browser console for errors

**Detection not working:**
- Ensure Python dependencies are installed correctly
- Check if YOLO model is downloaded (happens automatically on first run)
- Verify sufficient system resources (CPU/GPU)

**Performance issues:**
- Reduce mobile camera resolution/frame rate
- Close unnecessary applications
- Consider using GPU acceleration if available

## 💻 Technical Stack

### Backend:
- **FastAPI**: Web framework for API development
- **YOLOv8**: AI model for person detection
- **OpenCV**: Computer vision processing
- **FFmpeg**: Video stream processing
- **Uvicorn**: ASGI server

### Frontend:
- **React**: User interface framework
- **Vite**: Build tool and development server
- **Tailwind CSS**: Styling framework
- **HLS.js**: Video streaming library
- **Recharts**: Data visualization

### Infrastructure:
- **MediaMTX**: RTMP server
- **RTMP Protocol**: Video streaming
- **HLS Protocol**: Web video delivery

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Review the console logs for error messages
3. Create an issue in the GitHub repository

---

**Note**: This system is designed for educational and demonstration purposes. For production surveillance systems, consider additional security measures and proper hardware.
