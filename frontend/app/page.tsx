"use client";
import { useState } from "react";

export default function Home() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!files || files.length === 0) return;
    const formData = new FormData();
    Array.from(files).forEach((f) => formData.append("images", f));
    setLoading(true);
    setResultUrl(null);
    const res = await fetch("/api/process", { method: "POST", body: formData });
    setLoading(false);
    if (res.ok) {
      const blob = await res.blob();
      setResultUrl(URL.createObjectURL(blob));
    } else {
      alert(await res.text());
    }
  };

  return (
    <main className="flex flex-col items-center p-4 gap-4">
      <form onSubmit={handleSubmit} className="flex flex-col items-center gap-4">
        <input type="file" multiple accept="image/*" onChange={(e) => setFiles(e.target.files)} />
        <button type="submit" className="border px-4 py-2">Create HDR</button>
      </form>
      {loading && <p>Processing...</p>}
      {resultUrl && (
        <a href={resultUrl} download="hdr_result.jpg" className="underline text-blue-600">Download Result</a>
      )}
    </main>
  );
}
