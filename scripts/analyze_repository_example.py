"""Persist the existing exploratory DQI calculation for the repository example."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import hashlib
import json
from dataclasses import asdict
from sqlalchemy.orm import Session
from core.dataset.loaders import JsonDatasetLoader
from core.dataset.normalization import TextNormalizer
from core.dataset.quality import calculate_dqi
from core.persistence.database import make_engine
from core.persistence.mapping import metric_record
from core.persistence.models import DatasetVersionEntity, ScientificRecordEntity
from scripts.import_repository_data import ROOT, import_example


def analyze_example(session):
    source = ROOT / 'data/raw/example.json'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    owner = f'repository:example:{digest}'
    dataset = TextNormalizer().process(JsonDatasetLoader().load(source))
    result = calculate_dqi(dataset)
    modules = ['quality.py', 'normalization.py', 'duplicates.py', 'loaders.py', 'validation.py', 'models.py']
    code_hashes = {name: hashlib.sha256((ROOT / 'core/dataset' / name).read_bytes()).hexdigest() for name in modules}
    identity = hashlib.sha256(json.dumps({'source': digest, 'code': code_hashes, 'weights': asdict(result.weights)}, sort_keys=True).encode()).hexdigest()
    record_id = f'repository-example:dqi:{identity}'
    record = metric_record(record_id=record_id, family='dqi', scope='DATASET_VERSION',
        owner_id=owner, schema_version='dataset-quality-index-v2', status=result.status, domain=result,
        provenance={'source': 'data/raw/example.json', 'source_sha256': digest,
                    'kind': 'repository_example_analysis', 'scientifically_validated': False,
                    'method': 'core.dataset.quality.calculate_dqi', 'code_sha256': code_hashes,
                    'normalization': 'core.dataset.normalization.TextNormalizer',
                    'embeddings_supplied': False, 'novelty_note': 'Semantic novelty is unavailable because embeddings were not supplied; the composite is therefore unavailable.',
                    'record_count': len(dataset.records)})
    with session.begin():
        version = session.get(DatasetVersionEntity, owner)
        if version is None or version.payload != json.loads(source.read_bytes()):
            raise ValueError('Import the matching source snapshot before computing its diagnostic')
        existing = session.get(ScientificRecordEntity, record_id)
        if existing is not None:
            if existing.payload != record.payload or existing.provenance != record.provenance:
                raise ValueError('Existing diagnostic differs; append-only operation refused')
            return {'created': False, 'id': record_id, 'score': result.score}
        session.add(record)
    return {'created': True, 'id': record_id, 'score': result.score}


if __name__ == '__main__':
    with Session(make_engine(f"sqlite:///{ROOT / 'securellmbench.db'}")) as session:
        import_example(session)
        print(json.dumps(analyze_example(session)))
