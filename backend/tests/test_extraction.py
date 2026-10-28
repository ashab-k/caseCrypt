"""Offline regressions: no spaCy model or OpenAI request needed."""
import json
import unittest
from datetime import datetime
from types import SimpleNamespace

from services.nlp_service import _extract_heuristic, _normalize_date, _normalize_payload
from services.timeline_service import aggregate_entities, build_timeline


class ExtractionTests(unittest.TestCase):
    def test_indian_and_written_dates(self):
        for raw in ('25.08.2020', '25/08/2020', '25-08-2020', '2020-08-25',
                    '25 August 2020', '25 Aug. 2020', 'August 25, 2020', '25th August 2020'):
            with self.subTest(raw=raw):
                self.assertEqual(_normalize_date(raw), '2020-08-25')
        self.assertIsNone(_normalize_date('2020-02-31'))
        self.assertIsNone(_normalize_date('31.02.2020'))

    def test_source_dates_attach_to_sentences_and_pages(self):
        text = '''--- Page 2 ---
On 25.08.2020, the petitioner filed an affidavit.
On 14/09/2020, the court held a hearing.

--- Page 3 ---
On 17 November 2020, the court disposed of the petition.
'''
        result = _extract_heuristic(text, [])
        self.assertEqual([e['date'] for e in result['events']], ['2020-08-25', '2020-09-14', '2020-11-17'])
        self.assertEqual([e['type'] for e in result['events']], ['filing', 'hearing', 'judgment'])
        self.assertEqual([e['page_number'] for e in result['events']], [2, 2, 3])

    def test_generic_rules_do_not_become_events_or_parties(self):
        text = '''Petitioner: Asha Mehta
Respondent: Rohan Shah
Counsel: Priya Rao

The respondent: husband in the event of his failing to pay interim maintenance.
An affidavit must be filed by both parties at the threshold of litigation.
An application may be filed under Section 125 of the Code of Criminal Procedure.
Iyer in his judgment in Captain Ramesh Chander Kaushal v. Mrs Neha discussed maintenance.
'''
        result = _extract_heuristic(text, [])
        self.assertEqual(result['parties'], {'petitioner': ['Asha Mehta'], 'respondent': ['Rohan Shah'], 'counsel': ['Priya Rao']})
        self.assertEqual(result['events'], [])
        self.assertEqual(result['cited_provisions'][0]['act'], 'CrPC')

    def test_citations_are_bounded_and_deduplicated(self):
        text = '''The assets 125 and paragraphs 24 and 25 are listed.
Section 125 of the Code of Criminal Procedure applies.
Section 125 CrPC is cited again.
Section 24 of the Hindu Marriage Act is also cited.
Section 4 is discussed without an identified act.
'''
        result = _extract_heuristic(text, [{'label': 'SECTION_REF', 'text': 'Section 125'}])
        self.assertEqual([(p['act'], p['section']) for p in result['cited_provisions']],
                         [('CrPC', '125'), ('HMA', '24'), ('Unknown', '4')])

    def test_section_lists_share_only_the_explicitly_cited_act(self):
        result = _extract_heuristic('Sections 24, 25 and 26 of the Hindu Marriage Act are cited.', [])
        self.assertEqual([(p['act'], p['section']) for p in result['cited_provisions']],
                         [('HMA', '24'), ('HMA', '25'), ('HMA', '26')])

    def test_multiline_caption(self):
        result = _extract_heuristic('SUPREME COURT\nAsha Mehta\nVERSUS\nRohan Shah\nCase number 17', [])
        self.assertEqual(result['parties']['petitioner'], ['Asha Mehta'])
        self.assertEqual(result['parties']['respondent'], ['Rohan Shah'])

    def test_ambiguous_dates_are_not_assigned_to_one_event(self):
        result = _extract_heuristic('The order dated 25.08.2020 referred to an affidavit dated 23.08.2020.', [])
        self.assertEqual(result['events'], [])
        self.assertEqual(len(result['dates']), 2)

    def test_llm_dates_are_normalized_and_invalid_dates_rejected(self):
        result = _normalize_payload({'events': [{'date': '25.08.2020', 'description': 'Affidavit filed'}],
                                     'dates': [{'date': '31.02.2020'}, {'date': '25.08.2020'}]})
        self.assertEqual(result['events'][0]['date'], '2020-08-25')
        self.assertEqual([d['date'] for d in result['dates']], ['2020-08-25'])

    def test_date_mentions_alone_do_not_create_timeline_events(self):
        extraction = SimpleNamespace(extracted_at=datetime(2020, 8, 26), events_json='[]',
            dates_json=json.dumps([{'date': '2020-08-25', 'event': 'A referenced date in a cited precedent.'}]))
        document = SimpleNamespace(id='doc-1', original_name='judgment.pdf', file_type='pdf')
        self.assertEqual(build_timeline([(extraction, document)])['events'], [])

    def test_timeline_does_not_duplicate_dated_events(self):
        payload = _extract_heuristic('On 25.08.2020, the petitioner filed an affidavit.', [])
        extraction = SimpleNamespace(extracted_at=datetime(2020, 8, 26), extraction_method='heuristic',
                                     **{f'{key}_json': json.dumps(payload.get(key, [])) for key in
                                        ['events', 'dates', 'parties', 'claims', 'cited_provisions', 'spacy_entities']})
        document = SimpleNamespace(id='doc-1', original_name='affidavit.pdf', file_type='pdf')
        pairs = [(extraction, document)]
        self.assertEqual(len(build_timeline(pairs)['events']), 1)
        self.assertEqual(aggregate_entities(pairs)['extraction_methods'], ['heuristic'])


if __name__ == '__main__':
    unittest.main()
