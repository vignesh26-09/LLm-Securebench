import { MetricReadiness } from "../components/common/MetricReadiness";
import { EntityPage } from "./EntityPage";

export function ScientificReviewsPage() {
  return <>
    <section aria-label="Scientific review readiness"><MetricReadiness implementation="Implemented review records" calibration="Not established" detail="Unavailable: scientific calibration needs documented independent review decisions tied to claims, evidence bundles and a review protocol; saved calculations do not establish it." /></section>
    <EntityPage title="Scientific reviews" resource="scientific-reviews" description="Explicit review records. Statistical outputs never automatically validate claims." />
  </>;
}
