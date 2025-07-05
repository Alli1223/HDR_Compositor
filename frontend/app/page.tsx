"use client";
import { useState, useEffect } from "react";
import Button from "@mui/material/Button";

export default function Home() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [previews, setPreviews] = useState<string[]>([]);
  const [ghostLevel, setGhostLevel] = useState(0);
  const [autoAlign, setAutoAlign] = useState(false);

  const handleFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files;
    setFiles(f);
    previews.forEach((u) => URL.revokeObjectURL(u));
    if (f) {
      setPreviews(Array.from(f).map((file) => URL.createObjectURL(file)));
    } else {
      setPreviews([]);
    }
  };

  const handleGhostChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setGhostLevel(parseFloat(e.target.value));
  };

  const handleAlignChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAutoAlign(e.target.checked);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!files || files.length === 0) return;
    const formData = new FormData();
    Array.from(files).forEach((f) => formData.append("images", f));
    formData.append("ghost", ghostLevel.toString());
    formData.append("align", autoAlign ? "1" : "0");
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

  useEffect(() => {
    return () => {
      previews.forEach((u) => URL.revokeObjectURL(u));
    };
  }, [previews]);

  return (
    <main className="flex flex-col items-center p-4 gap-4">
      <form onSubmit={handleSubmit} className="flex flex-col items-center gap-4">
        <input
          id="file-input"
          type="file"
          multiple
          accept="image/*"
          onChange={handleFilesChange}
          className="hidden"
        />
        <label htmlFor="file-input">
          <Button variant="contained" component="span">
            Choose Images
          </Button>
        </label>
        <label className="flex items-center gap-2">
          Ghost Removal
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={ghostLevel}
            onChange={handleGhostChange}
          />
          <span>{ghostLevel.toFixed(1)}</span>
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={autoAlign} onChange={handleAlignChange} />
          Auto Align
        </label>
        <Button type="submit" variant="contained">
          Create HDR
        </Button>
      </form>
      {previews.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {previews.map((src) => (
            <img key={src} src={src} className="h-32 object-cover rounded" />
          ))}
        </div>
      )}
      {loading && <p>Processing...</p>}
      {resultUrl && (
        <a href={resultUrl} download="hdr_result.jpg" className="underline text-blue-600">
          Download Result
        </a>
      )}
    </main>
  );
}
