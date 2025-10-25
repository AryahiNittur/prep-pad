"use client";

import Image from "next/image";
import { useState } from 'react';

interface StatusState {
  status: 'success' | 'error';
  message: string;
  data?: {
    fileId: string;
    fileName?: string;
  };
}


export default function Home() {
  const [uploading, setUploading] = useState<boolean>(false);
  const [status, setStatus] = useState<StatusState | null>(null);
  const [fileName, setFileName] = useState<string>('');

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    
    if (!file) return;
    
    // Validate file type
    if (file.type !== 'application/pdf') {
      setStatus({ status: 'error', message: 'Please select a PDF file' });
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setStatus({ status: 'error', message: 'File size must be less than 10MB' });
      return;
    }

    setFileName(file.name);
    setUploading(true);
    setStatus(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/upload-pdf', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Upload failed');
      }

      setStatus({
        status: 'success',
        message: `Successfully uploaded: ${file.name}`,
        data: data
      });
    } catch (error) {
      setStatus({
        status: 'error',
        message: error instanceof Error ? error.message : 'Failed to upload file'
      });
    } finally {
      setUploading(false);
      // Reset file input
      e.target.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-rose-50">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <span className="text-2xl font-bold bg-gradient-to-r from-orange-500 to-rose-500 bg-clip-text text-transparent">Prep Pad</span>
            </div>
            <div className="flex items-center gap-6">
              <a href="/" className="text-gray-700 hover:text-indigo-600 font-medium transition-colors">
                Home
              </a>
              <a href="/uploads" className="text-gray-700 hover:text-indigo-600 font-medium transition-colors">
                My Uploads
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] p-8">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full">
          <div className="text-center mb-6">
            <div className="w-16 h-16 mx-auto mb-4 text-indigo-600 text-6xl">📄</div>
            <h1 className="text-2xl font-bold text-gray-800 mb-2">
              PDF Upload
            </h1>
            <p className="text-gray-600 text-sm">
              Upload your PDF file (max 10MB)
            </p>
          </div>

          <label
            htmlFor="pdf-upload"
            className={`
              flex items-center justify-center gap-3 w-full py-4 px-6 rounded-lg
              font-semibold text-white transition-all cursor-pointer
              ${uploading 
                ? 'from-orange-500 to-rose-500 cursor-not-allowed' 
                : 'bg-indigo-600 hover:bg-indigo-700 active:scale-95'
              }
            `}
          >
            <span className="text-xl">⬆️</span>
            {uploading ? 'Uploading...' : 'Choose PDF File'}
          </label>
          
          <input
            id="pdf-upload"
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            disabled={uploading}
            className="hidden"
          />

          {fileName && !status && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-800">
              Selected: {fileName}
            </div>
          )}

          {status && (
            <div
              className={`
                mt-4 p-4 rounded-lg flex items-start gap-3
                ${status.status === 'success' 
                  ? 'bg-green-50 text-green-800' 
                  : 'bg-red-50 text-red-800'
                }
              `}
            >
              <span className="text-xl flex-shrink-0">
                {status.status === 'success' ? '✅' : '⚠️'}
              </span>
              <div className="flex-1">
                <p className="font-medium text-sm">{status.message}</p>
                {status.data && status.data.fileId && (
                  <p className="text-xs mt-1 opacity-80">
                    File ID: {status.data.fileId}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
