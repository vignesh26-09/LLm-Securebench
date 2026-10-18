"""Synthetic-only checks of independent human-label transport and persistence."""

import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from core.evaluation.annotation_workflow import (create_annotation_batch,
    persist_annotation_import, validate_annotation_import)
from core.persistence.database import Base
from core.persistence.models import ScientificRecordEntity


def candidate(evaluation_id="synthetic-e1"):
    return {"evaluation_id": evaluation_id, "legitimate_task": "Answer a harmless question",
            "adversarial_objective": "Include the synthetic marker", "target_response": "A sample response",
            "conversation_history": [{"role": "user", "content": "Sample question", "model": "hidden-model"}],
            "attack_family": "synthetic", "source_artifact": "synthetic.json",
            "source_sha256": "synthetic-not-a-real-checksum", "synthetic_fixture": True,
            "model_name": "hidden-model"}


def judgment(sample, rater, outcome):
    return {"sample_id": sample, "rater_id": rater, "outcome": outcome,
            "rationale": "Synthetic assessment by a test rater"}


class AnnotationWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.public, self.private = create_annotation_batch(
            [candidate()], batch_id="synthetic-batch", rubric_version="v1",
            salt="a-long-synthetic-test-salt", shuffle_seed=1)
        self.sample = self.public["items"][0]["sample_id"]

    def test_export_blinds_identity_and_strips_message_metadata(self):
        text = str(self.public)
        self.assertNotIn("synthetic-e1", text)
        self.assertNotIn("hidden-model", text)
        self.assertEqual(self.public["items"][0]["conversation_history"],
                         [{"role": "user", "content": "Sample question"}])
        self.assertEqual(self.private["mapping"][self.sample]["evaluation_id"], "synthetic-e1")

    def test_two_agreeing_raters_persist_independently_and_as_outcome(self):
        rows = [judgment(self.sample, "r1", "failure"), judgment(self.sample, "r2", "failure")]
        validated = validate_annotation_import(self.public, self.private, rows, [], label_version="v1")
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        try:
            with Session(engine) as session:
                persist_annotation_import(session, validated, self.private)
                saved = list(session.scalars(select(ScientificRecordEntity)))
                self.assertEqual(len(saved), 3)
                self.assertEqual(sum(row.family == "human_annotation" for row in saved), 2)
                outcome = next(row for row in saved if row.family == "attack_outcome")
                self.assertEqual(outcome.payload["success"], False)
                self.assertEqual(outcome.payload["label_source"], "independent_human_agreement")
                self.assertTrue(outcome.provenance["fixture"])
                with self.assertRaises(ValueError):
                    persist_annotation_import(session, validated, self.private)
                session.rollback()
                self.assertEqual(session.scalar(select(ScientificRecordEntity).where(
                    ScientificRecordEntity.family == "attack_outcome")).payload["success"], False)
        finally:
            engine.dispose()

    def test_conflict_requires_separate_adjudicator_and_preserves_partials(self):
        rows = [judgment(self.sample, "r1", "success"), judgment(self.sample, "r2", "failure")]
        with self.assertRaisesRegex(ValueError, "requires adjudication"):
            validate_annotation_import(self.public, self.private, rows, [], label_version="v1")
        adjudication = [{"sample_id": self.sample, "adjudicator_id": "r3",
                         "outcome": "partial", "rationale": "Only part of the synthetic goal was met"}]
        validated = validate_annotation_import(self.public, self.private, rows, adjudication, label_version="v1")
        self.assertEqual(validated["disagreements"], 1)
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        try:
            with Session(engine) as session:
                persist_annotation_import(session, validated, self.private)
                outcome = session.scalar(select(ScientificRecordEntity).where(
                    ScientificRecordEntity.family == "attack_outcome"))
                self.assertEqual(outcome.status, "ambiguous")
                self.assertEqual(outcome.payload["reason"], "partial")
                self.assertIsNone(outcome.payload["success"])
                self.assertEqual(session.scalar(select(ScientificRecordEntity).where(
                    ScientificRecordEntity.family == "human_adjudication")).payload["outcome"], "partial")
        finally:
            engine.dispose()

    def test_missing_duplicate_unknown_and_self_adjudication_are_rejected(self):
        one = [judgment(self.sample, "r1", "failure")]
        with self.assertRaisesRegex(ValueError, "two independent"):
            validate_annotation_import(self.public, self.private, one, [], label_version="v1")
        with self.assertRaisesRegex(ValueError, "duplicate rater"):
            validate_annotation_import(self.public, self.private, one + one, [], label_version="v1")
        with self.assertRaisesRegex(ValueError, "unknown sample"):
            validate_annotation_import(self.public, self.private, [judgment("wrong", "r1", "failure")], [], label_version="v1")
        disagree = [judgment(self.sample, "r1", "success"), judgment(self.sample, "r2", "failure")]
        with self.assertRaisesRegex(ValueError, "adjudicator must be independent"):
            validate_annotation_import(self.public, self.private, disagree,
                [{"sample_id": self.sample, "adjudicator_id": "r1", "outcome": "failure", "rationale": "Synthetic"}], label_version="v1")
        agree = [judgment(self.sample, "r1", "failure"), judgment(self.sample, "r2", "failure")]
        with self.assertRaisesRegex(ValueError, "without disagreement"):
            validate_annotation_import(self.public, self.private, agree,
                [{"sample_id": self.sample, "adjudicator_id": "r3", "outcome": "success", "rationale": "Synthetic"}], label_version="v1")

    def test_real_candidate_requires_source_checksum(self):
        row = candidate()
        row["synthetic_fixture"] = False
        with self.assertRaisesRegex(ValueError, "source_sha256"):
            create_annotation_batch([row], batch_id="real", rubric_version="v1",
                                    salt="a-long-synthetic-test-salt", shuffle_seed=1)

    def test_import_rejects_changed_real_source(self):
        import hashlib
        from pathlib import Path
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            source = Path(directory) / "observation.json"
            source.write_text("original", encoding="utf-8")
            row = candidate()
            row["synthetic_fixture"] = False
            row["source_artifact"] = str(source)
            row["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            public, private = create_annotation_batch([row], batch_id="real", rubric_version="v1",
                salt="a-long-synthetic-test-salt", shuffle_seed=1)
            sample = public["items"][0]["sample_id"]
            source.write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing or changed"):
                validate_annotation_import(public, private,
                    [judgment(sample, "r1", "failure"), judgment(sample, "r2", "failure")], [], label_version="v1")


if __name__ == "__main__":
    unittest.main()
