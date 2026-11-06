
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Upload,
  FileAudio,
  X,
  CheckCircle2,
  Loader2,
  AlertCircle
} from "lucide-react";

import api from "../services/api";

function UploadAudio() {
  const navigate = useNavigate();
  const inputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [transcriptionStatus, setTranscriptionStatus] = useState("");
  const [transcriptionError, setTranscriptionError] = useState("");
  const [startingTranscription, setStartingTranscription] = useState(false);

  const handleFile = (selectedFile) => {
    setError("");
    setUploadResult(null);
    setProgress(0);
    setTranscriptionStatus("");
    setTranscriptionError("");
    setStartingTranscription(false);

    if (!selectedFile) return;

    const allowedExtensions = ["mp3", "wav", "m4a"];
    const extension = selectedFile.name.split(".").pop().toLowerCase();

    if (!allowedExtensions.includes(extension)) {
      setError("Only MP3, WAV and M4A files are supported.");
      return;
    }

    if (selectedFile.size > 100 * 1024 * 1024) {
      setError("File size must not exceed 100 MB.");
      return;
    }

    if (selectedFile.size === 0) {
      setError("Selected file is empty.");
      return;
    }

    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError("");
    setProgress(0);
    setUploadResult(null);
    setTranscriptionStatus("");
    setTranscriptionError("");
    setStartingTranscription(false);

    const formData = new FormData();

    formData.append("file", file);

    try {
      const response = await api.post(
        "/api/audio/upload",
        formData,
        {
          onUploadProgress: (event) => {
            if (event.total) {
              const percentage = Math.round(
                (event.loaded * 100) / event.total
              );

              setProgress(percentage);
            }
          }
        }
      );

      setUploadResult(response.data.data);
      setProgress(100);
      setFile(null);

      if (inputRef.current) {
        inputRef.current.value = "";
      }

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Audio upload failed. Please try again."
      );

    } finally {
      setLoading(false);
    }
  };

  const handleStartTranscription = async () => {
    if (!uploadResult?.call_id) return;

    try {
      setStartingTranscription(true);
      setTranscriptionError("");

      const response = await api.post(
        `/api/transcription/${uploadResult.call_id}/start`
      );

      setTranscriptionStatus(
        response.data?.data?.transcription_status || "processing"
      );
    } catch (err) {
      setTranscriptionError(
        err.response?.data?.detail || "Unable to start transcription."
      );
    } finally {
      setStartingTranscription(false);
    }
  };

  const formatSize = (bytes) => {
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  };

  useEffect(() => {
    if (!uploadResult?.call_id) return;

    if (
      !["processing"].includes(transcriptionStatus)
    ) {
      return;
    }

    const timer = setInterval(async () => {
      try {
        const response = await api.get(
          `/api/transcription/${uploadResult.call_id}/status`
        );

        const status = response.data?.data?.transcription_status;

        if (status) {
          setTranscriptionStatus(status);
        }

        if (status === "failed") {
          setTranscriptionError(
            response.data?.data?.error || "Transcription failed."
          );
        }
      } catch (err) {
        setTranscriptionError(
          err.response?.data?.detail || "Unable to check transcription status."
        );
      }
    }, 3000);

    return () => clearInterval(timer);
  }, [uploadResult?.call_id, transcriptionStatus]);

  return (
    <div className="space-y-7">

      <div>
        <h1 className="text-2xl font-bold">Upload Audio</h1>
        <p className="text-slate-400 text-sm mt-2">
          Upload customer and executive call recordings
          for AI assessment.
        </p>
      </div>

      <div className="bg-[#111827] border border-slate-800 rounded-2xl p-7">

        <div className="mb-6">
          <h2 className="font-semibold text-lg">Audio Recording</h2>
          <p className="text-sm text-slate-500 mt-1">
            Select an audio recording to begin assessment.
          </p>
        </div>

        <div
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => {
            event.preventDefault();

            if (!loading) {
              handleFile(event.dataTransfer.files[0]);
            }
          }}
          onClick={() => {
            if (!loading) inputRef.current?.click();
          }}
          className="border-2 border-dashed border-slate-700 hover:border-violet-500 rounded-2xl p-12 text-center cursor-pointer transition bg-slate-900/40"
        >
          <div className="w-16 h-16 bg-violet-500/10 rounded-2xl flex items-center justify-center mx-auto mb-5">
            <Upload size={30} className="text-violet-400" />
          </div>

          <h3 className="font-semibold text-lg">
            Drag and drop your audio file
          </h3>

          <p className="text-sm text-slate-500 mt-2">
            or click here to browse files
          </p>

          <p className="text-xs text-slate-600 mt-5">
            MP3, WAV, M4A · Maximum 100 MB
          </p>

          <input
            ref={inputRef}
            type="file"
            accept=".mp3,.wav,.m4a"
            hidden
            disabled={loading}
            onChange={(event) => handleFile(event.target.files[0])}
          />
        </div>

        {file && (
          <div className="mt-6 flex items-center justify-between bg-slate-800/60 border border-slate-700 rounded-xl p-4">

            <div className="flex items-center gap-3">
              <FileAudio className="text-violet-400" size={26} />

              <div>
                <p className="text-sm font-medium break-all">
                  {file.name}
                </p>

                <p className="text-xs text-slate-500 mt-1">
                  {formatSize(file.size)}
                </p>
              </div>
            </div>

            <button
              disabled={loading}
              onClick={(event) => {
                event.stopPropagation();
                setFile(null);
                setError("");
                if (inputRef.current) inputRef.current.value = "";
              }}
              className="text-slate-400 hover:text-rose-400"
            >
              <X size={19} />
            </button>
          </div>
        )}

        {loading && (
          <div className="mt-6 space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-slate-300">
                Uploading audio...
              </span>

              <span className="text-violet-400">
                {progress}%
              </span>
            </div>

            <div className="w-full bg-slate-800 rounded-full h-2">
              <div
                className="bg-violet-500 h-2 rounded-full transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {error && (
          <div className="mt-5 flex gap-2 items-center text-rose-400 text-sm">
            <AlertCircle size={18} />
            {error}
          </div>
        )}

        <div className="mt-7">
          <button
            disabled={!file || loading}
            onClick={handleUpload}
            className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:text-slate-500 px-6 py-3 rounded-xl text-sm font-semibold transition"
          >
            {loading ? (
              <>
                <Loader2 size={17} className="animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload size={17} />
                Upload Audio
              </>
            )}
          </button>
        </div>

        {uploadResult && (
          <div className="mt-6 p-5 rounded-xl border border-emerald-500/30 bg-emerald-500/5">

            <div className="flex items-center gap-2 text-emerald-400 font-semibold">
              <CheckCircle2 size={20} />
              Audio uploaded successfully!
            </div>

            <div className="mt-4 space-y-2 text-sm">
              <p>
                <span className="text-slate-400">Call ID:</span>{" "}
                <span className="text-white break-all">
                  {uploadResult.call_id}
                </span>
              </p>

              <p>
                <span className="text-slate-400">Filename:</span>{" "}
                {uploadResult.filename}
              </p>

              <p>
                <span className="text-slate-400">Format:</span>{" "}
                {uploadResult.file_format}
              </p>

              <p>
                <span className="text-slate-400">Size:</span>{" "}
                {formatSize(uploadResult.file_size)}
              </p>

              <p>
                <span className="text-slate-400">Status:</span>{" "}
                <span className="text-emerald-400">
                  {uploadResult.status}
                </span>
              </p>
            </div>
            <div className="mt-5 border-t border-slate-700 pt-5">

              <p className="text-sm text-slate-400 mb-3">
                Transcription Status:{" "}
                <span className="text-white capitalize">
                  {transcriptionStatus || "Not started"}
                </span>
              </p>

              {(!transcriptionStatus ||
                transcriptionStatus === "pending" ||
                transcriptionStatus === "failed") && (
                  <button
                    onClick={handleStartTranscription}
                    disabled={startingTranscription}
                    className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 px-5 py-3 rounded-xl text-sm font-semibold"
                  >
                    {startingTranscription ? "Starting..." : "Start Transcription"}
                  </button>
                )}

              {transcriptionStatus === "processing" && (
                <div className="flex items-center gap-2 text-blue-400 text-sm">
                  <Loader2 size={17} className="animate-spin" />
                  Transcription is processing...
                </div>
              )}

              {transcriptionStatus === "completed" && (
                <div className="space-y-3">
                  <p className="text-emerald-400 text-sm font-medium">
                    Transcription completed successfully!
                  </p>

                  <button
                    onClick={() => navigate(`/calls/${uploadResult.call_id}`)}
                    className="bg-violet-600 hover:bg-violet-500 px-5 py-3 rounded-xl text-sm font-semibold"
                  >
                    View Call Details
                  </button>
                </div>
              )}

              {transcriptionError && (
                <p className="text-rose-400 text-sm mt-3">
                  {transcriptionError}
                </p>
              )}

            </div>

          </div>
        )}

      </div>
    </div>
  );
}

export default UploadAudio;
