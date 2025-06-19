'use client';

import { useState } from 'react';

export default function ChatWindow({ onSend }: { onSend: (message: string) => void }) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<string[]>([]);

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages((prev) => [...prev, `🧑 You: ${input}`]);
    onSend(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full p-4 bg-gray-50 rounded-lg shadow">
      <div className="flex-1 overflow-y-auto space-y-2 mb-4">
        {messages.map((msg, i) => (
          <div key={i} className="text-sm bg-white p-2 rounded shadow">
            {msg}
          </div>
        ))}
      </div>
      <div className="flex space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          className="flex-1 px-3 py-2 border rounded-md"
        />
        <button
          onClick={handleSend}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Send
        </button>
      </div>
    </div>
  );
}
