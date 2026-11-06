import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Headphones,
  RefreshCw,
  Search,
  FileAudio,
} from "lucide-react";
import api from "../services/api";

function StatusBadge({ value }) {
  const styles = {
    completed: "bg-emerald-500/10 text-emerald-400",
    pending: "bg-amber-500/10 text-amber-400",
    processing: "bg-blue-500/10 text-blue-400",
    failed: "bg-rose-500/10 text-rose-400",
  };

  const label = typeof value === "string" ? value : value == null ? "unknown" : String(value);

  return (
    <span className={`rounded-full px-3 py-1 text-xs capitalize ${styles[label] || "bg-slate-700 text-slate-300"
      }`}>
      {label.replace(/_/g, " ")}
    </span>
  );
}

function CallHistory() {
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const loadCalls = useCallback(async () => {
    try {
      const response = await api.get("/api/calls");
      setCalls(response.data?.data || []);
      setError("");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to retrieve call history. Check the backend connection."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadCalls();
    }, 0);

    return () => clearTimeout(timer);
  }, [loadCalls]);

  const handleRefresh = () => {
    setLoading(true);
    loadCalls();
  };

  const filteredCalls = calls.filter((call) =>
    (call.filename || "").toLowerCase().includes(search.toLowerCase()) ||
    (call.call_id || "").toLowerCase().includes(search.toLowerCase())
  );

  const formatDate = (value) => {
    if (!value) return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
  };

  const formatSize = (bytes) => {
    if (!Number.isFinite(bytes)) return "—";
    return bytes >= 1024 * 1024
      ? `${(bytes / (1024 * 1024)).toFixed(2)} MB`
      : `${(bytes / 1024).toFixed(1)} KB`;
  };

  return (
    <div className="space-y-7">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">Call History</h1>
          <p className="text-slate-400 text-sm mt-2">
            View uploaded recordings and their processing status.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg border border-slate-700 px-4 py-2.5 text-sm hover:bg-slate-800 disabled:opacity-50"
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      <div className="bg-[#111827] border border-slate-800 rounded-2xl p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-slate-400">Total recordings</p>
            <p className="text-3xl font-bold mt-1">{calls.length}</p>
          </div>

          <div className="relative w-full sm:w-80">
            <Search
              size={17}
              className="absolute left-3 top-3 text-slate-500"
            />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search filename or call ID..."
              className="w-full bg-slate-800/60 border border-slate-700 rounded-lg py-2.5 pl-10 pr-4 text-sm outline-none focus:border-violet-500"
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300">
          {error}
        </div>
      )}

      <div className="bg-[#111827] border border-slate-800 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400">
            Loading call history...
          </div>
        ) : filteredCalls.length === 0 ? (
          <div className="p-12 text-center">
            <Headphones size={38} className="mx-auto text-slate-600 mb-4" />
            <h2 className="font-semibold">
              {calls.length ? "No matching calls" : "No call records found"}
            </h2>
            <p className="text-sm text-slate-500 mt-2">
              {calls.length
                ? "Try another filename or call ID."
                : "Upload an audio recording to get started."}
            </p>
            {!calls.length && (
              <Link
                to="/upload"
                className="inline-block mt-5 text-sm text-violet-400 hover:text-violet-300"
              >
                Upload Audio
              </Link>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-800/50 text-slate-400">
                <tr>
                  <th className="px-6 py-4">Recording</th>
                  <th className="px-6 py-4">Upload Date</th>
                  <th className="px-6 py-4">Transcription</th>
                  <th className="px-6 py-4">Evaluation</th>
                  <th className="px-6 py-4">File Size</th>
                  <th className="px-6 py-4">Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredCalls.map((call) => (
                  <tr
                    key={call.call_id}
                    className="border-t border-slate-800 hover:bg-slate-800/30"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="rounded-lg bg-violet-500/10 p-2">
                          <FileAudio size={18} className="text-violet-400" />
                        </div>
                        <div>
                          <p className="font-medium text-slate-200">
                            {call.filename || "Audio recording"}
                          </p>
                          <p className="text-xs text-slate-500 mt-1">
                            {call.file_format || "Audio"}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-400">
                      {formatDate(call.created_at)}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge value={call.transcription_status} />
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge value={call.evaluation_status} />
                    </td>
                    <td className="px-6 py-4 text-slate-400">
                      {formatSize(call.file_size)}
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        to={`/calls/${call.call_id}`}
                        className="text-violet-400 hover:text-violet-300 font-medium"
                      >
                        View details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default CallHistory;
