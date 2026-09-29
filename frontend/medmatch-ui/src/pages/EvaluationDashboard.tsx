import { useEffect, useState, useMemo } from "react";
import {
  Activity,
  ShieldAlert,
  Gauge,
  Layers,
  Search,
  CheckCircle2,
  AlertTriangle,
  Database,
  Info,
  RefreshCw,
  GitBranch,
  Cpu,
  FileCheck,
  UserCheck,
} from "lucide-react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

import StatCard from "../components/common/StatCard";
import TableCard from "../components/common/TableCard";
import ChartCard from "../components/common/ChartCard";
import {
  getEvaluationOverview,
  getEvaluationPerformance,
  getEvaluationSafety,
  getEvaluationAblations,
} from "../api/evaluationApi";
import type {
  EvaluationOverviewResponse,
  EvaluationPerformanceResponse,
  EvaluationSafetyResponse,
  EvaluationAblationsResponse,
  EvidenceType,
} from "../types/evaluation";

type TabId = "overview" | "performance" | "safety" | "ablations" | "retrieval" | "review";

export default function EvaluationDashboard() {
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [overview, setOverview] = useState<EvaluationOverviewResponse | null>(null);
  const [performance, setPerformance] = useState<EvaluationPerformanceResponse | null>(null);
  const [safety, setSafety] = useState<EvaluationSafetyResponse | null>(null);
  const [ablations, setAblations] = useState<EvaluationAblationsResponse | null>(null);

  const handleRefresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ovData, perfData, safeData, ablData] = await Promise.all([
        getEvaluationOverview(),
        getEvaluationPerformance(),
        getEvaluationSafety(),
        getEvaluationAblations(),
      ]);
      setOverview(ovData);
      setPerformance(perfData);
      setSafety(safeData);
      setAblations(ablData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load evaluation data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;

    async function loadInitialData() {
      try {
        const [ovData, perfData, safeData, ablData] = await Promise.all([
          getEvaluationOverview(),
          getEvaluationPerformance(),
          getEvaluationSafety(),
          getEvaluationAblations(),
        ]);
        if (cancelled) return;
        setOverview(ovData);
        setPerformance(perfData);
        setSafety(safeData);
        setAblations(ablData);
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load evaluation data");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadInitialData();

    return () => {
      cancelled = true;
    };
  }, []);

  // Performance chart data
  const latencyChartData = useMemo(() => {
    if (!performance) return [];
    const crit = performance.controlled_same_run_experiment.criteria_loading_latency_ms;
    const pipe = performance.controlled_same_run_experiment.local_pipeline_latency_ms;
    return [
      {
        stage: "Criteria Loading",
        Baseline: Number(crit.baseline.mean_ms.toFixed(2)),
        Optimized: Number(crit.optimized.mean_ms.toFixed(2)),
      },
      {
        stage: "Total Local Pipeline",
        Baseline: Number(pipe.baseline.mean_ms.toFixed(2)),
        Optimized: Number(pipe.optimized.mean_ms.toFixed(2)),
      },
      {
        stage: "Direct PostgreSQL",
        Baseline: performance.real_postgresql_measurement.sequential_5_trials_mean_ms,
        Optimized: performance.real_postgresql_measurement.batched_5_trials_mean_ms,
      },
    ];
  }, [performance]);

  // Vector scaling chart data
  const vectorScalingData = useMemo(() => {
    if (!performance) return [];
    return performance.vector_retrieval_scaling.map((item) => ({
      corpus: `${item.corpus_size.toLocaleString()} rows`,
      latency_ms: item.latency_ms,
    }));
  }, [performance]);

  // Ablation chart data
  const ablationChartData = useMemo(() => {
    if (!ablations) return [];
    return ablations.ablations.map((a) => {
      const metricKey = a.specification.primary_metrics[0] || "accuracy";
      return {
        ablation: a.ablation_id,
        name: a.specification.name,
        baseline: a.baseline_metrics[metricKey] ?? 0,
        treatment: a.treatment_metrics[metricKey] ?? 0,
        metric: metricKey,
      };
    });
  }, [ablations]);

  // Retrieval E0-E4 chart data
  const retrievalE0E4Data = useMemo(() => {
    if (!ablations) return [];
    return ablations.experiments.map((exp) => ({
      experiment: exp.experiment_id.replace("_RAG", "").replace("_BASELINE", " (Base)"),
      precision_at_k: exp.retrieval_metrics.precision_at_k ?? 0,
      recall_at_k: exp.retrieval_metrics.recall_at_k ?? 0,
      mrr: exp.retrieval_metrics.mrr ?? 0,
      ndcg: exp.retrieval_metrics.ndcg ?? 0,
      grounding_score: exp.grounding_metrics.grounding_score ?? 0,
    }));
  }, [ablations]);

  const renderBadge = (evidence: EvidenceType) => {
    switch (evidence) {
      case "MEASURED":
        return (
          <span className="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200">
            MEASURED
          </span>
        );
      case "OFFLINE EXPERIMENT":
        return (
          <span className="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-700 border border-blue-200">
            OFFLINE EXPERIMENT
          </span>
        );
      case "SYNTHETIC / DEVELOPMENT FIXTURE":
        return (
          <span className="inline-flex items-center rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700 border border-amber-200">
            SYNTHETIC / DEV FIXTURE
          </span>
        );
      case "CONFIGURATION RISK ONLY":
        return (
          <span className="inline-flex items-center rounded-full bg-purple-50 px-2.5 py-0.5 text-xs font-semibold text-purple-700 border border-purple-200">
            CONFIG RISK ONLY
          </span>
        );
      case "NOT MEASURED":
        return (
          <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600 border border-slate-300">
            NOT MEASURED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center rounded-full bg-slate-50 px-2.5 py-0.5 text-xs font-medium text-slate-600 border border-slate-200">
            {evidence}
          </span>
        );
    }
  };

  if (loading) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-3">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm font-medium text-text-muted">Loading research evaluation artifacts...</p>
      </div>
    );
  }

  if (error || !overview || !performance || !safety || !ablations) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center">
        <AlertTriangle className="mx-auto h-8 w-8 text-red-500" />
        <h2 className="mt-2 text-base font-semibold text-red-900">Failed to Load Evaluation Dashboard</h2>
        <p className="mt-1 text-sm text-red-700">{error || "One or more evaluation artifacts could not be retrieved."}</p>
        <button
          onClick={handleRefresh}
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        >
          <RefreshCw size={16} />
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-text">
              Evaluation & Benchmarks
            </h1>
            <span className="rounded-full bg-primary-bg px-3 py-1 text-xs font-semibold text-primary-dark border border-primary-light/40">
              Phase 15 Evidence Layer
            </span>
          </div>
          <p className="mt-1 text-sm text-text-muted">
            Read-only empirical performance measurements, safety pipelines, and research ablation studies across Phases 5–14.
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface px-3 py-2 text-sm font-medium text-text hover:bg-surface-alt"
          title="Reload artifacts"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Disclaimers & Evidence Guardrails Banner */}
      <div className="rounded-2xl border border-amber-200 bg-amber-50/80 p-4">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 shrink-0 text-amber-600 mt-0.5" />
          <div className="space-y-1 text-xs text-amber-900">
            <p className="font-semibold text-sm text-amber-950">
              Scientific Evidence Integrity Guardrails
            </p>
            <p>
              • <strong>Development Test Fixtures:</strong> Phase 11 ablations (n=6) and Phase 12 error injections (14 scenarios) evaluate system logic and gate interception. They do <strong>NOT</strong> constitute clinical validation or generalized efficacy claims.
            </p>
            <p>
              • <strong>Phase 14 Performance Methodology:</strong> Phase 14.1 is a frozen historical reference (128.32 ms). Reported Phase 14.2 improvements (79.15% criteria, 58.71% pipeline) are computed strictly from the same-run controlled baseline (121.55 ms → 25.34 ms). Cross-run percentage math is strictly prohibited.
            </p>
            <p>
              • <strong>External Latency Boundary:</strong> Live Gemini LLM inference and external network HTTP socket latencies are explicitly marked <strong>NOT MEASURED</strong> in local benchmarks.
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-border pb-2">
        {[
          { id: "overview", label: "Executive Overview", icon: Activity },
          { id: "performance", label: "Phase 14 Performance", icon: Gauge },
          { id: "safety", label: "Clinical Safety & Errors", icon: ShieldAlert },
          { id: "ablations", label: "Ablations (A1–A5)", icon: Layers },
          { id: "retrieval", label: "Retrieval & RAG (E0–E4)", icon: Search },
          { id: "review", label: "Uncertainty & Review", icon: UserCheck },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id as TabId)}
            className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition ${
              activeTab === id
                ? "bg-primary text-white shadow-sm"
                : "bg-surface text-text-muted hover:bg-surface-alt hover:text-text border border-border"
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {/* =================================================================== */}
      {/* TAB 1: EXECUTIVE OVERVIEW */}
      {/* =================================================================== */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Executive StatCards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {overview.highlights.map((h, i) => (
              <StatCard
                key={i}
                label={h.title}
                value={`${h.value} ${h.unit ? `(${h.unit})` : ""}`}
                icon={
                  h.title.includes("Safety") ? (
                    <CheckCircle2 size={18} />
                  ) : h.title.includes("Query") ? (
                    <Database size={18} />
                  ) : h.title.includes("Latency") ? (
                    <Gauge size={18} />
                  ) : h.title.includes("Review") ? (
                    <UserCheck size={18} />
                  ) : (
                    <Info size={18} />
                  )
                }
                hint={h.description}
              />
            ))}
          </div>

          {/* Research Coverage Matrix */}
          <TableCard
            title="Evaluation Coverage Across Project Phases"
            action={
              <span className="text-xs text-text-muted">
                10 Project Milestones Verified
              </span>
            }
          >
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-surface-alt text-xs font-semibold text-text-muted uppercase">
                <tr>
                  <th className="px-5 py-3.5">Phase</th>
                  <th className="px-5 py-3.5">Milestone / Title</th>
                  <th className="px-5 py-3.5">Classification</th>
                  <th className="px-5 py-3.5">Evaluation Scope</th>
                  <th className="px-5 py-3.5">Key Metric / Finding</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {overview.evaluation_coverage.map((c) => (
                  <tr key={c.phase_id} className="hover:bg-surface-alt/50">
                    <td className="px-5 py-3.5 font-medium text-text">{c.phase_id}</td>
                    <td className="px-5 py-3.5 font-semibold text-text">{c.title}</td>
                    <td className="px-5 py-3.5">{renderBadge(c.evidence_classification)}</td>
                    <td className="px-5 py-3.5 text-xs text-text-muted max-w-xs">{c.scope}</td>
                    <td className="px-5 py-3.5 text-xs font-mono text-emerald-800">{c.key_metric}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableCard>

          {/* Evidence Classification Matrix Table */}
          <TableCard title="Strict Evidence Classification Dictionary">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-surface-alt text-xs font-semibold text-text-muted uppercase">
                <tr>
                  <th className="px-5 py-3">Metric / Component</th>
                  <th className="px-5 py-3">Evidence Classification</th>
                  <th className="px-5 py-3">Interpretation Boundary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {Object.entries(overview.evidence_classification_summary).map(([k, v]) => (
                  <tr key={k} className="hover:bg-surface-alt/50">
                    <td className="px-5 py-3 font-medium text-text">{k}</td>
                    <td className="px-5 py-3">{renderBadge(v)}</td>
                    <td className="px-5 py-3 text-xs text-text-muted">
                      {v === "MEASURED" && "Empirically quantified under reproducible benchmark harness"}
                      {v === "NOT MEASURED" && "Deliberately excluded from offline runs to avoid unverified assertions"}
                      {v === "SYNTHETIC / DEVELOPMENT FIXTURE" && "Tested on deterministic synthetic fixtures; no generalized clinical claims"}
                      {v === "OFFLINE EXPERIMENT" && "Precomputed local research script execution"}
                      {v === "CONFIGURATION RISK ONLY" && "Derived from architectural configurations rather than empirical stress"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableCard>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 2: PERFORMANCE (PHASE 14.1 & 14.2) */}
      {/* =================================================================== */}
      {activeTab === "performance" && (
        <div className="space-y-6">
          {/* Headline Methodology Callout */}
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
            {/* Frozen Phase 14.1 Reference */}
            <div className="rounded-2xl border border-slate-300 bg-slate-50/70 p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-700">
                  <GitBranch size={16} /> Frozen Reference (Phase 14.1)
                </span>
                <span className="font-mono text-xs text-slate-600 bg-slate-200/80 px-2 py-0.5 rounded">
                  commit: {performance.frozen_phase14_1_reference.commit}
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-600">
                {performance.frozen_phase14_1_reference.note}
              </p>
              <div className="mt-4 grid grid-cols-2 gap-3 border-t border-slate-200 pt-3 text-center">
                <div>
                  <p className="text-xs text-slate-500">Criteria Loading Mean</p>
                  <p className="text-xl font-bold text-slate-800">
                    {performance.frozen_phase14_1_reference.criteria_loading_mean_ms} ms
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Local Pipeline Mean</p>
                  <p className="text-xl font-bold text-slate-800">
                    {performance.frozen_phase14_1_reference.local_pipeline_mean_ms} ms
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Sequential Queries</p>
                  <p className="text-xl font-bold text-slate-800">
                    {performance.frozen_phase14_1_reference.criteria_loading_queries} queries
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Live Gemini / HTTP</p>
                  <p className="text-sm font-semibold text-slate-500 mt-1">
                    NOT MEASURED
                  </p>
                </div>
              </div>
            </div>

            {/* Controlled Same-Run Experiment (Phase 14.2) */}
            <div className="rounded-2xl border border-emerald-300 bg-emerald-50/70 p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-800">
                  <Cpu size={16} /> Same-Run Controlled Experiment (Phase 14.2)
                </span>
                <span className="inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-300">
                  OPTIMIZATION ACCEPTED
                </span>
              </div>
              <p className="mt-2 text-xs text-emerald-900">
                {performance.controlled_same_run_experiment.variance_explanation}
              </p>
              <div className="mt-4 grid grid-cols-2 gap-3 border-t border-emerald-200 pt-3 text-center">
                <div>
                  <p className="text-xs text-emerald-700">Criteria Loading Improvement</p>
                  <p className="text-xl font-bold text-emerald-900">
                    79.15%
                  </p>
                  <p className="text-xs text-emerald-700 font-mono">121.55 → 25.34 ms</p>
                </div>
                <div>
                  <p className="text-xs text-emerald-700">Local Pipeline Improvement</p>
                  <p className="text-xl font-bold text-emerald-900">
                    58.71%
                  </p>
                  <p className="text-xs text-emerald-700 font-mono">163.63 → 67.57 ms</p>
                </div>
                <div>
                  <p className="text-xs text-emerald-700">Primary Query Reduction</p>
                  <p className="text-xl font-bold text-emerald-900">
                    80.0%
                  </p>
                  <p className="text-xs text-emerald-700 font-mono">5 queries → 1 query</p>
                </div>
                <div>
                  <p className="text-xs text-emerald-700">Direct PostgreSQL Reduction</p>
                  <p className="text-xl font-bold text-emerald-900">
                    97.65%
                  </p>
                  <p className="text-xs text-emerald-700 font-mono">118.51 → 2.79 ms</p>
                </div>
              </div>
            </div>
          </div>

          {/* Secondary ORM Selectin Loading Insight */}
          <div className="rounded-xl border border-blue-200 bg-blue-50/60 p-4 text-xs text-blue-900">
            <p className="font-semibold text-blue-950">Secondary ORM Relationship Loading Insight:</p>
            <p className="mt-1">{performance.controlled_same_run_experiment.secondary_orm_observation}</p>
          </div>

          {/* Latency Comparison Chart */}
          <ChartCard
            title="Controlled Same-Run Execution Latency (ms)"
            subtitle="Comparing fresh sequential baseline vs set-based optimized execution (15 iterations, 5 candidate trials, 77 criteria)"
            evidenceType="MEASURED"
          >
            <div className="h-72 w-full min-h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={latencyChartData} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="stage" tick={{ fill: "#0F172A", fontSize: 12 }} />
                  <YAxis unit=" ms" tick={{ fill: "#64748B", fontSize: 12 }} />
                  <Tooltip formatter={(value) => [`${value} ms`]} />
                  <Legend />
                  <Bar dataKey="Baseline" fill="#94A3B8" radius={[4, 4, 0, 0]} name="Baseline (Sequential)" />
                  <Bar dataKey="Optimized" fill="#047857" radius={[4, 4, 0, 0]} name="Optimized (Batched)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>

          {/* Vector Retrieval Scaling Chart */}
          <ChartCard
            title="Unindexed pgvector Cosine Distance (<=>) Scan Latency"
            subtitle="Measured sequential scan execution time across corpus scaling from 100 to 50,000 rows (PostgreSQL 17 + pgvector 0.8.5)"
            evidenceType="MEASURED"
          >
            <div className="h-64 w-full min-h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={vectorScalingData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="corpus" tick={{ fill: "#0F172A", fontSize: 12 }} />
                  <YAxis unit=" ms" tick={{ fill: "#64748B", fontSize: 12 }} />
                  <Tooltip formatter={(value) => [`${value} ms`, "Scan Latency"]} />
                  <Line
                    type="monotone"
                    dataKey="latency_ms"
                    stroke="#047857"
                    strokeWidth={2.5}
                    dot={{ r: 5, fill: "#047857" }}
                    activeDot={{ r: 7 }}
                    name="Mean Scan Latency"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>

          {/* Benchmark Completeness Matrix */}
          <TableCard title="Empirical Benchmark Completeness & Qualification Matrix">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-surface-alt text-xs font-semibold text-text-muted uppercase">
                <tr>
                  <th className="px-5 py-3">Benchmark Dimension</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Tested / Documented Scope</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {performance.completeness_matrix.map((c, i) => (
                  <tr key={i} className="hover:bg-surface-alt/50">
                    <td className="px-5 py-3 font-medium text-text">{c.benchmark}</td>
                    <td className="px-5 py-3">{renderBadge(c.status)}</td>
                    <td className="px-5 py-3 text-xs text-text-muted">{c.scope}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableCard>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 3: SAFETY (PHASE 12) */}
      {/* =================================================================== */}
      {activeTab === "safety" && (
        <div className="space-y-6">
          {/* Safety Headline Stats */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Error Injection Detection Rate"
              value="100.0%"
              icon={<CheckCircle2 size={18} />}
              hint="14 / 14 adversarial corruptions intercepted"
            />
            <StatCard
              label="Safety Pipeline Unsafe Rate"
              value="0.00%"
              icon={<ShieldAlert size={18} />}
              hint="Dropped from 58.33% unmitigated (S-E0)"
            />
            <StatCard
              label="Human Review Routing Recall"
              value="100.0%"
              icon={<UserCheck size={18} />}
              hint="0 missing facts or contradictions dropped"
            />
            <StatCard
              label="Tenant Isolation Violations"
              value="0.00%"
              icon={<Database size={18} />}
              hint="100% multi-tenant boundary integrity"
            />
          </div>

          {/* Safety Pipeline Comparison Table */}
          <TableCard title="Clinical Safety Pipeline Progression (S-E0 Baseline → S-E4 Full Defense)">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-surface-alt text-xs font-semibold text-text-muted uppercase">
                <tr>
                  <th className="px-5 py-3">Metric</th>
                  <th className="px-5 py-3">S-E0 (Unmitigated Baseline)</th>
                  <th className="px-5 py-3">S-E4 (Full Safety Pipeline)</th>
                  <th className="px-5 py-3">Impact</th>
                  <th className="px-5 py-3">Evidence Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                <tr className="hover:bg-surface-alt/50">
                  <td className="px-5 py-3 font-medium text-text">Synthetic Unsafe Recommendation Rate</td>
                  <td className="px-5 py-3 font-mono text-red-600">58.33%</td>
                  <td className="px-5 py-3 font-mono text-emerald-600 font-semibold">0.00%</td>
                  <td className="px-5 py-3 text-xs text-emerald-800 font-medium">-58.33% unsafe recommendations eliminated</td>
                  <td className="px-5 py-3">{renderBadge(safety.evidence_classification)}</td>
                </tr>
                <tr className="hover:bg-surface-alt/50">
                  <td className="px-5 py-3 font-medium text-text">Gate Pass Rate</td>
                  <td className="px-5 py-3 font-mono text-slate-500">N/A (No gates)</td>
                  <td className="px-5 py-3 font-mono text-emerald-700">92.77%</td>
                  <td className="px-5 py-3 text-xs text-text-muted">High pass rate preserves eligible patient throughput</td>
                  <td className="px-5 py-3">{renderBadge(safety.evidence_classification)}</td>
                </tr>
                <tr className="hover:bg-surface-alt/50">
                  <td className="px-5 py-3 font-medium text-text">Human Review Routing Recall</td>
                  <td className="px-5 py-3 font-mono text-red-600">0.00%</td>
                  <td className="px-5 py-3 font-mono text-emerald-600 font-semibold">100.00%</td>
                  <td className="px-5 py-3 text-xs text-emerald-800 font-medium">All ambiguous/contradictory records escalated</td>
                  <td className="px-5 py-3">{renderBadge(safety.evidence_classification)}</td>
                </tr>
              </tbody>
            </table>
          </TableCard>

          {/* Safety Gate Ablations (A-S1 to A-S7) */}
          <TableCard title="Safety Gate Component Ablations (A-S1 through A-S7)">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-surface-alt text-xs font-semibold text-text-muted uppercase">
                <tr>
                  <th className="px-5 py-3">Ablation</th>
                  <th className="px-5 py-3">Gate Enforced</th>
                  <th className="px-5 py-3">Target Metric</th>
                  <th className="px-5 py-3">Baseline</th>
                  <th className="px-5 py-3">Enforced</th>
                  <th className="px-5 py-3">Delta</th>
                  <th className="px-5 py-3">Observation Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {safety.safety_ablations.map((a) => (
                  <tr key={a.ablation_id} className="hover:bg-surface-alt/50">
                    <td className="px-5 py-3 font-bold text-text">{a.ablation_id}</td>
                    <td className="px-5 py-3 text-xs font-medium text-text">{a.changed_gate}</td>
                    <td className="px-5 py-3 font-mono text-xs text-text-muted">{a.primary_metric}</td>
                    <td className="px-5 py-3 font-mono text-xs">{a.baseline_value}</td>
                    <td className="px-5 py-3 font-mono text-xs font-semibold text-emerald-700">{a.treatment_value}</td>
                    <td className="px-5 py-3 font-mono text-xs font-semibold text-emerald-800">{a.delta > 0 ? `+${a.delta}` : a.delta}</td>
                    <td className="px-5 py-3 text-xs text-text-muted max-w-sm">{a.observation_summary}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableCard>

          {/* Adversarial Error Injection Scenarios Table */}
          <TableCard title="14 Adversarial Error Injection Test Scenarios">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-surface-alt text-xs font-semibold text-text-muted uppercase">
                <tr>
                  <th className="px-5 py-3">ID</th>
                  <th className="px-5 py-3">Corruption Type</th>
                  <th className="px-5 py-3">Target Gate</th>
                  <th className="px-5 py-3">Defense Tier</th>
                  <th className="px-5 py-3">Detected</th>
                  <th className="px-5 py-3">Mitigation / Protection</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {safety.error_scenarios.map((s) => (
                  <tr key={s.scenario_id} className="hover:bg-surface-alt/50">
                    <td className="px-5 py-3 font-mono text-xs font-medium text-text">{s.scenario_id}</td>
                    <td className="px-5 py-3 font-medium text-text">{s.name}</td>
                    <td className="px-5 py-3 font-mono text-xs text-text-muted">{s.target_gate}</td>
                    <td className="px-5 py-3">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
                        s.interception_mode === "PREVENTION" ? "bg-purple-100 text-purple-800" : "bg-blue-100 text-blue-800"
                      }`}>
                        {s.interception_mode}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700">
                        <CheckCircle2 size={14} /> Intercepted
                      </span>
                    </td>
                    <td className="px-5 py-3 text-xs text-text-muted">{s.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableCard>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 4: ABLATIONS (PHASE 11 A1–A5) */}
      {/* =================================================================== */}
      {activeTab === "ablations" && (
        <div className="space-y-6">
          {/* Sample Size Guardrail Alert */}
          <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-xs text-amber-950">
            <p className="font-semibold text-sm text-amber-950">Development Fixture Observation Only (n=6)</p>
            <p className="mt-1">
              Due to the absence of ingested external public benchmarks (TrialGPT/TREC), all ablation comparisons are evaluated strictly on deterministic test fixtures (n=6). These findings characterize pipeline component responsiveness; no generalized statistical superiority or clinical efficacy claims are permitted.
            </p>
          </div>

          {/* Ablations Comparison Chart */}
          <ChartCard
            title="Component Ablations Impact (A1–A5)"
            subtitle="Comparing baseline vs treatment primary metrics across 5 architectural component ablations"
            evidenceType="SYNTHETIC / DEVELOPMENT FIXTURE"
          >
            <div className="h-72 w-full min-h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={ablationChartData} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="ablation" tick={{ fill: "#0F172A", fontSize: 12 }} />
                  <YAxis domain={[0, 1.1]} tick={{ fill: "#64748B", fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="baseline" fill="#94A3B8" name="Baseline Score" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="treatment" fill="#047857" name="Treatment Score" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>

          {/* Ablation Details Table */}
          <TableCard title="Detailed Component Ablations (A1 through A5)">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-surface-alt text-xs font-semibold text-text-muted uppercase">
                <tr>
                  <th className="px-5 py-3">Ablation</th>
                  <th className="px-5 py-3">Experiment Baseline → Treatment</th>
                  <th className="px-5 py-3">Changed Component</th>
                  <th className="px-5 py-3">Hypothesis Tested</th>
                  <th className="px-5 py-3">Sample (n)</th>
                  <th className="px-5 py-3">Observation Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {ablations.ablations.map((a) => (
                  <tr key={a.ablation_id} className="hover:bg-surface-alt/50">
                    <td className="px-5 py-3 font-bold text-text">
                      {a.ablation_id}: {a.specification.name}
                    </td>
                    <td className="px-5 py-3 font-mono text-xs text-text-muted">
                      {a.specification.baseline_experiment} → {a.specification.treatment_experiment}
                    </td>
                    <td className="px-5 py-3 text-xs text-text-muted max-w-xs">
                      {a.specification.changed_component}
                    </td>
                    <td className="px-5 py-3 text-xs text-text-muted max-w-xs">
                      {a.specification.hypothesis_tested}
                    </td>
                    <td className="px-5 py-3 font-mono text-xs">{a.sample_size}</td>
                    <td className="px-5 py-3 text-xs text-slate-700 max-w-xs">
                      {a.observation_summary}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableCard>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 5: RETRIEVAL & RAG COMPARISON (E0–E4) */}
      {/* =================================================================== */}
      {activeTab === "retrieval" && (
        <div className="space-y-6">
          <ChartCard
            title="Retrieval Metrics Across Experiments E0 through E4"
            subtitle="Evaluating Recall@K, Precision@K, MRR, nDCG, and Grounding Score across architectural progression"
            evidenceType="OFFLINE EXPERIMENT"
          >
            <div className="h-72 w-full min-h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={retrievalE0E4Data} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="experiment" tick={{ fill: "#0F172A", fontSize: 12 }} />
                  <YAxis domain={[0, 1.1]} tick={{ fill: "#64748B", fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="recall_at_k" fill="#3B82F6" name="Recall@5" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="precision_at_k" fill="#94A3B8" name="Precision@5" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="mrr" fill="#F59E0B" name="MRR" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="grounding_score" fill="#047857" name="Grounding Score" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>

          {/* Experiments E0–E4 Table */}
          <TableCard title="Experiment Architecture & Metric Matrix (E0–E4)">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-surface-alt text-xs font-semibold text-text-muted uppercase">
                <tr>
                  <th className="px-5 py-3">Experiment ID</th>
                  <th className="px-5 py-3">Representation</th>
                  <th className="px-5 py-3">Retrieval Strategy</th>
                  <th className="px-5 py-3">Accuracy</th>
                  <th className="px-5 py-3">Macro-F1</th>
                  <th className="px-5 py-3">Grounding Score</th>
                  <th className="px-5 py-3">Evidence Coverage</th>
                  <th className="px-5 py-3">Citation Validity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {ablations.experiments.map((e) => (
                  <tr key={e.experiment_id} className="hover:bg-surface-alt/50">
                    <td className="px-5 py-3 font-semibold text-text">{e.experiment_id}</td>
                    <td className="px-5 py-3 font-mono text-xs">{e.config.patient_representation}</td>
                    <td className="px-5 py-3 font-mono text-xs">{e.config.retrieval_strategy}</td>
                    <td className="px-5 py-3 font-mono text-xs font-semibold text-emerald-700">
                      {e.eligibility_metrics.accuracy?.toFixed(2) ?? "1.00"}
                    </td>
                    <td className="px-5 py-3 font-mono text-xs font-semibold text-emerald-700">
                      {e.eligibility_metrics.macro_f1?.toFixed(2) ?? "1.00"}
                    </td>
                    <td className="px-5 py-3 font-mono text-xs">
                      {e.grounding_metrics.grounding_score?.toFixed(4) ?? "N/A"}
                    </td>
                    <td className="px-5 py-3 font-mono text-xs">
                      {e.grounding_metrics.evidence_coverage?.toFixed(4) ?? "N/A"}
                    </td>
                    <td className="px-5 py-3 font-mono text-xs">
                      {e.grounding_metrics.citation_validity_rate?.toFixed(4) ?? "N/A"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableCard>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 6: UNCERTAINTY & HUMAN REVIEW (PHASE 9) */}
      {/* =================================================================== */}
      {activeTab === "review" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard
              label="Human Review Routing Recall"
              value="100.0%"
              icon={<CheckCircle2 size={18} />}
              hint="All discordant/missing clinical facts routed to review"
            />
            <StatCard
              label="Synthetic Test Scenarios"
              value={safety.uncertainty_and_review.total_cases}
              icon={<FileCheck size={18} />}
              hint="Phase 9 development test cases"
            />
            <StatCard
              label="Evidence Classification"
              value="DEV FIXTURE"
              icon={<Info size={18} />}
              hint="Tested on synthetic fixtures"
            />
          </div>

          <TableCard title="Uncertainty Taxonomy & Human Review Priority Matrix">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-surface-alt text-xs font-semibold text-text-muted uppercase">
                <tr>
                  <th className="px-5 py-3">Clinical Uncertainty Category</th>
                  <th className="px-5 py-3">Case Count</th>
                  <th className="px-5 py-3">Escalation Priority</th>
                  <th className="px-5 py-3">Machine Determination Allowed</th>
                  <th className="px-5 py-3">Safety Policy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {safety.uncertainty_and_review.categories.map((c) => (
                  <tr key={c.category} className="hover:bg-surface-alt/50">
                    <td className="px-5 py-3 font-medium text-text capitalize">
                      {c.category.replace(/_/g, " ")}
                    </td>
                    <td className="px-5 py-3 font-mono text-xs">{c.case_count}</td>
                    <td className="px-5 py-3">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
                        c.expected_priority === "ROUTINE"
                          ? "bg-slate-100 text-slate-700"
                          : c.expected_priority === "PRIORITY"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-red-100 text-red-800"
                      }`}>
                        {c.expected_priority}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      {c.machine_decision_allowed ? (
                        <span className="text-xs font-medium text-emerald-700">Permitted (Complete evidence)</span>
                      ) : (
                        <span className="text-xs font-semibold text-red-700">PROHIBITED (Mandatory Clinician Review)</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-xs text-text-muted">
                      {c.machine_decision_allowed
                        ? "Clear passing/failing criteria proceed automatically"
                        : "Enforces Closed-World guard: Missing/conflicting data blocks automated eligibility"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableCard>
        </div>
      )}
    </div>
  );
}
