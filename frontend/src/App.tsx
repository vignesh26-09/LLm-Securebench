import { Link, Route, Routes, useLocation } from "react-router-dom";
import { AppShell } from "./components/shell/AppShell";
import { BSDAPage, DQIPage, DRAAPage, MatchedHallucinationPage, MLPredictionPage, PRIPage, RecoveryPage, SAEAPage, StatisticalPage } from "./pages/MetricPages";
import { EntityPage } from "./pages/EntityPage";
import { StudioDashboard } from "./pages/StudioDashboard";
import { LandingPage } from "./pages/LandingPage";
import { ScientificRecordsPage } from "./pages/ScientificRecordsPage";
import { ModelsPage } from "./pages/ModelsPage";
import { ComparisonPage } from "./pages/ComparisonPage";
import { ModelTestPage as BenchmarkPage } from "./pages/ModelTestPage";
import { TestRunPage } from "./pages/TestRunPage";
import { TestHistoryPage } from "./pages/TestHistoryPage";
import { RunReportPage } from "./pages/RunReportPage";
import { WorkspaceAccess } from "./components/shell/WorkspaceAccess";
import { useEffect } from "react";

export default function App() {
  const location = useLocation();
  useEffect(() => { if (window.scrollY) window.scrollTo(0, 0); }, [location.pathname]);
  if (location.pathname === "/") return <LandingPage />;
  const publicPage = location.pathname === "/benchmark" || location.pathname === "/history" || location.pathname.startsWith("/testing/") || location.pathname.startsWith("/results/");
  const content = <AppShell><Routes>
    <Route path="/workspace" element={<StudioDashboard />} />
    <Route path="/import" element={<BenchmarkPage />} />
    <Route path="/models" element={<ModelsPage />} />
    <Route path="/benchmark" element={<BenchmarkPage />} />
    <Route path="/testing/:runId" element={<TestRunPage />} />
    <Route path="/history" element={<TestHistoryPage />} />
    <Route path="/results/:runId" element={<RunReportPage />} />
    <Route path="/datasets" element={<EntityPage title="Datasets" resource="datasets" description="Source datasets with provenance. Repository examples are engineering inputs, not validated research corpora." />} />
    <Route path="/runs" element={<EntityPage title="Benchmark runs" resource="benchmark-runs" description="Recorded executions and their original status. No runs are launched here." />} />
    <Route path="/evaluations" element={<EntityPage title="Evaluation results" resource="evaluations" description="Stored responses and execution status, with links to source-native layer evidence." />} />
    <Route path="/security" element={<EntityPage title="Security analysis · Layer 1" resource="layer1-results" description="Persisted detector evidence. Explore Layer 2 from each evaluation or the navigation." />} />
    <Route path="/metrics/bsda" element={<BSDAPage />} /><Route path="/metrics/recovery" element={<RecoveryPage />} /><Route path="/metrics/saea" element={<SAEAPage />} /><Route path="/metrics/draa" element={<DRAAPage />} /><Route path="/metrics/pri" element={<PRIPage />} /><Route path="/metrics/dqi" element={<DQIPage />} />
    <Route path="/metrics/mchl" element={<MatchedHallucinationPage />} />
    <Route path="/ml" element={<MLPredictionPage />} /><Route path="/statistics" element={<StatisticalPage />} />
    <Route path="/comparison" element={<ComparisonPage />} />
    <Route path="/dataset-versions" element={<EntityPage title="Dataset versions" resource="dataset-versions" description="Immutable source snapshots, content hashes and original payloads." />} />
    <Route path="/layer2" element={<EntityPage title="Layer 2 evidence" resource="layer2-results" description="Source-native dimensions and statuses. Scores are not probabilities; nulls remain null." />} />
    <Route path="/reviews" element={<EntityPage title="Scientific reviews" resource="scientific-reviews" description="Explicit review records. Statistical outputs never automatically validate claims." />} />
    <Route path="/records" element={<ScientificRecordsPage title="Experiment details" intro="Raw persisted scientific records with schema, status, payload, and provenance." />} />
    <Route path="*" element={<section><h1>Page not found</h1><p>This address does not match a dashboard page.</p><Link to="/">Return to overview</Link></section>} />
  </Routes></AppShell>;
  return <WorkspaceAccess allowGuest={publicPage}>{content}</WorkspaceAccess>;
}
