"""Versioned public statute corpus. Seed CLI owns writes; requests only read."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from config import settings

COLLECTION = 'indian_legal_corpus'
NOTICE = ('Research aid from a static statute snapshot; verify the cited source and applicability. '
          'IPC, CrPC and the Indian Evidence Act are historical texts; the 2023 replacement criminal '
          'laws took effect on 1 July 2024. This corpus does not include those replacement laws or case law.')


@dataclass(frozen=True)
class ActSpec:
    act: str
    title: str
    url: str
    historical: bool = False
    minimum_sections: int = 50
    maximum_section: int = 999


ACTS = [
    ActSpec('IPC', 'Indian Penal Code, 1860', 'https://indiacode.gov.in/server/api/core/bitstreams/337c7a03-60c6-4953-8dd6-90e65c343629/content', True, 400, 511),
    ActSpec('CrPC', 'Code of Criminal Procedure, 1973', 'https://aphc.gov.in/docs/6_20241130054414.pdf', True, 400, 484),
    ActSpec('Constitution', 'Constitution of India', 'https://www.legislative.gov.in/static/uploads/2025/07/c9fe9c9b6840524844316f74bb1c556c.pdf', False, 300, 395),
    ActSpec('Evidence Act', 'Indian Evidence Act, 1872', 'https://indiacode.gov.in/server/api/core/bitstreams/4a3677bf-e488-4689-bf30-6ae29255a3ba/content', True, 140, 167),
    ActSpec('IT Act', 'Information Technology Act, 2000', 'https://indiacode.gov.in/server/api/core/bitstreams/770a7d02-48f2-4274-bab9-10d0f48ee264/content', False, 70, 94),
]


class CorpusUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_client():
    import chromadb
    from chromadb.config import Settings
    return chromadb.PersistentClient(path=str(settings.chroma_dir), settings=Settings(anonymized_telemetry=False))


@lru_cache(maxsize=1)
def get_encoder():
    from sentence_transformers import SentenceTransformer
    # Queries never trigger network downloads. The seed command downloads once.
    local = settings.corpus_dir / 'models' / 'local'
    if not local.is_dir():
        raise CorpusUnavailable('Local embedding model is missing. Run python seed.py --force to rebuild it.')
    return SentenceTransformer(str(local), device='cpu', local_files_only=True)


def encode(texts: list[str]):
    return get_encoder().encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


def get_collection():
    try:
        collection = get_client().get_collection(COLLECTION, embedding_function=None)
        if not collection.count() or not (collection.metadata or {}).get('ready'):
            raise CorpusUnavailable('Corpus is not seeded. Run python seed.py in the backend directory.')
        if (collection.metadata or {}).get('embedding_model') != settings.embedding_model:
            raise CorpusUnavailable('Corpus embedding model changed. Rebuild it with python seed.py --force.')
        return collection
    except CorpusUnavailable:
        raise
    except Exception as exc:
        raise CorpusUnavailable('Corpus is unavailable. Install backend requirements and run python seed.py.') from exc


def corpus_status() -> dict:
    counts: dict[str, int] = {}
    sections: dict[str, set[str]] = {}
    metadata = {}
    try:
        collection = get_collection()
        metadata = collection.metadata or {}
        for record in collection.get(include=['metadatas'])['metadatas']:
            act = record['act']
            counts[act] = counts.get(act, 0) + 1
            sections.setdefault(act, set()).add(record['section'])
    except CorpusUnavailable:
        pass
    acts = [{'act': spec.act, 'chunks': counts.get(spec.act, 0),
             'sections': len(sections.get(spec.act, set())), 'historical': spec.historical,
             'source_url': spec.url} for spec in ACTS]
    return {'seeded': bool(counts), 'complete': all(a['chunks'] > 0 for a in acts),
            'total_chunks': sum(counts.values()), 'acts': acts,
            'seeded_at': metadata.get('seeded_at'), 'embedding_model': settings.embedding_model,
            'generation_available': bool(settings.openai_api_key), 'notice': NOTICE}


def parse_pdf(path: Path, spec: ActSpec) -> list[dict]:
    """Split actual section bodies (not the contents table), retaining PDF page anchors."""
    import fitz
    with fitz.open(path) as pdf:
        pages = [page.get_text('text', sort=True) for page in pdf]
    # A provision heading ends in an em dash; table-of-contents lines do not.
    text = '\n'.join(pages)
    compact = lambda value: re.sub(r'[^a-z0-9]', '', value.casefold())
    if spec.act in {act.act for act in ACTS} and compact(spec.title) not in compact(text[:30000]):
        raise ValueError(f'{spec.act}: PDF does not contain the expected English act title')
    offsets, cursor = [], 0
    for page in pages:
        offsets.append(cursor)
        cursor += len(page) + 1
    heading = re.compile(
        r'^[ \t]*(?:\d+\*?\[)?(\d{1,3}[A-Z]?)\.[ \t]+'
        r'((?:(?!—|\.--|\.–)[^\n]|\n(?![ \t]*(?:\n|\d))){3,300}?)[ \t]*(?:\.—|—|\.--|\.–)', re.M)
    candidates = list(heading.finditer(text))
    matches = []
    last = (0, '')
    for match in candidates:
        number = match[1]
        title = re.sub(r'\s+', ' ', match[2]).strip(' .—–')
        if re.match(r'(?:Subs\.|Ins\.|Omitted|Rep\.|See |For |The words|Added by)', title, re.I):
            continue
        order = (int(re.match(r'\d+', number)[0]), re.sub(r'\d+', '', number))
        if not matches and number != '1':
            continue
        if order[0] > spec.maximum_section or order[0] > last[0] + 20:
            continue
        if order <= last:
            continue
        matches.append(match)
        last = order
    sections = {}
    for index, match in enumerate(matches):
        number = match[1]
        title = re.sub(r'\s+', ' ', match[2]).strip(' .—–')
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        if index == len(matches) - 1:
            schedule = re.search(r'(?m)^[ \t]*(?:THE )?FIRST SCHEDULE', text[match.end():])
            if schedule:
                end = match.end() + schedule.start()
        raw_body = text[match.start():end]
        start = match.start() + len(raw_body) - len(raw_body.lstrip())
        body = raw_body.strip()
        if len(body) < 30:
            continue
        page = next((i for i, offset in enumerate(offsets) if offset > match.start()), len(offsets))
        sections[number] = {'section': number, 'title': title, 'text': body, 'page': max(1, page),
                            'page_breaks': [(offset - start, i + 1) for i, offset in enumerate(offsets)
                                            if start < offset < end]}
    if len(sections) < spec.minimum_sections:
        raise ValueError(f'{spec.act}: only {len(sections)} provision bodies found; expected at least '
                         f'{spec.minimum_sections}. Refusing to index a contents page or wrong document.')
    return list(sections.values())


def chunk_sections(sections: list[dict], spec: ActSpec, source_url: str | None = None) -> list[dict]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150, add_start_index=True,
                                              separators=['\n\n', '\n', '. ', ' ', ''])
    chunks = []
    for section in sections:
        for index, document in enumerate(splitter.create_documents([section['text']])):
            passage = document.page_content
            page = section['page']
            for offset, page_number in section.get('page_breaks', []):
                if offset <= document.metadata['start_index']:
                    page = page_number
            # Text is a verbatim substring of the source section, not a generated summary.
            digest = hashlib.sha256(f'{spec.act}|{section["section"]}|{index}|{passage}'.encode()).hexdigest()
            chunks.append({'id': digest, 'text': passage, 'metadata': {
                'act': spec.act, 'section': section['section'], 'title': section['title'],
                'source_url': source_url or spec.url, 'page': page, 'chunk_index': index,
                'historical': spec.historical,
            }})
    return chunks


def seed_corpus(*, force: bool = False, source_dir: Path | None = None, acts: list[str] | None = None) -> dict:
    import httpx

    client = get_client()
    try:
        current = get_collection()
    except CorpusUnavailable:
        current = None
    if current is not None and not force:
        return {'skipped': True, **corpus_status()}
    selected = [spec for spec in ACTS if not acts or spec.act in acts]
    # Parse and embed before replacing anything: failed downloads leave the last good corpus intact.
    chunks = []
    for spec in selected:
        filename = re.sub(r'\W+', '_', spec.act.lower()) + '.pdf'
        path = (source_dir or settings.corpus_dir) / filename
        if not path.exists():
            if source_dir:
                raise FileNotFoundError(f'Missing {path}')
            response = httpx.get(spec.url, timeout=45, follow_redirects=True)
            response.raise_for_status()
            if not response.content.startswith(b'%PDF'):
                raise ValueError(f'{spec.act}: source did not return a PDF')
            path.write_bytes(response.content)
        chunks.extend(chunk_sections(parse_pdf(path, spec), spec))
    from sentence_transformers import SentenceTransformer
    encoder = SentenceTransformer(settings.embedding_model, device='cpu',
                                  cache_folder=str(settings.corpus_dir / 'models'), trust_remote_code=False)
    encoder.save(str(settings.corpus_dir / 'models' / 'local'))
    embeddings = encoder.encode([c['text'] for c in chunks], normalize_embeddings=True,
                                show_progress_bar=True, batch_size=32).tolist()
    # Use a new collection until all vectors are safely persisted; publish via collection name swap.
    staging_name = f'{COLLECTION}_staging_{datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")}'
    metadata = {'embedding_model': settings.embedding_model, 'ready': True,
                'seeded_at': datetime.now(timezone.utc).isoformat()}
    staging = client.create_collection(staging_name, embedding_function=None,
                                      metadata=metadata, configuration={'hnsw': {'space': 'cosine'}})
    try:
        for offset in range(0, len(chunks), 128):
            batch = chunks[offset:offset + 128]
            staging.add(ids=[c['id'] for c in batch], documents=[c['text'] for c in batch],
                        metadatas=[c['metadata'] for c in batch], embeddings=embeddings[offset:offset + 128])
        # Seeding is an administrative CLI operation; run with the API stopped when replacing.
        existing_names = {c.name for c in client.list_collections()}
        backup_name = f'{staging_name}_backup'
        old = client.get_collection(COLLECTION, embedding_function=None) if COLLECTION in existing_names else None
        if old is not None:
            old.modify(name=backup_name)
        try:
            staging.modify(name=COLLECTION)
        except Exception:
            if old is not None:
                old.modify(name=COLLECTION)
            raise
        if old is not None:
            client.delete_collection(backup_name)
    except Exception:
        if staging_name in {c.name for c in client.list_collections()}:
            client.delete_collection(staging_name)
        raise
    get_encoder.cache_clear()
    return {'skipped': False, **corpus_status()}
