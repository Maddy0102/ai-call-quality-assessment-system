import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Phone,
  CheckCircle2,
  AlertCircle,
  Mic,
  ArrowUpRight,
  Clock,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import api from "../services/api";

function formatDate(value) {
  if (!value) return "Date unavailable";

  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Date unavailable"
    : date.toLocaleString();
}

function formatFileSize(bytes) {
  if (!Number.isFinite(bytes)) return "—";
  return bytes >= 1024 * 1024
    ? `${(bytes / (1024 * 1024)).toFixed(2)} MB`
    : `${(bytes / 1024).toFixed(1)} KB`;
}

function StatusBadge({ value }) {
  const styles = {
    completed: "bg-emerald-500/10 text-emerald-400",
    pending: "bg-amber-500/10 text-amber-400",
    processing: "bg-blue-500/10 text-blue-400",
    failed: "bg-rose-500/10 text-rose-400",
  };

  const label = typeof value === "string" ? value : value == null ? "unknown" : String(value);

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs capitalize ${styles[label] || "bg-slate-700 text-slate-300"
        }`}
    >
      {label.replace(/_/g, " ")}
    </span>
  );
}

function Dashboard() {
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadCalls = useCallback(async () => {
    try {
      const response = await api.get("/api/calls");
      setCalls(response.data?.data || []);
      setError("");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load call records. Check that the backend is running."
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

  const stats = useMemo(() => {
    const evaluated = calls.filter(
      (call) => call.evaluation_status === "completed"
    );

    const complianceValues = evaluated
      .map((call) => call.evaluation_summary?.compliance_percentage)
      .filter((value) => typeof value === "number");

    const averageCompliance = complianceValues.length
      ? `${(
        complianceValues.reduce((sum, value) => sum + value, 0) /
        complianceValues.length
      ).toFixed(1)}%`
      : "—";

    const failedChecks = evaluated.reduce(
      (sum, call) => sum + (call.evaluation_summary?.no_count || 0),
      0
    );
    const humanReviewCount = evaluated.reduce(
      (sum, call) =>
        sum + (call.evaluation_summary?.human_review_count || 0),
      0
    );

    return [
      {
        title: "Total Calls",
        value: calls.length,
        description: "Uploaded recordings",
        icon: Phone,
        color: "text-blue-400",
        bg: "bg-blue-500/10",
      },
      {
        title: "Average Compliance",
        value: averageCompliance,
        description: "Average scored compliance across completed evaluations",
        icon: CheckCircle2,
        color: "text-emerald-400",
        bg: "bg-emerald-500/10",
      },
      {
        title: "Failed Checks",
        value: failedChecks,
        description: "NO results in completed evaluations",
        icon: AlertCircle,
        color: "text-rose-400",
        bg: "bg-rose-500/10",
      },
      {
        title: "Human Review",
        value: humanReviewCount,
        description: "Checklist questions requiring review",
        icon: AlertCircle,
        color: "text-amber-400",
        bg: "bg-amber-500/10",
      },
      {
        title: "Voice Quality",
        value: "Not measured",
        description: "No validated voice score available",
        icon: Mic,
        color: "text-violet-400",
        bg: "bg-violet-500/10",
      },
    ];
  }, [calls]);

  const assessmentCounts = useMemo(() => {
    return calls.reduce(
      (counts, call) => {
        if (call.evaluation_status !== "completed") return counts;

        const summary = call.evaluation_summary || {};
        counts.YES += summary.yes_count || 0;
        counts.NO += summary.no_count || 0;
        counts.PARTIAL += summary.partial_count || 0;
        counts.NOT_CLEAR += summary.not_clear_count || 0;

        return counts;
      },
      { YES: 0, NO: 0, PARTIAL: 0, NOT_CLEAR: 0 }
    );
  }, [calls]);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">Dashboard Overview</h1>
          <p className="text-sm text-slate-400 mt-2">
            Monitor call performance and quality assessments.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-400">
            Development Environment
          </span>
          <button
            onClick={loadCalls}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800 disabled:opacity-50"
          >
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300">
          {error}
          <button onClick={loadCalls} className="ml-3 underline">
            Retry
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">
        {stats.map((item) => {
          const Icon = item.icon;

          return (
            <div
              key={item.title}
              className="bg-[#111827] border border-slate-800 rounded-2xl p-5"
            >
              <div className="flex justify-between items-center">
                <div className={`p-3 rounded-xl ${item.bg}`}>
                  <Icon size={22} className={item.color} />
                </div>
                <ArrowUpRight size={18} className="text-slate-600" />
              </div>

              <p className="text-sm text-slate-400 mt-5">{item.title}</p>
              <h2 className="text-3xl font-bold mt-2">{item.value}</h2>
              <p className="text-xs text-slate-500 mt-2">
                {item.description}
              </p>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        <div className="xl:col-span-2 bg-[#111827] border border-slate-800 rounded-2xl p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="font-semibold text-lg">Call Analysis</h2>
              <p className="text-sm text-slate-500 mt-1">
                Your call assessment activity
              </p>
            </div>
            <Clock size={20} className="text-slate-500" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl bg-slate-800/50 p-5">
              <p className="text-sm text-slate-400">Transcribed Calls</p>
              <p className="text-3xl font-bold mt-2">
                {calls.filter((c) => c.transcription_status === "completed").length}
              </p>
            </div>
            <div className="rounded-xl bg-slate-800/50 p-5">
              <p className="text-sm text-slate-400">Evaluated Calls</p>
              <p className="text-3xl font-bold mt-2">
                {calls.filter((c) => c.evaluation_status === "completed").length}
              </p>
            </div>
          </div>

          <div className="mt-5 text-sm text-slate-500">
            {loading
              ? "Loading call activity..."
              : `${calls.length} call record(s) retrieved from the backend.`}
          </div>
        </div>

        <div className="bg-[#111827] border border-slate-800 rounded-2xl p-6">
          <h2 className="font-semibold text-lg">Assessment Summary</h2>
          <p className="text-sm text-slate-500 mt-1">
            Results from completed evaluations only
          </p>

          <div className="space-y-5 mt-8">
            {[
              ["YES", assessmentCounts.YES, "text-emerald-400"],
              ["NO", assessmentCounts.NO, "text-rose-400"],
              ["PARTIAL", assessmentCounts.PARTIAL, "text-amber-400"],
              ["NOT CLEAR", assessmentCounts.NOT_CLEAR, "text-slate-400"],
            ].map(([label, value, color]) => (
              <div key={label} className="flex justify-between">
                <span className={color}>{label}</span>
                <span className="font-semibold">{value}</span>
              </div>
            ))}
          </div>

          <div className="border-t border-slate-800 mt-7 pt-5">
            <p className="text-xs text-slate-500">
              {calls.some((c) => c.evaluation_status === "completed")
                ? "Counts include completed checklist evaluations."
                : "No completed checklist evaluations yet."}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-[#111827] border border-slate-800 rounded-2xl p-6">
        <div className="flex justify-between items-center gap-4">
          <div>
            <h2 className="font-semibold text-lg">Recent Calls</h2>
            <p className="text-sm text-slate-500 mt-1">
              Latest uploaded audio recordings
            </p>
          </div>
          <Link
            to="/calls"
            className="flex items-center gap-2 text-sm text-violet-400 hover:text-violet-300"
          >
            View all <ArrowRight size={17} />
          </Link>
        </div>

        {loading ? (
          <p className="py-10 text-center text-slate-400">
            Loading call records...
          </p>
        ) : calls.length === 0 ? (
          <div className="py-12 text-center">
            <Phone size={32} className="mx-auto text-slate-600 mb-3" />
            <p className="text-slate-400">No calls uploaded yet.</p>
            <Link to="/upload" className="text-sm text-violet-400 mt-3 inline-block">
              Upload your first recording
            </Link>
          </div>
        ) : (
          <div className="mt-6 overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-slate-500 border-b border-slate-800">
                <tr>
                  <th className="py-3 pr-4">Recording</th>
                  <th className="py-3 pr-4">Uploaded</th>
                  <th className="py-3 pr-4">Transcription</th>
                  <th className="py-3 pr-4">Evaluation</th>
                  <th className="py-3">Size</th>
                </tr>
              </thead>
              <tbody>
                {calls.slice(0, 5).map((call) => (
                  <tr key={call.call_id} className="border-b border-slate-800/70">
                    <td className="py-4 pr-4">
                      <Link
                        to={`/calls/${call.call_id}`}
                        className="font-medium text-slate-200 hover:text-violet-400"
                      >
                        {call.filename || "Audio recording"}
                      </Link>
                    </td>
                    <td className="py-4 pr-4 text-slate-400">
                      {formatDate(call.created_at)}
                    </td>
                    <td className="py-4 pr-4">
                      <StatusBadge value={call.transcription_status} />
                    </td>
                    <td className="py-4 pr-4">
                      <StatusBadge value={call.evaluation_status} />
                    </td>
                    <td className="py-4 text-slate-400">
                      {formatFileSize(call.file_size)}
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

export default Dashboard;
