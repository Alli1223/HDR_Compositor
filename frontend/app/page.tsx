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
import Tooltip from "@mui/material/Tooltip";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import HourglassEmptyIcon from "@mui/icons-material/HourglassEmpty";
import AutorenewIcon from "@mui/icons-material/Autorenew";
import DeleteIcon from "@mui/icons-material/Delete";
import SwapHorizIcon from "@mui/icons-material/SwapHoriz";

// Prefix API requests and returned download URLs when the application is served
// behind a reverse proxy. The value is injected at build time via the
// NEXT_PUBLIC_BASE_PATH environment variable and defaults to an empty string.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

type Settings = {
  autoAlign: boolean;
  antiGhost: boolean;
  contrast: number;
  saturation: number;
  algorithm: "mantiuk" | "reinhard" | "drago";
};

type Result = { url: string; settings: Settings };

type Group = {
  hash: Hash;
  urls: string[];
  files: File[];
  results: Result[];
  settings: Settings;
  status?: "idle" | "queued" | "processing" | "done" | "error";
  progress?: number;
  errorMessage?: string;
};

type Algo = "mantiuk" | "reinhard" | "drago";

type QueueItem = { index: number; settings: Settings };

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [groups, setGroups] = useState<Group[]>([]);
  const [dragging, setDragging] = useState(false);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [thumbLoading, setThumbLoading] = useState(false);
  const [thumbProgress, setThumbProgress] = useState(0);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [settingsOpen, setSettingsOpen] = useState<Record<number, boolean>>({});
  const processingRef = useRef(false);

  const statusIcon = (g: Group) => {
    switch (g.status) {
      case "queued":
        return <HourglassEmptyIcon fontSize="small" color="action" />;
      case "processing":
        return (
          <AutorenewIcon
            fontSize="small"
            color="primary"
            className="animate-spin"
          />
        );
      case "done":
        return <CheckCircleIcon fontSize="small" color="success" />;
      case "error":
        return (
          <Tooltip title={g.errorMessage || "Error"}>
            <ErrorIcon fontSize="small" color="error" />
          </Tooltip>
        );
      default:
        return null;
    }
  };

  const resetURLs = (gs: Group[]) => {
    gs.forEach((g) => {
      g.results.forEach((r) => {
        if (r.url.startsWith("blob:")) {
          URL.revokeObjectURL(r.url);
        }
      });
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
          results: [],
          settings: {
            autoAlign: false,
            antiGhost: false,
            contrast: 1,
            saturation: 1,
            algorithm: "mantiuk",
          },
          status: "idle",
          progress: 0,
          errorMessage: undefined,
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

  const enqueueHDR = (index: number, algorithm?: Algo) => {
    const settingsSnapshot = {
      ...groups[index].settings,
      ...(algorithm ? { algorithm } : {}),
    };
    setQueue((q) => [...q, { index, settings: settingsSnapshot }]);
    setGroups((gs) => {
      const copy = [...gs];
      if (copy[index].status !== "processing") {
        copy[index].status = "queued";
        copy[index].progress = 0;
        copy[index].errorMessage = undefined;
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
      g.results.forEach((r, j) => {
        const name =
          groups.length === 1 && g.results.length === 1
            ? "hdr_result.jpg"
            : `hdr_batch_${idx + 1}_${j + 1}.jpg`;
        triggerDownload(r.url, name);
      });
    });
  };

  const handleAddImages = async (index: number, files: FileList | null) => {
    if (!files) return;
    const arr = Array.from(files);
    for (const file of arr) {
      const url = await createThumbnail(file);
      setGroups((gs) => {
        const copy = [...gs];
        copy[index].urls.push(url);
        copy[index].files.push(file);
        return copy;
      });
    }
  };

  const handleReplaceImage = async (
    groupIndex: number,
    imgIndex: number,
    file: File
  ) => {
    const url = await createThumbnail(file);
    setGroups((gs) => {
      const copy = [...gs];
      copy[groupIndex].urls[imgIndex] = url;
      copy[groupIndex].files[imgIndex] = file;
      return copy;
    });
  };

  const handleRemoveImage = (groupIndex: number, imgIndex: number) => {
    setGroups((gs) => {
      const copy = [...gs];
      const g = copy[groupIndex];
      g.urls.splice(imgIndex, 1);
      g.files.splice(imgIndex, 1);
      if (g.urls.length === 0) {
        copy.splice(groupIndex, 1);
      }
      return copy;
    });
  };

  const assignUnmatched = (fromIndex: number, toIndex: number) => {
    setGroups((gs) => {
      const copy = [...gs];
      const item = copy[fromIndex];
      if (!item || !copy[toIndex]) return copy;
      copy[toIndex].urls.push(item.urls[0]);
      copy[toIndex].files.push(item.files[0]);
      copy.splice(fromIndex, 1);
      return copy;
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
    const { index, settings } = queue[0];
    processingRef.current = true;
    setGroups((gs) => {
      const copy = [...gs];
      copy[index].status = "processing";
      return copy;
    });
    const run = async () => {
      const g = groups[index];
      const { autoAlign, antiGhost, contrast, saturation, algorithm } = settings;
      const formData = new FormData();
      g.files.forEach((f) => formData.append("images", f));
      formData.append("autoAlign", autoAlign ? "1" : "0");
      formData.append("antiGhost", antiGhost ? "1" : "0");
      formData.append("contrast", (2 - contrast).toString());
      formData.append("saturation", (2 - saturation).toString());
      formData.append("algorithm", algorithm);
      setLoading(true);
      try {
        const res = await fetch(`${basePath}/api/process`, {
          method: "POST",
          body: formData,
        });
        if (!res.ok || !res.body) throw new Error("request failed");
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let done = false;
        let resultUrl: string | null = null;
        let currentEvent = "";
        let errorMsg = "";
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
                // Server returns a relative download URL
                resultUrl = valueStr;
              } else if (currentEvent === "error") {
                errorMsg += valueStr + "\n";
              }
            }
          }
        }
        if (resultUrl) {
          setGroups((gs) => {
            const copy = [...gs];
            const settingsCopy = { ...settings };
            copy[index].results.push({ url: resultUrl!, settings: settingsCopy });
            copy[index].status = "done";
            copy[index].progress = 100;
            return copy;
          });
        } else {
          setGroups((gs) => {
            const copy = [...gs];
            copy[index].status = "error";
            copy[index].errorMessage = errorMsg.trim() || "Unknown error";
            return copy;
          });
        }
      } catch (e) {
        setGroups((gs) => {
          const copy = [...gs];
          copy[index].status = "error";
          copy[index].errorMessage = String(e);
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
      <Paper variant="outlined" className="p-4 my-2 flex flex-col gap-4">
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
        <div>
          <label className="block text-sm mb-1">Tone Mapping</label>
          <div className="flex gap-2" role="radiogroup">
            {(["mantiuk", "reinhard", "drago"] as const).map((opt) => (
              <label key={opt} className="flex items-center gap-1 text-sm">
                <input
                  type="radio"
                  name={`algorithm-${index}`}
                  value={opt}
                  checked={s.algorithm === opt}
                  onChange={() =>
                    setGroups((gs) => {
                      const copy = [...gs];
                      copy[index].settings.algorithm = opt;
                      return copy;
                    })
                  }
                />
                {opt}
              </label>
            ))}
          </div>
        </div>
        <Button
          variant="outlined"
          size="small"
          onClick={() =>
            (["mantiuk", "reinhard", "drago"] as const).forEach((algo) =>
              enqueueHDR(index, algo)
            )
          }
        >
          Create All Mapping Options
        </Button>
      </Paper>
    );
  };

  const allResults = groups.flatMap((g) => g.results);
  const currentUrl =
    selectedIndex !== null ? allResults[selectedIndex]?.url ?? null : null;
  const matched = groups
    .map((g, idx) => ({ g, idx }))
    .filter(({ g }) => g.urls.length > 1);
  const unmatched = groups
    .map((g, idx) => ({ g, idx }))
    .filter(({ g }) => g.urls.length === 1);

  useEffect(() => {
    if (selectedIndex === null) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        setSelectedIndex((i) =>
          i === null ? null : (i - 1 + allResults.length) % allResults.length
        );
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        setSelectedIndex((i) =>
          i === null ? null : (i + 1) % allResults.length
        );
      } else if (e.key === "Escape") {
        setSelectedIndex(null);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selectedIndex, allResults.length]);

  return (
    <main className="flex flex-col items-center p-4 gap-4 pb-32">
      <h1 className="text-3xl font-bold">
        AEB <span role="img" aria-label="arrow">➡️</span> HDR Compositor
      </h1>
      <p className="text-center max-w-xl">
        Select your bracketed images to merge them into a single high dynamic
        range photo.
      </p>

      <Paper
        elevation={3}
        className={`p-8 text-center w-full max-w-xl cursor-pointer ${
          dragging ? "bg-gray-100" : ""
        }`}
        sx={{ borderStyle: "dashed", borderWidth: 2, borderColor: "primary.main" }}
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
      </Paper>

      {thumbLoading && (
        <div className="w-full max-w-xl mt-2">
          <LinearProgress variant="determinate" value={thumbProgress} />
        </div>
      )}

      {queue.length > 0 && (
        <Paper className="w-full max-w-xl p-2" elevation={3}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Processing Queue
          </Typography>
          <List dense disablePadding>
            {queue.map((item, i) => (
              <ListItem key={i} sx={{ display: "block" }}>
                <ListItemText
                  primary={`Batch ${item.index + 1} (${item.settings.algorithm})`}
                  secondary={groups[item.index].status}
                />
                {i === 0 && groups[item.index].status === "processing" && (
                  <LinearProgress
                    sx={{ mt: 1 }}
                    variant="determinate"
                    value={groups[item.index].progress ?? 0}
                  />
                )}
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {matched.length === 1 && (
        <div className="w-full max-w-2xl grid gap-4">
          <div className="grid md:grid-cols-2 gap-4">
            <Paper className="relative p-4 flex flex-col gap-4" elevation={3}>
              <div className="absolute top-2 right-2">
                {statusIcon(matched[0].g)}
              </div>
              <div className="grid grid-cols-3 gap-2">
                {matched[0].g.urls.map((src, i) => (
                  <div key={src} className="relative group">
                    <img src={src} className="w-16 h-16 object-cover rounded-lg" />
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100">
                      <label className="cursor-pointer text-white">
                        <SwapHorizIcon fontSize="small" />
                        <input
                          type="file"
                          className="hidden"
                          onChange={(e) => {
                            const f = e.target.files?.[0];
                            if (f) handleReplaceImage(matched[0].idx, i, f);
                          }}
                        />
                      </label>
                      <button onClick={() => handleRemoveImage(matched[0].idx, i)} className="text-white">
                        <DeleteIcon fontSize="small" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              <div>
                <label className="text-sm text-blue-600 cursor-pointer">
                  Add Images
                  <input
                    type="file"
                    multiple
                    className="hidden"
                    onChange={(e) => handleAddImages(matched[0].idx, e.target.files)}
                  />
                </label>
              </div>
              <div className="mt-auto pt-2 border-t border-gray-300 flex items-start justify-between gap-2">
                <div>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() =>
                      setSettingsOpen((o) => ({ ...o, [matched[0].idx]: !o[matched[0].idx] }))
                    }
                  >
                    Settings
                  </Button>
                  {settingsOpen[matched[0].idx] && renderSettings(matched[0].idx)}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="contained"
                    onClick={() => enqueueHDR(matched[0].idx)}
                    disabled={matched[0].g.status === "processing"}
                  >
                    {matched[0].g.status === "processing" ? (
                      <CircularProgress size={24} color="inherit" />
                    ) : (
                      "Create HDR"
                    )}
                  </Button>
                  {matched[0].g.status === "processing" && (
                    <LinearProgress
                      sx={{ mt: 1 }}
                      variant="determinate"
                      value={matched[0].g.progress ?? 0}
                    />
                  )}
                </div>
              </div>
            </Paper>
            {matched[0].g.results.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {(() => {
                  const r = matched[0].g.results[matched[0].g.results.length - 1];
                  return r ? (
                    <Paper className="flex flex-col items-center gap-2 p-2" elevation={3}>
                      <Typography variant="subtitle2">HDR Result {matched[0].g.results.length}</Typography>
                      <img
                        src={r.url}
                        className="w-48 h-48 object-cover rounded-lg cursor-pointer"
                        onClick={() => setSelectedIndex(allResults.indexOf(r))}
                      />
                      <a href={r.url} download={`hdr_result_${matched[0].g.results.length}.jpg`}>
                        <Button variant="outlined" color="secondary" size="small">Download</Button>
                      </a>
                    </Paper>
                  ) : null;
                })()}
              </div>
            )}
          </div>
        </div>
      )}

      {matched.length > 1 && (
        <div className="w-full max-w-3xl grid gap-4 md:grid-cols-2">
          {matched.map(({ g, idx }) => (
            <Paper key={idx} variant="outlined" className="relative p-4 flex flex-col gap-4">
              <div className="absolute top-2 right-2">{statusIcon(g)}</div>
              <h3 className="text-sm font-semibold mb-2">Batch {idx + 1}</h3>
              <div className="grid md:grid-cols-2 gap-4 flex-grow">
                <div className="grid gap-4">
                  <div className="grid grid-cols-3 gap-2">
                    {g.urls.map((src, i) => (
                      <div key={src} className="relative group">
                        <img src={src} className="w-16 h-16 object-cover rounded-lg" />
                        <div className="absolute inset-0 bg-black/50 flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100">
                          <label className="cursor-pointer text-white">
                            <SwapHorizIcon fontSize="small" />
                            <input
                              type="file"
                              className="hidden"
                              onChange={(e) => {
                                const f = e.target.files?.[0];
                                if (f) handleReplaceImage(idx, i, f);
                              }}
                            />
                          </label>
                          <button onClick={() => handleRemoveImage(idx, i)} className="text-white">
                            <DeleteIcon fontSize="small" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-sm text-blue-600 cursor-pointer">
                    Add Images
                    <input
                      type="file"
                      multiple
                      className="hidden"
                      onChange={(e) => handleAddImages(idx, e.target.files)}
                    />
                  </label>
                </div>
                {g.results.length > 0 && (
                  <div className="flex flex-col gap-2">
                    {(() => {
                      const r = g.results[g.results.length - 1];
                      return r ? (
                        <Paper className="flex flex-col items-center gap-2 p-2" elevation={3}>
                          <Typography variant="subtitle2">HDR Result {g.results.length}</Typography>
                          <img
                            src={r.url}
                            className="w-48 h-48 object-cover rounded-lg cursor-pointer"
                            onClick={() => setSelectedIndex(allResults.indexOf(r))}
                          />
                          <a href={r.url} download={`hdr_batch_${idx + 1}_${g.results.length}.jpg`}>
                            <Button size="small" variant="outlined" color="secondary">Download</Button>
                          </a>
                        </Paper>
                      ) : null;
                    })()}
                  </div>
                )}
              </div>
              <div className="mt-auto pt-2 border-t border-gray-300 flex items-start justify-between gap-2">
                <div>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() =>
                      setSettingsOpen((o) => ({ ...o, [idx]: !o[idx] }))
                    }
                  >
                    Settings
                  </Button>
                  {settingsOpen[idx] && renderSettings(idx)}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => enqueueHDR(idx)}
                    disabled={g.status === "processing"}
                  >
                    {g.status === "processing" ? (
                      <CircularProgress size={24} color="inherit" />
                    ) : (
                      "Create HDR"
                    )}
                  </Button>
                  {g.status === "processing" && (
                    <LinearProgress
                      sx={{ mt: 1 }}
                      variant="determinate"
                      value={g.progress ?? 0}
                    />
                  )}
                </div>
              </div>
            </Paper>
          ))}
        </div>
      )}

      {unmatched.length > 0 && (
        <Paper variant="outlined" className="p-4 w-full max-w-xl">
          <h3 className="text-sm font-semibold mb-2">Unmatched</h3>
          <div className="grid grid-cols-3 gap-4">
            {unmatched.map(({ g, idx }) => (
              <div key={idx} className="flex flex-col items-center gap-1">
                <div className="relative group">
                  <img src={g.urls[0]} className="w-16 h-16 object-cover rounded-lg" />
                  <div className="absolute inset-0 bg-black/50 flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100">
                    <label className="cursor-pointer text-white">
                      <SwapHorizIcon fontSize="small" />
                      <input
                        type="file"
                        className="hidden"
                        onChange={(e) => {
                          const f = e.target.files?.[0];
                          if (f) handleReplaceImage(idx, 0, f);
                        }}
                      />
                    </label>
                    <button onClick={() => handleRemoveImage(idx, 0)} className="text-white">
                      <DeleteIcon fontSize="small" />
                    </button>
                  </div>
                </div>
                {matched.length > 0 && (
                  <select
                    className="text-sm border rounded"
                    defaultValue=""
                    onChange={(e) => {
                      const val = parseInt(e.target.value);
                      if (!isNaN(val)) assignUnmatched(idx, val);
                    }}
                  >
                    <option value="" disabled>
                      Move to...
                    </option>
                    {matched.map(({ idx: mi }) => (
                      <option key={mi} value={mi}>
                        Batch {mi + 1}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            ))}
          </div>
        </Paper>
      )}

      {groups.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 z-20 bg-white/90 dark:bg-gray-900/90 backdrop-blur p-2 flex items-center">
          <div className="flex gap-2 justify-center flex-grow overflow-x-auto">
            {allResults.map((r, i) => (
              <img
                key={i}
                src={r.url}
                className="h-16 w-16 object-cover rounded-lg cursor-pointer"
                onClick={() => setSelectedIndex(i)}
              />
            ))}
          </div>
          <div className="flex gap-2 ml-auto">
            <Button variant="contained" onClick={handleCreateAll}>
              Create All
            </Button>
            {groups.some((g) => g.results.length > 0) && (
              <Button variant="outlined" color="secondary" onClick={handleDownloadAll}>
                Download All
              </Button>
            )}
          </div>
        </div>
      )}

      {loading && <CircularProgress />}
      {currentUrl && (
        <div
          className="fixed inset-0 bg-gray-200 bg-opacity-80 flex items-center justify-center z-50"
          onClick={() => setSelectedIndex(null)}
        >
          <img src={currentUrl} className="max-w-full max-h-full" />
        </div>
      )}
      <p className="text-xs text-gray-600 mt-4">
        Uploaded images are stored on the server for up to 1 day and are then
        automatically deleted.
      </p>
    </main>
  );
}
