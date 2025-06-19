'use client';

import { useState } from 'react';
import Upload from './components/upload';
import ChatWindow from './components/chat';
import ReasoningLog from './components/log';

export default function Home() {
  const [logs, setLogs] = useState<string[]>([]);

  const handlePDFUpload = (file: File) => {
    console.log('PDF Uploaded:', file.name);
    // Later: Send to FastAPI backend
  };

  const handleUserMessage = (msg: string) => {
    setLogs((prev) => [...prev, `Received message: ${msg}`, 'Thinking...']);
    // Later: Call backend and update logs with response
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <Upload onUpload={handlePDFUpload} />
      <div className="grid grid-cols-2 gap-4 h-[70vh]">
        <ChatWindow onSend={handleUserMessage} />
        <ReasoningLog logs={logs} />
      </div>
    </div>
  );
}
