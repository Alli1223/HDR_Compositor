"use client";
import { useState, useEffect } from "react";
import type { Hash } from "./lib/imageHash";
import { computeHash, hamming } from "./lib/imageHash";
import Button from "@mui/material/Button";
import Slider from "@mui/material/Slider";
import CircularProgress from "@mui/material/CircularProgress";

type Settings = {
  autoAlign: boolean;
  antiGhost: boolean;
  contrast: number;
  saturation: number;
};

type Group = {
  hash: Hash;
  urls: string[];
  files: File[];
  resultUrl?: string;
  settings: Settings;
};

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [groups, setGroups] = useState<Group[]>([]);
  const [dragging, setDragging] = useState(false);

  const resetURLs = (gs: Group[]) => {
    gs.forEach((g) => {
      g.urls.forEach((u) => URL.revokeObjectURL(u));
      if (g.resultUrl) URL.revokeObjectURL(g.resultUrl);
    });
  };

  const handleFiles = async (files: FileList | File[]) => {
    resetURLs(groups);
    if (!files || files.length === 0) {
      setGroups([]);
      return;
    }
    const newGroups: Group[] = [];
    for (const file of Array.from(files)) {
      const url = URL.createObjectURL(file);
      const hash = await computeHash(file);
      let group = newGroups.find((g) => hamming(g.hash, hash) <= 10);
      if (!group) {
        group = {
          hash,
          urls: [],
          files: [],
          settings: { autoAlign: false, antiGhost: false, contrast: 1, saturation: 1 },
        };
        newGroups.push(group);
      }
      group.urls.push(url);
      group.files.push(file);
    }
    setGroups(newGroups);
  };

  const handleFilesChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files;
    if (f) await handleFiles(f);
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
    if (e.dataTransfer.files) {
      await handleFiles(e.dataTransfer.files);
    }
  };

  const handleCreateHDR = async (index: number) => {
    const group = groups[index];
    if (!group || group.files.length === 0) return;
    const { autoAlign, antiGhost, contrast, saturation } = group.settings;
    const formData = new FormData();
    group.files.forEach((f) => formData.append("images", f));
    formData.append("autoAlign", autoAlign ? "1" : "0");
    formData.append("antiGhost", antiGhost ? "1" : "0");
    formData.append("contrast", (2 - contrast).toString());
    formData.append("saturation", (2 - saturation).toString());
    setLoading(true);
    const res = await fetch("/api/process", { method: "POST", body: formData });
    setLoading(false);
    if (res.ok) {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setGroups((gs) => {
        const copy = [...gs];
        const prev = copy[index].resultUrl;
        if (prev) URL.revokeObjectURL(prev);
        copy[index] = { ...copy[index], resultUrl: url };
        return copy;
      });
    } else {
      alert(await res.text());
    }
  };

  const handleCreateAll = async () => {
    for (let i = 0; i < groups.length; i++) {
      await handleCreateHDR(i);
    }
  };

  useEffect(() => {
    return () => {
      resetURLs(groups);
    };
  }, [groups]);

  const renderSettings = (index: number) => {
    const g = groups[index];
    const s = g.settings;
    return (
      <div className="border rounded-lg p-4 my-2 flex flex-col gap-4">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={s.autoAlign}
            onChange={(e) =>
              setGroups((gs) => {
                const copy = [...gs];
                copy[index].settings.autoAlign = e.target.checked;
                return copy;
              })
            }
          />
          Auto Alignment
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={s.antiGhost}
            onChange={(e) =>
              setGroups((gs) => {
                const copy = [...gs];
                copy[index].settings.antiGhost = e.target.checked;
                return copy;
              })
            }
          />
          Anti-Ghosting
        </label>
        <div>
          <label htmlFor={`contrast-${index}`} className="block text-sm mb-1">
            Contrast: {s.contrast.toFixed(2)}
          </label>
          <Slider
            id={`contrast-${index}`}
            min={0}
            max={2}
            step={0.05}
            value={s.contrast}
            onChange={(_, v) =>
              setGroups((gs) => {
                const copy = [...gs];
                copy[index].settings.contrast = v as number;
                return copy;
              })
            }
          />
        </div>
        <div>
          <label htmlFor={`saturation-${index}`} className="block text-sm mb-1">
            Saturation: {s.saturation.toFixed(2)}
          </label>
          <Slider
            id={`saturation-${index}`}
            min={0}
            max={2}
            step={0.05}
            value={s.saturation}
            onChange={(_, v) =>
              setGroups((gs) => {
                const copy = [...gs];
                copy[index].settings.saturation = v as number;
                return copy;
              })
            }
          />
        </div>
      </div>
    );
  };

  return (
    <main className="flex flex-col items-center p-4 gap-4">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center w-full max-w-xl cursor-pointer ${
          dragging ? "bg-gray-100" : ""
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setDragging(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setDragging(false);
        }}
        onDrop={handleDrop}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <p>Drag and drop images here or click to import</p>
        <input
          id="file-input"
          type="file"
          multiple
          accept="image/*"
          className="hidden"
          onChange={handleFilesChange}
        />
      </div>

      {groups.length === 1 && (
        <div className="w-full max-w-xl">
          <div className="grid grid-cols-3 gap-2 mb-2">
            {groups[0].urls.map((src) => (
              <img key={src} src={src} className="w-24 h-24 object-cover rounded-lg" />
            ))}
          </div>
          {renderSettings(0)}
          <div className="flex items-center gap-2">
            <Button variant="contained" onClick={() => handleCreateHDR(0)}>
              Create HDR
            </Button>
            {groups[0].resultUrl && (
              <a href={groups[0].resultUrl} download="hdr_result.jpg">
                <Button variant="outlined" size="small">
                  Download
                </Button>
              </a>
            )}
          </div>
        </div>
      )}

      {groups.length > 1 && (
        <div className="w-full max-w-xl">
          {groups.map((g, idx) => (
            <div key={idx} className="border rounded-lg p-4 mb-4">
              <h3 className="text-sm font-semibold mb-2">Group {idx + 1}</h3>
              <div className="grid grid-cols-3 gap-2 mb-2">
                {g.urls.map((src) => (
                  <img key={src} src={src} className="w-24 h-24 object-cover rounded-lg" />
                ))}
              </div>
              <details className="mb-2">
                <summary>
                  <Button variant="outlined" size="small">
                    Settings
                  </Button>
                </summary>
                {renderSettings(idx)}
              </details>
              <div className="flex items-center gap-2">
                <Button variant="contained" size="small" onClick={() => handleCreateHDR(idx)}>
                  Create HDR
                </Button>
                {g.resultUrl && (
                  <a href={g.resultUrl} download={`hdr_group_${idx + 1}.jpg`}>
                    <Button size="small" variant="outlined">
                      Download
                    </Button>
                  </a>
                )}
              </div>
            </div>
          ))}
          <div className="flex justify-end">
            <Button variant="contained" onClick={handleCreateAll}>
              Create All
            </Button>
          </div>
        </div>
      )}

      {loading && <CircularProgress />}
    </main>
  );
}
