import cv2
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from ultralytics import YOLO
import os
from pathlib import Path
import shutil
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
import platform

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure paths
HOME = Path.cwd()
UPLOADS_DIR = HOME / "uploads"
OUTPUTS_DIR = HOME / "outputs"
TRAINED_MODEL_PATH = HOME / "runs/detect/train3/weights/best.pt"

# Create directories if they don't exist
UPLOADS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# Initialize YOLO model
try:
    model = YOLO(TRAINED_MODEL_PATH)
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    model = None

# Determine the appropriate codec based on the operating system
def get_video_writer(filename, fps, frame_size):
    system = platform.system().lower()
    if system == "darwin":  # macOS
        fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
    elif system == "windows":
        fourcc = cv2.VideoWriter_fourcc(*'H264')
    else:  # Linux and others
        fourcc = cv2.VideoWriter_fourcc(*'X264')
    
    return cv2.VideoWriter(filename, fourcc, fps, frame_size)

@app.post("/upload_video/")
async def upload_video(file: UploadFile = File(...)):
    if not model:
        raise HTTPException(status_code=500, detail="YOLO model not initialized")
    
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov')):
        raise HTTPException(status_code=400, detail="Unsupported file format")

    try:
        # Save uploaded video
        video_path = UPLOADS_DIR / file.filename
        with video_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process video with YOLO
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not open video file")

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        output_path = OUTPUTS_DIR / f"processed_{file.filename}"
        
        # Use platform-specific codec
        out = get_video_writer(str(output_path), fps, (frame_width, frame_height))
        
        if not out.isOpened():
            raise HTTPException(status_code=500, detail="Failed to create video writer")

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            results = model(frame)
            result_frame = results[0].plot()
            out.write(result_frame)

        cap.release()
        out.release()

        # Clean up uploaded file
        video_path.unlink()

        # Return processed video with appropriate headers
        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="processed_{file.filename}"',
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache"
            }
        )

    except Exception as e:
        # Clean up any partial files
        if video_path.exists():
            video_path.unlink()
        if 'output_path' in locals() and output_path.exists():
            output_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}

@app.get("/outputs/{filename}")
async def get_processed_video(filename: str):
    video_path = OUTPUTS_DIR / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    # Return video with appropriate headers for streaming
    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
            "Content-Disposition": f'inline; filename="{filename}"'
        }
    )

# Optional: Add route for checking available codecs
@app.get("/check_codecs")
async def check_codecs():
    """Debug endpoint to check available codecs"""
    test_codecs = ['avc1', 'H264', 'X264', 'XVID', 'MJPG']
    available_codecs = {}
    for codec in test_codecs:
        try:
            test = cv2.VideoWriter_fourcc(*codec)
            available_codecs[codec] = test is not None
        except Exception as e:
            available_codecs[codec] = False
    return {"available_codecs": available_codecs}