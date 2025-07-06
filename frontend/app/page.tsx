"use client";
import { useState, useEffect } from "react";
import type { Hash } from "./lib/imageHash";
import { computeHash, hamming } from "./lib/imageHash";
import Button from "@mui/material/Button";
import Slider from "@mui/material/Slider";
import CircularProgress from "@mui/material/CircularProgress";

export default function Home() {
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [groups, setGroups] = useState<{
    hash: Hash;
    urls: string[];
    files: File[];
  }[]>([]);
  const [autoAlign, setAutoAlign] = useState(false);
  const [antiGhost, setAntiGhost] = useState(false);
  const [contrast, setContrast] = useState(1.0);
  const [saturation, setSaturation] = useState(1.0);

  const handleFilesChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files;
    groups.forEach((g) => g.urls.forEach((u) => URL.revokeObjectURL(u)));
    if (f) {
      const newGroups: { hash: Hash; urls: string[]; files: File[] }[] = [];
      for (const file of Array.from(f)) {
        const url = URL.createObjectURL(file);
        const hash = await computeHash(file);
        let group = newGroups.find((g) => hamming(g.hash, hash) <= 10);
        if (!group) {
          group = { hash, urls: [], files: [] };
          newGroups.push(group);
        }
        group.urls.push(url);
        group.files.push(file);
      }
      setGroups(newGroups);
    } else {
      setGroups([]);
    }
  };

  const handleCreateHDR = async (group: { files: File[] }) => {
    if (group.files.length === 0) return;
    const formData = new FormData();
    group.files.forEach((f) => formData.append("images", f));
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
      groups.forEach((g) => g.urls.forEach((u) => URL.revokeObjectURL(u)));
    };
  }, [groups]);

  return (
    <main className="flex p-4 gap-4">
      <div className="flex w-full gap-4">
        {/* Left column: file input and grouped previews */}
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
              Import Images
            </Button>
          </label>
          {groups.length > 0 && (
            <div className="border rounded-lg p-2 w-full">
              {groups.map((g, idx) => (
                <div key={idx} className="mb-4">
                  <h3 className="text-sm font-semibold mb-1">Group {idx + 1}</h3>
                  <div className="grid grid-cols-2 gap-2 mb-2">
                    {g.urls.map((src) => (
                      <img
                        key={src}
                        src={src}
                        className="w-24 h-24 object-cover rounded-lg"
                      />
                    ))}
                  </div>
                  <Button size="small" variant="contained" onClick={() => handleCreateHDR(g)}>
                    Create HDR
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Middle column: settings and result */}
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
          {resultUrl && (
            <div className="mt-4 flex flex-col items-center gap-2">
              <img src={resultUrl} className="w-96 rounded" />
              <a href={resultUrl} download="hdr_result.jpg">
                <Button variant="outlined">Download Result</Button>
              </a>
            </div>
          )}
        </div>

        {/* Right column: loader */}
        <div className="flex flex-col items-start gap-4 w-1/3">
          {loading && <CircularProgress />}
        </div>
      </div>
    </main>
  );
}
