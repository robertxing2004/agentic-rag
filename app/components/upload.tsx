'use client';

import { useState } from 'react';

export default function UploadPDF({ onUpload }: { onUpload: (file: File) => void }) {
  const [fileName, setFileName] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFileName(e.target.files[0].name);
      onUpload(e.target.files[0]);
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
      {fileName && <p className="mt-2 text-sm text-gray-600">Uploaded: {fileName}</p>}
    </div>
  );
}