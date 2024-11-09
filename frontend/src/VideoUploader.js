import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './VideoUploader.css'; // Import the CSS file

const VideoUploader = () => {
  const [file, setFile] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [serverStatus, setServerStatus] = useState(null);

  useEffect(() => {
    checkServerHealth();
  }, []);

  // Function to check server health
  const checkServerHealth = async () => {
    try {
      const response = await axios.get('http://localhost:8000/health');
      setServerStatus(response.data);
    } catch (error) {
      setServerStatus({ status: "unavailable" });
    }
  };

  // Handle file selection
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      if (!selectedFile.type.startsWith('video/')) {
        setError("Please select a video file");
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError("");
    }
  };

  // Handle video upload
  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file first");
      return;
    }

    setIsLoading(true);
    setError("");
    setDownloadUrl("");

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/upload_video/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',  // Handle response as blob
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          console.log(`Upload Progress: ${percentCompleted}%`);
        }
      });

      const videoUrl = `http://localhost:8000/outputs/processed_${file.name}`;
      setDownloadUrl(videoUrl);


    } catch (error) {
      let errorMessage = "Error uploading video";
      if (error.response) {
        errorMessage = error.response.data.detail || "Server error occurred";
      } else if (error.request) {
        errorMessage = "Cannot connect to server. Please check if the server is running.";
      }
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // Clean up download URL when component unmounts
  useEffect(() => {
    return () => {
      if (downloadUrl) {
        URL.revokeObjectURL(downloadUrl);
      }
    };
  }, [downloadUrl]);

  return (
    <div className="video-uploader-container">
      <div className="video-uploader">
        <h1 className="title">Upload Video for YOLO Processing</h1>

        {serverStatus && serverStatus.status !== "healthy" && (
          <div className="status-error">
            Server is currently unavailable. Please check your connection and try again.
          </div>
        )}

        {error && (
          <div className="status-error">
            {error}
          </div>
        )}

        <div className="input-section">
          <input
            type="file"
            onChange={handleFileChange}
            accept="video/*"
            className="file-input"
          />
          <button
            onClick={handleUpload}
            disabled={!file || isLoading}
            className={`upload-btn ${isLoading || !file ? 'disabled' : ''}`}
          >
            {isLoading ? 'Processing...' : 'Upload and Process'}
          </button>
        </div>

        {downloadUrl && (
          <div className="processed-video-section">
            <h2>Processed Video</h2>
            <video className="video-player" controls>
            <source src={downloadUrl} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
            <a
              href={downloadUrl}
              download="processed_video.mp4"
              className="download-btn"
            >
              Download Processed Video
            </a>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoUploader;
