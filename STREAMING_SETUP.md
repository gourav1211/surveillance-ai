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
