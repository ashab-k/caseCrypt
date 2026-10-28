"""Download and index public statutes once; cached PDFs and vectors survive restarts."""
import argparse
import json
from pathlib import Path

from services.corpus_service import ACTS, seed_corpus


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true', help='Replace the index after a successful rebuild. Stop the API first.')
    parser.add_argument('--source-dir', type=Path, help='Use locally downloaded official PDFs: ipc.pdf, crpc.pdf, constitution.pdf, evidence_act.pdf, it_act.pdf')
    parser.add_argument('--act', action='append', choices=[a.act for a in ACTS], help='Index a subset; status reports partial coverage')
    args = parser.parse_args()
    try:
        print(json.dumps(seed_corpus(force=args.force, source_dir=args.source_dir, acts=args.act), indent=2))
    except Exception as exc:
        parser.exit(1, f'Corpus seeding failed: {exc}\nThe previous index was not replaced unless publication had begun.\n')


if __name__ == '__main__':
    main()
