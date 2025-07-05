"use client";
import { useState, useEffect } from "react";
import Button from "@mui/material/Button";
import Slider from "@mui/material/Slider";
import CircularProgress from "@mui/material/CircularProgress";

export default function Home() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [previews, setPreviews] = useState<string[]>([]);
  const [autoAlign, setAutoAlign] = useState(false);
  const [antiGhost, setAntiGhost] = useState(false);
  const [contrast, setContrast] = useState(1.0);
  const [saturation, setSaturation] = useState(1.0);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!files || files.length === 0) return;
    const formData = new FormData();
    Array.from(files).forEach((f) => formData.append("images", f));
      formData.append("autoAlign", autoAlign ? "1" : "0");
      formData.append("antiGhost", antiGhost ? "1" : "0");
      formData.append("contrast", (2 - contrast).toString());
      formData.append("saturation", (2 - saturation).toString());
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
    <main className="flex p-4 gap-4">
      <form onSubmit={handleSubmit} className="flex w-full gap-4">
        {/* Left column: file input and previews */}
        <div className="flex flex-col items-start gap-4 w-1/3">
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
              Select Images
            </Button>
          </label>
          {previews.length > 0 && (
            <div className="border rounded-lg p-2">
              <div className="grid grid-cols-2 gap-2">
                {previews.map((src) => (
                  <img key={src} src={src} className="w-24 h-24 object-cover rounded-lg" />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Middle column: settings */}
        <div className="flex flex-col items-center justify-start flex-1">
          <div className="border rounded-lg p-4 w-full max-w-sm mx-auto flex flex-col items-center gap-4">
            <h2 className="text-lg font-semibold">Settings</h2>
            <ol className="list-decimal pl-5 space-y-2 w-full">
              <li>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={autoAlign}
                    onChange={(e) => setAutoAlign(e.target.checked)}
                  />
                  Auto Alignment
                </label>
              </li>
              <li>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={antiGhost}
                    onChange={(e) => setAntiGhost(e.target.checked)}
                  />
                  Anti-Ghosting
                </label>
              </li>
              <li>
                <div className="w-full">
                  <label htmlFor="contrast-slider" className="block text-sm mb-1">
                    Contrast: {contrast.toFixed(2)}
                  </label>
                  <Slider
                    id="contrast-slider"
                    min={0}
                    max={2}
                    step={0.05}
                    value={contrast}
                    onChange={(_, v) => setContrast(v as number)}
                  />
                </div>
              </li>
              <li>
                <div className="w-full">
                  <label htmlFor="saturation-slider" className="block text-sm mb-1">
                    Saturation: {saturation.toFixed(2)}
                  </label>
                  <Slider
                    id="saturation-slider"
                    min={0}
                    max={2}
                    step={0.05}
                    value={saturation}
                    onChange={(_, v) => setSaturation(v as number)}
                  />
                </div>
              </li>
            </ol>
          </div>
        </div>

        {/* Right column: create button and result */}
        <div className="flex flex-col items-end gap-4 w-1/3">
          <Button type="submit" variant="contained">
            Create HDR
          </Button>
          {loading && <CircularProgress />}
          {resultUrl && (
            <div className="flex flex-col items-end gap-2">
              <img src={resultUrl} className="w-48 rounded" />
              <a href={resultUrl} download="hdr_result.jpg">
                <Button variant="outlined">Download Result</Button>
              </a>
            </div>
          )}
        </div>
      </form>
    </main>
  );
}
