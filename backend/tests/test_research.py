"""Offline Phase 3 regressions with real Chroma and deterministic test embeddings."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import chromadb
import fitz
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from database import get_db
from middleware.auth import get_current_user
from models.research import ResearchRequest, ResearchResponse
from routers.rag import router
from services import corpus_service as corpus, rag_service as rag


class ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = chromadb.EphemeralClient()
        cls.collection = cls.client.create_collection('test_' + uuid4().hex, embedding_function=None,
            configuration={'hnsw': {'space': 'cosine'}}, metadata={'ready': True, 'seeded_at': uuid4().hex})
        cls.collection.add(ids=['ipc302','crpc302','evidence65b'],
            documents=['Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.',
                       'Any Magistrate inquiring into or trying a case may permit the prosecution to be conducted by any person.',
                       'Any information contained in an electronic record which is printed on a paper shall be deemed to be also a document.'],
            metadatas=[{'act':act,'section':number,'title':title,'source_url':'https://indiacode.gov.in/example.pdf','page':page,'chunk_index':0,'historical':True}
                for act,number,title,page in [('IPC','302','Punishment for murder',10),('CrPC','302','Permission to conduct prosecution',20),('Evidence Act','65B','Admissibility of electronic records',30)]],
            embeddings=[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])

    def setUp(self):
        self.get = patch.object(rag, 'get_collection', return_value=self.collection)
        self.encode = patch.object(rag, 'encode', return_value=[[1.,0.,0.]])
        self.get.start();self.encode.start();rag.lexical_index.cache_clear()
        self.key=patch.object(rag.settings,'openai_api_key','');self.key.start()

    def tearDown(self):
        self.get.stop();self.encode.stop();self.key.stop()
        rag.lexical_index.cache_clear()

    def test_exact_reference_never_returns_other_act(self):
        result=rag.query('What is Section 302 IPC?')
        self.assertEqual([(s['act'],s['section']) for s in result['sources']],[('IPC','302')])
        self.assertEqual(result['generation_mode'],'extractive')
        self.assertIn('imprisonment for life',result['answer'])
        self.assertTrue(result['sources'][0]['url'].endswith('#page=10'))
        ResearchResponse(**result)

    def test_missing_section_does_not_substitute_a_neighbor(self):
        self.assertEqual(rag.query('What is section 999 IPC?')['sources'],[])

    def test_conflicting_act_filter_returns_no_answer(self):
        self.assertEqual(rag.query('Section 302 IPC',act='CrPC')['generation_mode'],'unavailable')
        self.assertEqual(rag.query('Compare Section 302 IPC and Section 154 CrPC')['sources'],[])

    def test_replacement_laws_outside_corpus_do_not_return_historical_answers(self):
        self.assertEqual(rag.query('What is the punishment for murder under BNS?')['sources'],[])

    def test_multiple_exact_references_require_support_for_every_reference(self):
        result=rag.query('Compare Section 302 IPC and Section 999 IPC')
        self.assertEqual(result['sources'],[])
        self.assertEqual(rag.query_filters('Sections 302 and 304 IPC',None),('IPC',['302','304'],False))

    def test_hybrid_retrieval_and_filter(self):
        result=rag.retrieve('punishment for murder',act='IPC')
        self.assertEqual(result['sources'][0]['act'],'IPC')
        self.assertEqual(result['retrieval_mode'],'hybrid')

    def test_semantic_failure_uses_lexical_search(self):
        with patch.object(rag,'encode',side_effect=RuntimeError('offline')):
            with self.assertLogs(rag.logger,level='WARNING'):
                result=rag.retrieve('punishment for murder')
        self.assertEqual(result['retrieval_mode'],'lexical')
        self.assertEqual(result['sources'][0]['act'],'IPC')

    def test_bad_citations_and_invented_quotes_fall_back_to_excerpts(self):
        for row in [dict(text='An invented statement',citations=['S999'],supporting_quote='murder'),
                    dict(text='An invented statement',citations=['S1'],supporting_quote='not in the source')]:
            with self.subTest(row=row),patch.object(rag.settings,'openai_api_key','test-key'),patch.object(rag,'synthesize',return_value={'statements':[row]}):
                with self.assertLogs(rag.logger,level='WARNING'):
                    result=rag.query('Section 302 IPC')
                self.assertEqual(result['generation_mode'],'extractive')
                self.assertNotIn('An invented statement',result['answer'])

    def test_valid_cited_synthesis(self):
        with patch.object(rag.settings,'openai_api_key','test-key'),patch.object(rag,'synthesize',return_value={'statements':[
            {'text':'The excerpt describes punishment for murder.','citations':['S1'],'supporting_quote':'Whoever commits murder'}]}):
            result=rag.query('Section 302 IPC')
        self.assertEqual(result['generation_mode'],'openai')
        self.assertIn('[S1]',result['answer'])

    def test_request_bounds(self):
        for payload in [{'question':'   '},{'question':'x'*2001},{'question':'valid','top_k':11},{'question':'valid','act':'BNS'}]:
            with self.subTest(payload=payload),self.assertRaises(ValidationError):ResearchRequest(**payload)

    def test_routes_require_auth_and_validate_input(self):
        app=FastAPI();app.include_router(router,prefix='/api')
        async def empty_db():yield None
        app.dependency_overrides[get_db]=empty_db
        with TestClient(app) as client:
            self.assertEqual(client.post('/api/query',json={'question':'Section 302 IPC'}).status_code,401)
            self.assertEqual(client.get('/api/corpus/status').status_code,401)
            app.dependency_overrides[get_current_user]=lambda:object()
            self.assertEqual(client.post('/api/query',json={'question':'   '}).status_code,422)
            result=client.post('/api/query',json={'question':'Section 302 IPC'})
            self.assertEqual(result.status_code,200)
            self.assertEqual(result.json()['sources'][0]['section'],'302')


class CorpusParsingTests(unittest.TestCase):
    def test_parser_ignores_contents_and_preserves_page_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'statute.pdf'
            pdf=fitz.open()
            page=pdf.new_page();page.insert_text((60,60),'CONTENTS\n1. Short title.\n2. Second provision.')
            page=pdf.new_page();page.insert_text((60,60),'1. Short title.--This Act is a test fixture.\n2. Second provision.--This is the second test provision.')
            pdf.save(path);pdf.close()
            spec=corpus.ActSpec('Test','Test Act','https://indiacode.gov.in/test.pdf',minimum_sections=2)
            result=corpus.parse_pdf(path,spec)
            self.assertEqual([s['section'] for s in result],['1','2'])
            self.assertEqual([s['page'] for s in result],[2,2])
            self.assertIn('test fixture',result[0]['text'])

    def test_wrong_or_empty_pdf_is_not_indexed(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'empty.pdf';pdf=fitz.open();pdf.new_page();pdf.save(path);pdf.close()
            with self.assertRaises(ValueError):corpus.parse_pdf(path,corpus.ACTS[0])

    def test_chunk_ids_are_deterministic_and_text_is_verbatim(self):
        spec=corpus.ACTS[0]
        text='1. Sample.--'+('A long statutory test passage. '*80)
        sections=[{'section':'1','title':'Sample','text':text,'page':2}]
        a=corpus.chunk_sections(sections,spec);b=corpus.chunk_sections(sections,spec)
        self.assertEqual([c['id'] for c in a],[c['id'] for c in b])
        self.assertTrue(all(c['text'] in text for c in a))

class CorpusSeedingTests(unittest.TestCase):
    def test_existing_seed_is_idempotent_without_loading_model(self):
        with patch.object(corpus,'get_client'),patch.object(corpus,'get_collection',return_value=object()),patch.object(corpus,'corpus_status',return_value={'seeded':True}):
            self.assertEqual(corpus.seed_corpus(),{'skipped':True,'seeded':True})

    def test_failed_force_download_preserves_existing_collection(self):
        from unittest.mock import Mock
        client=Mock()
        with tempfile.TemporaryDirectory() as directory,patch.object(corpus,'get_client',return_value=client),patch.object(corpus,'get_collection',return_value=object()):
            with self.assertRaises(FileNotFoundError):corpus.seed_corpus(force=True,source_dir=Path(directory))
        client.create_collection.assert_not_called()
        client.delete_collection.assert_not_called()
