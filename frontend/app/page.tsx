"use client";
import { useState, useEffect, useRef } from "react";
import type { Hash } from "./lib/imageHash";
import { computeHash, hamming, createThumbnail } from "./lib/imageHash";
import Button from "@mui/material/Button";
import Slider from "@mui/material/Slider";
import CircularProgress from "@mui/material/CircularProgress";
import LinearProgress from "@mui/material/LinearProgress";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";

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
  status?: "idle" | "queued" | "processing" | "done" | "error";
  progress?: number;
};

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [groups, setGroups] = useState<Group[]>([]);
  const [dragging, setDragging] = useState(false);
  const [queue, setQueue] = useState<number[]>([]);
  const [thumbLoading, setThumbLoading] = useState(false);
  const [thumbProgress, setThumbProgress] = useState(0);
  const processingRef = useRef(false);

  const resetURLs = (gs: Group[]) => {
    gs.forEach((g) => {
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
    const arr = Array.from(files);
    setThumbLoading(true);
    setThumbProgress(0);
    for (let i = 0; i < arr.length; i++) {
      const file = arr[i];
      const url = await createThumbnail(file);
      const hash = await computeHash(file);
      let group = newGroups.find((g) => hamming(g.hash, hash) <= 10);
      if (!group) {
        group = {
          hash,
          urls: [],
          files: [],
          settings: { autoAlign: false, antiGhost: false, contrast: 1, saturation: 1 },
          status: "idle",
          progress: 0,
        };
        newGroups.push(group);
      }
      group.urls.push(url);
      group.files.push(file);
      setThumbProgress(Math.round(((i + 1) / arr.length) * 100));
    }
    setThumbLoading(false);
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

  const enqueueHDR = (index: number) => {
    setGroups((gs) => {
      const copy = [...gs];
      if (copy[index].status === "idle" || copy[index].status === "error") {
        copy[index].status = "queued";
        copy[index].progress = 0;
        setQueue((q) => [...q, index]);
      }
      return copy;
    });
  };

  const handleCreateAll = async () => {
    groups.forEach((_, i) => enqueueHDR(i));
  };

  const triggerDownload = (url: string, name: string) => {
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
  };

  const handleDownloadAll = () => {
    groups.forEach((g, idx) => {
      if (g.resultUrl) {
        const name = groups.length === 1 ?
          "hdr_result.jpg" : `hdr_group_${idx + 1}.jpg`;
        triggerDownload(g.resultUrl, name);
      }
    });
  };

  // Clean up created object URLs when the component is unmounted
  useEffect(() => {
    return () => {
      resetURLs(groups);
    };
    // Intentionally run only on mount/unmount
  }, []);

  useEffect(() => {
    if (processingRef.current || queue.length === 0) return;
    const index = queue[0];
    processingRef.current = true;
    setGroups((gs) => {
      const copy = [...gs];
      copy[index].status = "processing";
      return copy;
    });
    const run = async () => {
      const g = groups[index];
      const { autoAlign, antiGhost, contrast, saturation } = g.settings;
      const formData = new FormData();
      g.files.forEach((f) => formData.append("images", f));
      formData.append("autoAlign", autoAlign ? "1" : "0");
      formData.append("antiGhost", antiGhost ? "1" : "0");
      formData.append("contrast", (2 - contrast).toString());
      formData.append("saturation", (2 - saturation).toString());
      setLoading(true);
      try {
        const res = await fetch("/api/process", { method: "POST", body: formData });
        if (!res.ok || !res.body) throw new Error("request failed");
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let done = false;
        let resultUrl: string | null = null;
        let currentEvent = "";
        while (!done) {
          const { value, done: doneReading } = await reader.read();
          done = doneReading;
          buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
          let eolIndex;
          while ((eolIndex = buffer.indexOf("\n")) >= 0) {
            const line = buffer.slice(0, eolIndex).trimEnd();
            buffer = buffer.slice(eolIndex + 1);
            if (line === "") {
              // ignore empty separator
              continue;
            }
            const [field, ...rest] = line.split(":");
            const valueStr = rest.join(":").trim();
            if (field === "event") {
              currentEvent = valueStr;
            } else if (field === "data") {
              if (currentEvent === "progress") {
                const pct = parseInt(valueStr, 10);
                setGroups((gs) => {
                  const copy = [...gs];
                  copy[index].progress = pct;
                  return copy;
                });
              } else if (currentEvent === "done") {
                const byteString = atob(valueStr);
                const bytes = new Uint8Array(byteString.length);
                for (let i = 0; i < byteString.length; i++) {
                  bytes[i] = byteString.charCodeAt(i);
                }
                const blob = new Blob([bytes], { type: "image/jpeg" });
                resultUrl = URL.createObjectURL(blob);
              }
            }
          }
        }
        if (resultUrl) {
          setGroups((gs) => {
            const copy = [...gs];
            const prev = copy[index].resultUrl;
            if (prev) URL.revokeObjectURL(prev);
            copy[index] = { ...copy[index], resultUrl, status: "done", progress: 100 };
            return copy;
          });
        } else {
          setGroups((gs) => {
            const copy = [...gs];
            copy[index].status = "error";
            return copy;
          });
        }
      } catch (e) {
        setGroups((gs) => {
          const copy = [...gs];
          copy[index].status = "error";
          return copy;
        });
      }
      setLoading(false);
      setQueue((q) => q.slice(1));
      processingRef.current = false;
    };
    run();
  }, [queue, groups]);

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

      {thumbLoading && (
        <div className="w-full max-w-xl mt-2">
          <LinearProgress variant="determinate" value={thumbProgress} />
        </div>
      )}

      {queue.length > 0 && (
        <Paper className="w-full max-w-xl p-2" elevation={2}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Processing Queue
          </Typography>
          <List dense disablePadding>
            {queue.map((idx, i) => (
              <ListItem key={i} sx={{ display: "block" }}>
                <ListItemText
                  primary={`Group ${idx + 1}`}
                  secondary={groups[idx].status}
                />
                {i === 0 && groups[idx].status === "processing" && (
                  <LinearProgress
                    sx={{ mt: 1 }}
                    variant="determinate"
                    value={groups[idx].progress ?? 0}
                  />
                )}
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {groups.length === 1 && (
        <div className="w-full max-w-xl">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="grid grid-cols-3 gap-2 mb-2">
                {groups[0].urls.map((src) => (
                  <img key={src} src={src} className="w-24 h-24 object-cover rounded-lg" />
                ))}
              </div>
              {renderSettings(0)}
              <Button variant="contained" onClick={() => enqueueHDR(0)}>
                Create HDR
              </Button>
              {groups[0].status && groups[0].status !== "idle" && (
                <>
                  <p className="text-sm mt-1">Status: {groups[0].status}</p>
                  {groups[0].status === "processing" && (
                    <LinearProgress
                      sx={{ mt: 1 }}
                      variant="determinate"
                      value={groups[0].progress ?? 0}
                    />
                  )}
                </>
              )}
            </div>
            {groups[0].resultUrl && (
              <div className="flex flex-col items-center gap-2">
                <img
                  src={groups[0].resultUrl}
                  className="w-32 h-32 object-cover rounded-lg"
                />
                <a href={groups[0].resultUrl} download="hdr_result.jpg">
                  <Button variant="outlined" size="small">Download</Button>
                </a>
              </div>
            )}
          </div>
          {groups[0].resultUrl && (
            <div className="flex justify-end mt-2">
              <Button variant="outlined" onClick={handleDownloadAll}>
                Download All
              </Button>
            </div>
          )}
        </div>
      )}

      {groups.length > 1 && (
        <div className="w-full max-w-xl">
          {groups.map((g, idx) => (
            <div key={idx} className="border rounded-lg p-4 mb-4">
              <h3 className="text-sm font-semibold mb-2">Group {idx + 1}</h3>
              <div className="flex gap-4">
                <div className="flex-1">
                  <div className="grid grid-cols-3 gap-2 mb-2">
                    {g.urls.map((src) => (
                      <img key={src} src={src} className="w-24 h-24 object-cover rounded-lg" />
                    ))}
                  </div>
                  <details className="mb-2">
                    <summary>
                      <Button variant="outlined" size="small">Settings</Button>
                    </summary>
                    {renderSettings(idx)}
                  </details>
                  <Button variant="contained" size="small" onClick={() => enqueueHDR(idx)}>
                    Create HDR
                  </Button>
                  {g.status && g.status !== "idle" && (
                    <>
                      <p className="text-xs mt-1">Status: {g.status}</p>
                      {g.status === "processing" && (
                        <LinearProgress
                          sx={{ mt: 1 }}
                          variant="determinate"
                          value={g.progress ?? 0}
                        />
                      )}
                    </>
                  )}
                </div>
                {g.resultUrl && (
                  <div className="flex flex-col items-center gap-2">
                    <img
                      src={g.resultUrl}
                      className="w-32 h-32 object-cover rounded-lg"
                    />
                    <a href={g.resultUrl} download={`hdr_group_${idx + 1}.jpg`}>
                      <Button size="small" variant="outlined">Download</Button>
                    </a>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div className="flex justify-end gap-2">
            <Button variant="contained" onClick={handleCreateAll}>
              Create All
            </Button>
            {groups.some((g) => g.resultUrl) && (
              <Button variant="outlined" onClick={handleDownloadAll}>
                Download All
              </Button>
            )}
          </div>
        </div>
      )}

      {loading && <CircularProgress />}
    </main>
  );
}
