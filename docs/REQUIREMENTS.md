# CaseCrypt — Project Requirements

> **Project**: Smart Legal Case Intelligence System with Blockchain-Based Evidence Integrity
> **Team**: Niharika Singh (1DS23IC033), Meghana Pise (1DS23IC026), Ashab Khan (1DS23IC027), Aditya Piyush (1DS23IC002)
> **Institution**: Dayananda Sagar College of Engineering — Dept. of CSE (IoT & Cyber Security incl. Blockchain)
> **Guide**: Dr. D. Annapurna | Major Project Phase I | AY 2026–2027

---

## 1. Problem Statement

Current legal workflows lack a fast, structured and verifiable way to understand an entire case across multiple documents while preserving evidence integrity.

Legal professionals increasingly work with case files that combine judgments, petitions, affidavits, contracts and digital evidence. Reviewing these materials, connecting facts across documents and confirming that evidence has not been altered remain largely manual tasks.

### Core Pain Points

| # | Pain Point | Impact |
|---|---|---|
| 1 | **Volume overload** | Hundreds of pages per case — slow, error-prone manual review |
| 2 | **Slow legal research** | Locating relevant laws/precedents is unstructured and time-consuming |
| 3 | **Unverified evidence** | No reliable way to confirm a file hasn't been altered after submission |
| 4 | **Hidden contradictions** | Inconsistencies across documents are easy to miss by hand |
| 5 | **Hallucinating AI tools** | Existing legal AI (Lexis+, Westlaw AI) still hallucinate 17–33% of the time |
| 6 | **Indian legal resource gap** | Most legal LLMs target US/Chinese law; Indian-specific corpora are scarce |
| 7 | **No unified pipeline** | Existing tools handle isolated tasks — none combine extraction + retrieval + contradiction + evidence integrity |

---

## 2. Project Objectives

The system is organised around **6 core objectives**:

1. **Extract** key facts — parties, dates, events, claims — from legal documents (OCR + NLP)
2. **Build** a chronological case timeline from scattered documents
3. **Retrieve** relevant Indian statutes and precedents with cited sources (RAG)
4. **Detect** contradictions and inconsistencies across documents for lawyer review
5. **Verify** evidence integrity using blockchain-based hashing (SHA-256 + immutable ledger)
6. **Answer** natural-language queries about the whole case with explainable, source-grounded responses

---

## 3. Functional Requirements

### FR-1: User & Case Management
- Users can register and log in (JWT authentication)
- Each user owns multiple cases; cases are isolated per user
- Case types: Criminal, Civil, Contract, Other
- Users can create, view, update, delete cases

### FR-2: Document Upload
- Supported formats: PDF (native + scanned), DOCX, JPG, PNG
- Files stored per case; metadata recorded in SQLite
- Every uploaded file is SHA-256 hashed and recorded on the blockchain ledger at upload time

### FR-3: OCR & NLP Extraction
- Native PDFs: PyMuPDF text extraction
- Scanned PDFs/images: Tesseract OCR
- DOCX: python-docx extraction
- Extracted entities: parties (petitioner/respondent/counsel), dates, events, claims, cited provisions (IPC sections, CrPC provisions etc.)

### FR-4: Timeline Construction
- All extracted events across all documents in a case are normalised by date
- Timeline is ordered chronologically and annotated with source document
- Viewable in the UI as an interactive vertical timeline

### FR-5: Legal Research (RAG)
- Indian legal corpus seeded at startup: IPC, CrPC, Constitution, Evidence Act, IT Act
- Source: IndiaCode.gov.in (downloaded and parsed once)
- Lawyer asks a question in natural language → gets a cited answer from the corpus
- Each answer includes: response text + source statute + section + exact passage

### FR-6: Case Similarity
- Uploaded case facts compared against corpus of known cases
- Weighted combination of BM25 lexical (40%) + semantic cosine (60%) similarity
- Key facts and cited provisions weighted higher than boilerplate

### FR-7: Contradiction Detection
- Cross-document: compare statements across all documents in a case (FIR vs affidavit vs judgment)
- Staged pipeline: semantic filter → DeBERTa NLI → GPT-4o verifier
- Each flag includes: statement A, statement B, source documents, contradiction type, confidence score
- Lawyer can mark flags as Reviewed or Dismissed

### FR-8: Blockchain Evidence Integrity
- SHA-256 hash recorded on upload (append-only SQLite ledger)
- Custody events logged: UPLOAD, ACCESS, VERIFY, TRANSFER
- "Verify" action re-hashes current file and compares with ledger record
- Result: ✅ INTACT or ❌ TAMPERED
- Full chain-of-custody audit log visible per file

### FR-9: Natural Language Q&A
- Lawyer asks questions about the active case in plain English
- System answers using extracted entities + knowledge graph + statute corpus
- All answers are citation-grounded; lawyer can expand source passages

---

## 4. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | Document extraction < 30s for a 50-page PDF |
| **Security** | Passwords bcrypt-hashed; JWT tokens; files stored server-side only |
| **Privacy** | Case files never sent to third parties; documents kept off-chain |
| **Reliability** | Blockchain ledger is append-only — no UPDATE/DELETE ever issued |
| **Explainability** | Every AI output (RAG answer, contradiction flag) cites its source |
| **Human Oversight** | All AI outputs are for lawyer review — system is decision support, not autonomous advisor |
| **Scalability** | Phase I: Docker Compose single-host deploy with persistent SQLite volume |
| **Auditability** | Full chain-of-custody log for every evidence file |

---

## 5. System Constraints

- Indian legal context is the primary target; models trained on other jurisdictions may not transfer directly
- The blockchain is a simulated permissioned ledger (SQLite + SHA-256) for Phase I; real Hyperledger Fabric is a future-phase upgrade
- Blockchain does **not** prove lawful collection of evidence — only integrity since recording
- OCR quality depends on scan quality; very poor scans may require human-in-the-loop review
- LLM outputs (GPT-4o) may hallucinate — system design constrains generation to retrieved context

---

## 6. Literature Foundation (Key References)

| Ref | Paper | Relevance |
|---|---|---|
| [1] | Lai et al., "Large language models in law: A survey," AI Open 2024 | Legal LLM landscape |
| [2] | Hou et al., "LLMs meet legal AI: A survey," arXiv 2025 | 16 legal LLM series, 47 frameworks |
| [3] | Lewis et al., "RAG for knowledge-intensive NLP," NeurIPS 2020 | RAG foundation |
| [4] | Magesh et al., "Hallucination-free?," JELS 2025 | Commercial legal tools hallucinate 17–33% |
| [5] | Lone & Mir, "Forensic-Chain," 2019 | Blockchain chain-of-custody foundation |
| [6] | B-CoC, private Ethereum custody | Blockchain prototype evaluation |
| [7] | ContraDoc dataset | Self-contradiction detection benchmark |
| [8] | IL-PCSR | Indian legal precedent + statute retrieval corpus |
| [9] | LEGAL-BERT | Domain-specific legal language model |
| [10] | DELTA | Fact-focused case embedding for similarity |
| [11] | LCM-LAI | Law-article-aware case similarity |
| [12] | LegalWiz | Multi-agent contradiction detection framework |

---

## 7. Keywords

`legal artificial intelligence` · `legal NLP` · `legal document intelligence` · `retrieval-augmented generation` · `case similarity` · `contradiction detection` · `blockchain` · `evidence integrity` · `chain of custody` · `Indian legal technology`
