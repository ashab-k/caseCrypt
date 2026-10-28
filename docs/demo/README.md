# Fictional CaseCrypt demo

All people, events, court details, exhibits, and transactions in these documents are invented. They are test fixtures, not legal advice or real filings.

1. Restart/rebuild the backend and frontend with the latest code.
2. Create a **Criminal** case called **Asha Mehta v. Rohan Shah — fictional demo**.
3. Upload `01_mock_complaint.docx` and `02_mock_hearing_order.docx` into that same case. PDFs with identical content are also included: choose **either DOCX or PDF**, not both copies.
4. Open the case and choose **Run extraction**. For previously processed documents, choose **Re-run all** to replace cached extraction results.

The offline, pattern-based extractor should produce:

- Petitioner: Asha Mehta; respondent: Rohan Shah; counsel: Priya Rao.
- Two distinct provisions: IPC section 420 and CrPC section 154.
- Three party claims/submissions, with the respondent's dispute retained.
- Six dated timeline events, ordered as follows:

| Date | Event |
| --- | --- |
| 12 Jun 2023 | Mock payment transferred |
| 19 Jun 2023 | Alleged non-delivery incident |
| 22 Jun 2023 | Complaint filed |
| 3 Jul 2023 | Preliminary hearing |
| 10 Jul 2023 | Procedural order for documents |
| 24 Jul 2023 | Further hearing |

No OpenAI key is needed for the offline path. When a key is configured, LLM wording and event counts may vary. Pattern-based extraction deliberately avoids guessing dates from unrelated passages and may miss implicit facts in complex real judgments.

DOCX files exercise direct text extraction, and these PDFs have a text layer. To test actual OCR, upload `01_mock_complaint_scan.png` **instead of** the complaint DOCX/PDF, together with the hearing record. The scan was checked with Tesseract and recovered all three complaint dates. DOCX does not expose reliable physical page numbers; the current extractor treats its text as one logical page.

Regenerate the DOCX fixtures with `python scripts/create_demo_documents.py` (requires `python-docx`). Regression tests live in `backend/tests`; run from the repository root with `PYTHONPATH=backend backend/venv/bin/python -m unittest discover -s backend/tests -v` after installing the backend requirements.
