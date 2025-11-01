'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function UploadPage() {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{ success: boolean; message: string } | null>(null);
  const router = useRouter();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      setUploadStatus({ success: false, message: 'Only PDF files are accepted.' });
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setUploadStatus({ success: false, message: 'File size must be less than 50MB.' });
      return;
    }

    try {
      setUploading(true);
      setUploadStatus(null);

      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_URL}/contracts/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadStatus({
        success: true,
        message: `Contract uploaded successfully! Processing started. Contract ID: ${response.data.contract_id}`,
      });

      // Redirect to contract detail after 2 seconds
      setTimeout(() => {
        router.push(`/contracts/${response.data.contract_id}`);
      }, 2000);
    } catch (error: any) {
      setUploadStatus({
        success: false,
        message: error.response?.data?.detail || 'Failed to upload contract. Please try again.',
      });
    } finally {
      setUploading(false);
    }
  }, [router]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: false,
    maxSize: 50 * 1024 * 1024,
  });

  return (
    <div className="flex min-h-screen bg-white">
      <Sidebar />
      
      <div className="flex-1 flex flex-col">
        <Header 
          searchTerm=""
          onSearchChange={() => {}}
          onSearch={() => {}}
          onRefresh={() => {}}
        />
        
        <main className="flex-1 p-8 overflow-auto">
          <h1 className="text-3xl font-bold text-gray-800 mb-8">Upload Contract</h1>
          
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
            }`}
          >
            <input {...getInputProps()} />
            
            <div className="flex flex-col items-center">
              <svg
                className="w-16 h-16 text-gray-400 mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              
              {isDragActive ? (
                <p className="text-lg text-gray-700 mb-2">Drop the PDF file here</p>
              ) : (
                <>
                  <p className="text-lg text-gray-700 mb-2">
                    Drag and drop a PDF contract here, or click to select
                  </p>
                  <p className="text-sm text-gray-500">
                    Maximum file size: 50MB
                  </p>
                </>
              )}
            </div>
          </div>

          {uploading && (
            <div className="mt-6 text-center text-gray-600">
              Uploading and processing contract...
            </div>
          )}

          {uploadStatus && (
            <div
              className={`mt-6 p-4 rounded-lg ${
                uploadStatus.success
                  ? 'bg-green-50 text-green-800 border border-green-200'
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}
            >
              {uploadStatus.message}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

