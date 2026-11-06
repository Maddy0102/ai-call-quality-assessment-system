import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCw,
  FileAudio,
  AlertTriangle,
  Mic,
  CheckCircle2,
  Volume2,
} from "lucide-react";
import api from "../services/api";

function StatusBadge({ value }) {
  const styles = {
    completed: "bg-emerald-500/10 text-emerald-400",
    pending: "bg-amber-500/10 text-amber-400",
    processing: "bg-blue-500/10 text-blue-400",
    failed: "bg-rose-500/10 text-rose-400",
    review_required: "bg-amber-500/10 text-amber-400",
  };

  return (
    <span className={`rounded-full px-3 py-1 text-xs capitalize ${styles[value] || "bg-slate-700 text-slate-300"
      }`}>
      {(typeof value === "string" ? value : String(value || "unknown")).replace(/_/g, " ")}
    </span>
  );
}

function Metric({ label, value, suffix = "" }) {
  return (
    <div className="rounded-xl bg-slate-800/50 p-4">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="text-xl font-semibold mt-2">
        {value ?? "—"}{value !== null && value !== undefined ? suffix : ""}
      </p>
    </div>
  );
}

function SpeakerMetrics({ title, data }) {
  if (!data?.measurements) return null;

  const m = data.measurements;

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-2xl p-6">
      <div className="flex items-center gap-3 mb-5">
        <Volume2 size={20} className="text-violet-400" />
        <div>
          <h3 className="font-semibold">{title}</h3>
          <p className="text-xs text-slate-500">
            Local audio measurements · {data.sample_rate || "—"} Hz
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        <Metric label="Speech activity" value={m.speech_activity_percent} suffix="%" />
        <Metric label="Silence" value={m.silence_percent} suffix="%" />
        <Metric label="Pause count" value={m.pause_count} />
        <Metric label="Longest pause" value={m.longest_pause_seconds} suffix=" sec" />
        <Metric label="Average level" value={m.average_frame_level_dbfs} suffix=" dBFS" />
        <Metric label="Peak level" value={m.peak_level_dbfs} suffix=" dBFS" />
        <Metric label="Clipping samples" value={m.clipping_sample_count} />
      </div>

      {Array.isArray(data.limitations) && data.limitations.length > 0 && (
        <div className="mt-5 border-t border-slate-800 pt-4">
          <p className="text-xs font-medium text-slate-400 mb-2">
            Measurement limitations
          </p>
          {data.limitations.map((item, index) => (
            <p key={index} className="text-xs text-slate-500 mt-2">
              • {item}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

function CallDetails() {
  const { callId } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [speakerFilter, setSpeakerFilter] = useState("ALL");
  const [showAllSegments, setShowAllSegments] = useState(false);
  const [evaluationStatus, setEvaluationStatus] = useState("pending");
  const [startingEvaluation, setStartingEvaluation] = useState(false);
  const [evaluationError, setEvaluationError] = useState("");

  const loadReport = useCallback(async () => {
    try {
      const response = await api.get(`/api/reports/${callId}`);
      const data = response.data?.data || null;

      setReport(data);
      setEvaluationStatus(data?.evaluation_status || "pending");
      setError("");
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to load this call report."
      );
    } finally {
      setLoading(false);
    }
  }, [callId]);


  useEffect(() => {
    if (evaluationStatus !== "processing") {
      return;
    }

    const timer = setInterval(async () => {
      try {
        const response = await api.get(
          `/api/evaluation/${callId}/status`
        );

        const status = response.data?.data?.evaluation_status;

        if (!status) return;

        setEvaluationStatus(status);

        if (status === "failed") {
          setEvaluationError(
            response.data?.data?.error || "Checklist evaluation failed."
          );
        }

        if (status === "completed") {
          clearInterval(timer);
          await loadReport();
        }
      } catch (err) {
        setEvaluationError(
          err.response?.data?.detail ||
          "Unable to check evaluation status."
        );
      }
    }, 3000);

    return () => clearInterval(timer);
  }, [evaluationStatus, callId, loadReport]);

  const handleStartEvaluation = async () => {
    if (!callId || report?.transcription_status !== "completed") {
      return;
    }

    try {
      setStartingEvaluation(true);
      setEvaluationError("");

      const response = await api.post(
        `/api/evaluation/${callId}/start`
      );

      setEvaluationStatus(
        response.data?.data?.evaluation_status || "processing"
      );
    } catch (err) {
      setEvaluationError(
        err.response?.data?.detail || "Unable to start checklist evaluation."
      );
    } finally {
      setStartingEvaluation(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadReport();
    }, 0);

    return () => clearTimeout(timer);
  }, [loadReport]);

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400">
        Loading call report...
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="space-y-5">
        <Link to="/calls" className="inline-flex items-center gap-2 text-sm text-violet-400">
          <ArrowLeft size={16} /> Back to Call History
        </Link>
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-5 text-rose-300">
          {error || "Call report not found."}
          <button onClick={loadReport} className="ml-3 underline">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const segments = report.transcription_segments || [];
  const filteredSegments = segments.filter((segment) =>
    speakerFilter === "ALL" || segment.speaker === speakerFilter
  );
  const visibleSegments = showAllSegments
    ? filteredSegments
    : filteredSegments.slice(0, 30);

  const transcriptSummary = report.transcription_summary || {};
  const voice = report.voice_quality || {};
  const evaluation = report.checklist_evaluation;

  const formatTime = (seconds) => {
    if (typeof seconds !== "number") return "—";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  const formatDate = (value) => {
    if (!value) return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
  };

  return (
    <div className="space-y-7">
      <div className="flex flex-wrap justify-between items-start gap-4">
        <div>
          <Link to="/calls" className="inline-flex items-center gap-2 text-sm text-violet-400 hover:text-violet-300 mb-4">
            <ArrowLeft size={16} /> Back to Call History
          </Link>
          <h1 className="text-2xl font-bold">Call Details</h1>
          <p className="text-sm text-slate-400 mt-2 break-all">
            {report.filename || report.call_id}
          </p>
        </div>

        <button
          onClick={loadReport}
          className="flex items-center gap-2 rounded-lg border border-slate-700 px-4 py-2.5 text-sm hover:bg-slate-800"
        >
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <p className="text-xs text-slate-400">Report status</p>
          <div className="mt-3"><StatusBadge value={report.report_status} /></div>
        </div>
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <p className="text-xs text-slate-400">Transcription</p>
          <div className="mt-3"><StatusBadge value={report.transcription_status} /></div>
        </div>
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <p className="text-xs text-slate-400">Checklist evaluation</p>
          <div className="mt-3"><StatusBadge value={report.evaluation_status} /></div>
        </div>
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <p className="text-xs text-slate-400">Uploaded</p>
          <p className="font-semibold mt-3">{formatDate(report.created_at)}</p>
        </div>
      </div>

      {report.review_required && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-5">
          <div className="flex gap-3">
            <AlertTriangle size={20} className="text-amber-400 shrink-0" />
            <div>
              <h3 className="font-semibold text-amber-300">
                Human review required
              </h3>
              <p className="text-sm text-amber-200/70 mt-1">
                Some transcript or assessment information needs verification.
              </p>
              {report.review_reasons?.map((reason, index) => (
                <p key={index} className="text-sm text-amber-200/70 mt-2">
                  • {reason}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}

      <section className="bg-[#111827] border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-5">
          <FileAudio size={20} className="text-violet-400" />
          <div>
            <h2 className="text-lg font-semibold">Transcription Summary</h2>
            <p className="text-xs text-slate-500">Existing saved transcript</p>
          </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Metric label="Total segments" value={transcriptSummary.total_segments} />
          <Metric label="Reliable" value={transcriptSummary.reliable_segments} />
          <Metric label="Needs review" value={transcriptSummary.needs_review_segments} />
          <Metric label="Uncertain" value={transcriptSummary.uncertain_segments} />
        </div>
      </section>

      <section className="bg-[#111827] border border-slate-800 rounded-2xl p-6">
        <div className="flex flex-wrap justify-between items-center gap-4 mb-5">
          <div>
            <h2 className="text-lg font-semibold">Transcript</h2>
            <p className="text-xs text-slate-500 mt-1">
              {segments.length} saved segments
              {report.timestamp_status === "unavailable"
                ? " · timestamps unavailable from transcription model"
                : " · timestamps in mm:ss"}
            </p>
          </div>

          <select
            value={speakerFilter}
            onChange={(event) => setSpeakerFilter(event.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm"
          >
            <option value="ALL">All speakers</option>
            <option value="EXECUTIVE">Executive</option>
            <option value="CUSTOMER">Customer</option>
          </select>
        </div>

        {visibleSegments.length === 0 ? (
          <p className="text-sm text-slate-500 py-8 text-center">
            No transcript segments available.
          </p>
        ) : (
          <div className="space-y-3">
            {visibleSegments.map((segment, index) => (
              <div
                key={`${segment.speaker}-${segment.start}-${index}`}
                className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"
              >
                <div className="flex flex-wrap justify-between gap-2 mb-2">
                  <span className={`text-xs font-semibold ${segment.speaker === "EXECUTIVE"
                    ? "text-violet-400"
                    : "text-cyan-400"
                    }`}>
                    {segment.speaker || "UNKNOWN"}
                  </span>
                  <span className="text-xs text-slate-500">
                    {report.timestamp_status === "unavailable"
                      ? "Time unavailable"
                      : `${formatTime(segment.start)} – ${formatTime(segment.end)}`}
                  </span>
                </div>
                <p className="text-sm leading-7 text-slate-200 whitespace-pre-wrap">
                  {segment.text}
                </p>
                {segment.reliability && (
                  <div className="mt-4 rounded-lg border border-slate-700/70 bg-slate-800/40 p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs text-slate-400">
                        Transcript reliability:
                      </span>

                      <StatusBadge value={segment.reliability.status} />
                    </div>

                    {segment.reliability.reasons?.length > 0 && (
                      <div className="space-y-1">
                        {segment.reliability.reasons.map((reason, i) => (
                          <p key={i} className="text-xs text-amber-400">
                            ⚠ {reason}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {filteredSegments.length > 30 && (
          <button
            onClick={() => setShowAllSegments(!showAllSegments)}
            className="mt-5 text-sm text-violet-400 hover:text-violet-300"
          >
            {showAllSegments
              ? "Show fewer segments"
              : `Show all ${filteredSegments.length} segments`}
          </button>
        )}
      </section>

      <section>
        <div className="flex items-center gap-3 mb-4">
          <Mic size={21} className="text-violet-400" />
          <div>
            <h2 className="text-lg font-semibold">Voice Quality Measurements</h2>
            <p className="text-xs text-slate-500">
              Audio measurements, not subjective AI quality scores
            </p>
          </div>
        </div>

        {voice.executive && voice.customer ? (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
            <SpeakerMetrics title="Executive" data={voice.executive} />
            <SpeakerMetrics title="Customer" data={voice.customer} />
          </div>
        ) : (
          <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 text-sm text-slate-400">
            Voice measurements are not available.
            {report.voice_quality_error && (
              <p className="mt-2">{report.voice_quality_error}</p>
            )}
          </div>
        )}
      </section>

      <section className="bg-[#111827] border border-slate-800 rounded-2xl p-6">

        <div className="flex flex-wrap justify-between items-center gap-4 mb-5">
          <div className="flex items-center gap-3">
            <CheckCircle2 size={20} className="text-violet-400" />
            <div>
              <h2 className="text-lg font-semibold">
                Checklist Evaluation
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                AI-based verification against the predefined checklist
              </p>
            </div>
          </div>

          <StatusBadge value={evaluationStatus} />
        </div>

        {report.transcription_status !== "completed" && (
          <p className="text-sm text-amber-400">
            Complete transcription before starting checklist evaluation.
          </p>
        )}

        {report.transcription_status === "completed" &&
          ["pending", "failed"].includes(evaluationStatus) && (
            <div className="mb-5">
              <p className="text-sm text-slate-400 mb-3">
                Review the transcript before starting evaluation.
                This operation uses OpenAI API credits.
              </p>

              <button
                onClick={handleStartEvaluation}
                disabled={startingEvaluation}
                className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 px-5 py-3 rounded-xl text-sm font-semibold"
              >
                {startingEvaluation ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    Starting Evaluation...
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={16} />
                    {evaluationStatus === "failed"
                      ? "Retry Checklist Evaluation"
                      : "Start Checklist Evaluation"}
                  </>
                )}
              </button>
            </div>
          )}

        {evaluationStatus === "processing" && (
          <div className="rounded-xl bg-blue-500/10 border border-blue-500/20 p-4 mb-5">
            <div className="flex items-center gap-3 text-blue-400">
              <RefreshCw size={18} className="animate-spin" />
              <p className="text-sm font-medium">
                Checklist evaluation is processing...
              </p>
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Checking evaluation progress automatically.
            </p>
          </div>
        )}

        {evaluationError && (
          <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 mb-5">
            <p className="text-sm text-rose-400">
              {evaluationError}
            </p>
          </div>
        )}

        {evaluationStatus === "completed" && evaluation ? (
          <div className="space-y-4">

            <div className="rounded-xl bg-slate-800/50 p-4 space-y-4">
              <div>
                <p className="text-xs text-slate-400">
                  Scored Compliance
                </p>

                <p className="text-3xl font-bold text-emerald-400 mt-2">
                  {evaluation.compliance_percentage ?? "—"}%
                </p>

                <p className="text-xs text-slate-500 mt-1">
                  Calculated using questions with clear evaluation results.
                </p>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div>
                  <p className="text-xs text-slate-400">Total Questions</p>
                  <p className="text-xl font-semibold">
                    {evaluation.total_questions ?? evaluation.results?.length ?? 0}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-400">Scored</p>
                  <p className="text-xl font-semibold text-emerald-400">
                    {(evaluation.yes_count || 0) +
                      (evaluation.no_count || 0) +
                      (evaluation.partial_count || 0)}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-400">Human Review</p>
                  <p className="text-xl font-semibold text-amber-400">
                    {evaluation.results?.filter(
                      (item) => item.review_required || item.status === "NOT_CLEAR"
                    ).length || 0}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-400">Not Clear</p>
                  <p className="text-xl font-semibold text-amber-400">
                    {evaluation.not_clear_count || 0}
                  </p>
                </div>
              </div>

              <p className="text-xs text-amber-300">
                Questions marked NOT_CLEAR are excluded from the compliance calculation.
                Human review is required before treating this percentage as a complete assessment.
              </p>
            </div>

            {evaluation.results?.map((item, index) => (
              <div
                key={item.question_id || index}
                className="rounded-xl border border-slate-800 p-4"
              >
                <div className="flex flex-wrap justify-between gap-3">
                  <p className="font-medium">
                    {item.question}
                  </p>
                  <StatusBadge value={item.status} />
                </div>

                <p className="text-sm text-slate-400 mt-2">
                  {item.explanation || "No explanation available."}
                </p>

                {item.evidence?.map((evidence, i) => (
                  <p
                    key={i}
                    className="text-xs text-violet-300 mt-2"
                  >
                    {evidence.speaker}
                    {" · "}
                    {evidence.start == null
                      ? "Time unavailable"
                      : formatTime(evidence.start)}
                    {": "}
                    {evidence.text}
                  </p>
                ))}

                {item.review_required && (
                  <p className="text-xs text-amber-400 mt-3">
                    Human review: {item.review_reason || "Verification required."}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : evaluationStatus === "completed" ? (
          <p className="text-sm text-amber-400">
            Evaluation completed, but checklist results are not available in the report.
            Refresh the report to check again.
          </p>
        ) : evaluationStatus === "pending" ? (
          <p className="text-sm text-slate-500">
            No checklist results or compliance score are available yet.
          </p>
        ) : evaluationStatus === "failed" ? (
          <p className="text-sm text-rose-400">
            Evaluation failed. Check the error and retry when ready.
          </p>
        ) : null}

      </section>

      {report.limitations?.length > 0 && (
        <section className="bg-[#111827] border border-slate-800 rounded-2xl p-6">
          <h2 className="font-semibold mb-3">Report Limitations</h2>
          {report.limitations.map((item, index) => (
            <p key={index} className="text-sm text-slate-500 mt-2">
              • {item}
            </p>
          ))}
        </section>
      )}

      <div className="text-xs text-slate-600 break-all">
        Call ID: {report.call_id}
      </div>
    </div>
  );
}

export default CallDetails;
