# 🔍 Surveillance AI System

An intelligent on-premise surveillance system that uses AI-powered person detection with real-time alerts and monitoring capabilities. This project demonstrates how to build a complete surveillance solution using mobile cameras (for test) as video sources.

<img width="1886" height="931" alt="image" src="https://github.com/user-attachments/assets/f1ffa5a4-1456-4027-b7e9-91665b80fecf" />


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
- ![WhatsApp Image 2025-08-12 at 00 50 37_b020db8f](https://github.com/user-attachments/assets/bd6dbc1d-a202-493e-afa2-d82902a114d6)


#### Configuration Steps:

1. Install the appropriate app on your mobile device
2. Connect your mobile device to the same WiFi network as your computer
3. Open the app and configure RTMP streaming:
   - **Server URL**: `rtmp://[YOUR_COMPUTER_IP]:1935/input/1`
   - **Resolution**: 720p or 1080p (recommended)
   - **Frame Rate**: 15-30 fps

### 2. MediaMTX RTMP Server Setup

MediaMTX acts as the RTMP server that receives video from your mobile camera.

#### Installation:

1. **Download MediaMTX**: (Check for latest version from the releases)
   ```bash
   # For Windows
   wget https://github.com/bluenviron/mediamtx/releases/download/v1.13.1/mediamtx_v1.13.1_windows_amd64.zip
   
   # For macOS
   wget https://github.com/bluenviron/mediamtx/releases
   
   # For Linux
   wget https://github.com/bluenviron/mediamtx/releases/download/v1.13.1/mediamtx_v1.13.1_linux_amd64.tar.gz
   ```

2. **Extract the files** to a folder (e.g., `C:\mediamtx` on Windows)
   (can use this command to extract in linux) 
   ```bash
   tar -xf mediamtx_v1.13.1_linux_amd64.tar.gz
   ```
4. **Find your computer's IP address**:
   ```bash
   # Windows
   ipconfig
   
   # macOS/Linux
   ifconfig
   ```

5. **Configure MediaMTX**:
   - Open `mediamtx.yml` in a text editor
   - Find the `rtmpAddress` setting and update it:
   ```yaml
   rtmpAddress: [YOUR_COMPUTER_IP]:1935
   ```

6. **Start MediaMTX**:
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
   You need to update the RTMP URL in multiple files to match your MediaMTX server address:
   
   - **main.py**: Update the `RTMP_URL` variable:
   ```python
   RTMP_URL = "rtmp://[YOUR_COMPUTER_IP]:1935/input/1"
   ```
   
   - **openai_version.py**: Update the `RTMP_URL` variable:
   ```python
   RTMP_URL = "rtmp://[YOUR_COMPUTER_IP]:1935/input/1"
   ```
   
   - **yolo_version.py**: Update the `RTMP_URL` variable:
   ```python
   RTMP_URL = "rtmp://[YOUR_COMPUTER_IP]:1935/input/1"
   ```
   
   - **person_detection.py**: Update the `DEFAULT_RTMP_URL` variable:
   ```python
   DEFAULT_RTMP_URL = "rtmp://[YOUR_COMPUTER_IP]:1935/input/1"
   ```
   
   Replace `[YOUR_COMPUTER_IP]` with the actual IP address of your computer running MediaMTX.

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

# Surveillance AI - Live Streaming Setup

This guide will help you set up live video streaming from an RTMP source to your React frontend.

## Architecture Overview

1. **RTMP Stream Source** → RTMP stream (`rtmp://82.112.235.249:1935/input/1`)
2. **FFmpeg** → Converts RTMP to HLS format
3. **FastAPI Backend** → Serves HLS stream and analytics API
4. **React Frontend** → Displays live video using HLS.js

## Prerequisites

### Required Software:
- **Python 3.8+**
- **Node.js 16+**
- **FFmpeg** (for RTMP to HLS conversion)

### Installing FFmpeg:

#### Windows:
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your system PATH
4. Verify: `ffmpeg -version`

#### macOS:
```bash
brew install ffmpeg
```

#### Linux:
```bash
sudo apt update
sudo apt install ffmpeg
```

## Setup Instructions

### 1. Backend Setup

Navigate to the backend directory:
```bash
cd backend
```

#### Windows:
```bash
# Run the setup script
start.bat
```

#### Linux/macOS:
```bash
# Make script executable
chmod +x start.sh
# Run the setup script
./start.sh
```

#### Manual Setup:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create HLS output directory
mkdir hls_output

# Start the server
python main.py
```

The backend will start on `http://localhost:8000`

### 2. Frontend Setup

Navigate to the frontend directory:
```bash
cd frontend
```

Install dependencies and start the development server:
```bash
# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will start on `http://localhost:5173`

## How It Works

### 1. RTMP to HLS Conversion
The FastAPI backend uses FFmpeg to convert the RTMP stream to HLS format:
- **Input**: RTMP stream from `rtmp://82.112.235.249:1935/input/1`
- **Output**: HLS segments in `backend/hls_output/` directory
- **Playlist**: `stream.m3u8` file that browsers can consume

### 2. API Endpoints

The backend provides these endpoints:

- `GET /api/stream` - Returns HLS stream URL
- `GET /api/analytics/summary` - Returns analytics data
- `GET /api/alerts` - Returns alert history
- `GET /api/alerts/stream` - Server-sent events for real-time alerts
- `GET /hls/stream.m3u8` - HLS playlist file
- `GET /hls/*.ts` - HLS video segments

### 3. Frontend Integration

The React frontend:
- Uses `HLS.js` to play the HLS stream
- Automatically retries connection on failures
- Displays loading and error states
- Shows live analytics and alerts

## Configuration

### Environment Variables

Create a `.env` file in the frontend directory with:
```env
VITE_API_URL=http://localhost:8000/api
VITE_STREAM_URL=http://localhost:8000/hls/stream.m3u8
```

### Backend Configuration

In `backend/main.py`, you can modify:
- `RTMP_URL` - Source RTMP stream URL
- `HLS_OUTPUT_DIR` - Directory for HLS files
- `JSONL_FILE` - Path to alerts/events file

## Troubleshooting

### Stream Not Loading
1. **Check FFmpeg**: Ensure FFmpeg is installed and in PATH
2. **Check RTMP Source**: Verify the RTMP stream is active
3. **Check Backend Logs**: Look for FFmpeg errors in the console
4. **Check Network**: Ensure ports 8000 and 5173 are not blocked

### Common Issues

#### "FFmpeg not found"
- Install FFmpeg and add to system PATH
- Restart terminal/command prompt after installation

#### "Stream unavailable"
- Check if the RTMP source is broadcasting
- Verify the RTMP URL is correct
- Check firewall settings

#### "CORS errors"
- Ensure backend is running on localhost:8000
- Check that frontend .env file has correct API URL

### Debugging Steps

1. **Check Backend Health**:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **Check Stream Endpoint**:
   ```bash
   curl http://localhost:8000/api/stream
   ```

3. **Check HLS Playlist**:
   ```bash
   curl http://localhost:8000/hls/stream.m3u8
   ```

4. **Monitor Backend Logs**: Watch the console where you started the backend

## Production Deployment

For production deployment:

1. **Use HTTPS**: Configure SSL certificates
2. **Update CORS**: Restrict origins to your domain
3. **Environment Variables**: Use production URLs
4. **Process Management**: Use PM2 or systemd for the backend
5. **Reverse Proxy**: Use Nginx to serve static files and proxy API requests

## Performance Optimization

- **HLS Settings**: Adjust segment duration and playlist size in FFmpeg command
- **Quality Settings**: Modify FFmpeg encoding presets for quality vs. performance
- **Caching**: Implement CDN for HLS segments in production
- **Load Balancing**: Use multiple backend instances for high traffic

## Security Considerations

- **Authentication**: Add API authentication for production
- **Rate Limiting**: Implement rate limiting on API endpoints
- **Input Validation**: Validate all API inputs
- **HTTPS Only**: Force HTTPS in production
- **Stream Access**: Restrict access to HLS endpoints

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all prerequisites are installed
3. Check console logs for error messages
4. Ensure the RTMP source stream is active


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
