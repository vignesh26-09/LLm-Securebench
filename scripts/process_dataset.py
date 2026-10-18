"""Process a dataset end-to-end using the dependency-free processing pipeline."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import json
from pathlib import Path

from core.dataset.duplicates import find_dataset_duplicates
from core.dataset.ingestion import loader_for_path
from core.dataset.normalization import TextNormalizer
from core.dataset.quality import analyze_category_balance, calculate_coverage_statistics, calculate_dqi, difficulty_distribution
from core.dataset.statistics import calculate_dataset_statistics


def main() -> None:
    parser = argparse.ArgumentParser(description="Load, normalize, and summarize a SecureLLMBench dataset.")
    parser.add_argument("dataset", type=Path, help="Path to a JSON, JSONL, or CSV dataset")
    parser.add_argument("--output", type=Path, help="Optional path for the JSON summary")
    arguments = parser.parse_args()
    dataset = TextNormalizer().process(loader_for_path(arguments.dataset).load(arguments.dataset))
    basic = calculate_dataset_statistics(dataset)
    coverage = calculate_coverage_statistics(dataset)
    dqi = calculate_dqi(dataset)
    summary = {
        "dataset": {"name": dataset.metadata.name, "version": dataset.metadata.version.version},
        "statistics": {"record_count": basic.record_count, "prompt_count": basic.prompt_count, "missing_field_counts": basic.missing_field_counts},
        "duplicates": {"exact_group_count": len(find_dataset_duplicates(dataset))},
        "coverage": {"prompt_coverage": coverage.prompt_coverage, "field_coverage": coverage.field_coverage},
        "difficulty_distribution": difficulty_distribution(dataset),
        "category_balance": {"counts": analyze_category_balance(dataset).counts, "normalized_entropy": analyze_category_balance(dataset).normalized_entropy},
        "dqi": {"score": dqi.score, "components": dict(dqi.components), "note": "Exploratory and not scientifically validated."},
    }
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    if arguments.output:
        arguments.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
