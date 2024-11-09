import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import VideoUploader from './VideoUploader';

function App() {
  return (
    <Router>
    <Routes>
        <Route path="/" element={<VideoUploader />} />
        </Routes>
        </Router>
    
  );
}

export default App;