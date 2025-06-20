'use client';

import { useState } from 'react';

export default function UploadPDF({ onUpload }: { onUpload: (file: File, setStatus: (status: string, message?: string) => void) => void }) {
  const [fileName, setFileName] = useState('');
  const [status, setStatus] = useState<'idle' | 'uploading' | 'uploaded' | 'error'>('idle');
  const [backendMsg, setBackendMsg] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFileName(e.target.files[0].name);
      setStatus('uploading');
      setBackendMsg('');
      onUpload(e.target.files[0], (newStatus, msg) => {
        setStatus(newStatus as any);
        if (msg) setBackendMsg(msg);
      });
    }
  };

  return (
    <div className="p-4 bg-white shadow-md rounded-lg mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">Upload PDF</label>
      <input
        type="file"
        accept="application/pdf"
        onChange={handleFileChange}
        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4
                   file:rounded-md file:border-0 file:text-sm file:font-semibold
                   file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
      />
      {status === 'uploading' && <p className="mt-2 text-sm text-gray-600">Uploading...</p>}
      {status === 'uploaded' && <p className="mt-2 text-sm text-green-600">{backendMsg || `Uploaded: ${fileName}`}</p>}
      {status === 'error' && <p className="mt-2 text-sm text-red-600">{backendMsg || 'Upload failed.'}</p>}
    </div>
  );
}