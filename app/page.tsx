'use client';

import { useState, useEffect, useRef } from 'react';
import Upload from './components/upload';
import ChatWindow from './components/chat';
import ReasoningLog from './components/log';
import { v4 as uuidv4 } from 'uuid';

export default function Home() {
  const [logs, setLogs] = useState<string[]>([]);
  const [chatMessages, setChatMessages] = useState<string[]>([]);
  const sessionIdRef = useRef<string | null>(null);

  useEffect(() => {
    let sessionId = localStorage.getItem('session_id');
    if (!sessionId) {
      sessionId = uuidv4();
      localStorage.setItem('session_id', sessionId);
    }
    sessionIdRef.current = sessionId;
  }, []);

  const handlePDFUpload = async (
    file: File,
    setStatus: (status: string, message?: string) => void
  ) => {
    console.log('Uploading and Embedding PDF:', file.name);
    setStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);
  
    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });
  
      if (!response.ok) {
        setStatus('error', 'Upload failed');
        throw new Error('Upload failed');
      }
  
      const data = await response.json();
      setStatus('uploaded', data.message);
      setLogs((prev) => [...prev, `Upload successful: ${data.message}`]);
    } catch (error) {
      setStatus('error', 'Upload error');
      setLogs((prev) => [...prev, `Upload error: ${error}`]);
    }
  };

  const handleUserMessage = async (msg: string) => {
    setLogs((prev) => [...prev, `Received message: ${msg}`, 'Thinking...']);
    setChatMessages((prev) => [...prev, `🧑 You: ${msg}`]);
  
    try {
      const sessionId = sessionIdRef.current;
      const response = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ question: msg, session_id: sessionId ?? '' }),
      });
  
      if (!response.ok) {
        throw new Error('Failed to get answer');
      }
  
      const data = await response.json();
  
      if (data.clarification) {
        setChatMessages((prev) => [...prev, `🤖 Agent: ${data.clarification}`]);
      } else if (data.answer) {
        setChatMessages((prev) => [...prev, `🤖 Agent: ${data.answer}`]);
      }
  
      setLogs((prev) => [
        ...prev.filter(line => line !== 'Thinking...'),
        ...(data.reasoning_log || []).map((line: string) => `Reasoning: ${line}`),
        data.answer ? `Answer: ${data.answer}` : undefined,
      ].filter(Boolean));
    } catch (error) {
      setLogs((prev) => [...prev, `Error: ${error}`]);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <Upload onUpload={handlePDFUpload} />
      <div className="grid grid-cols-2 gap-4 h-[70vh]">
        <ChatWindow onSend={handleUserMessage} messages={chatMessages} />
        <ReasoningLog logs={logs} />
      </div>
    </div>
  );
}
