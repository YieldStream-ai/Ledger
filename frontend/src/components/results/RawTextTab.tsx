interface RawTextTabProps {
  text: string;
}

export function RawTextTab({ text }: RawTextTabProps) {
  if (!text) {
    return <p className="text-sm text-gray-500">No text extracted.</p>;
  }

  return (
    <pre className="text-xs font-mono text-gray-800 bg-gray-50 rounded-lg p-4 overflow-auto max-h-[600px] whitespace-pre-wrap break-words">
      {text}
    </pre>
  );
}
