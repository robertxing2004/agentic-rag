import { useEffect, useRef } from 'react';

export default function ReasoningLog({ logs }: { logs: string[] }) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="h-full overflow-y-auto p-4 bg-gray-100 rounded-lg shadow text-sm font-mono">
      {logs.map((line, i) => (
        <pre key={i} className="mb-1 text-gray-700 whitespace-pre-wrap">{line}</pre>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
