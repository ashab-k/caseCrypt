# Phase 5 — Blockchain Evidence Integrity

> **Status**: ⏳ Pending
> **Goal**: Guarantee tamper-evident chain of custody using SHA-256 cryptographic hashing on an append-only immutable ledger.
> **Depends on**: Phase 1 (documents uploaded and stored in MongoDB)
> **Unlocks**: Court-admissible electronic evidence compliance (Section 65B Indian Evidence Act) and full case audit readiness

---

## What This Phase Builds

| Area | What |
|---|---|
| **Backend** | Append-only SQLite blockchain ledger (`backend/data/ledger.db`), cryptographic SHA-256 block creation, custody event logging (`UPLOAD`, `ACCESS`, `VERIFY`, `TRANSFER`, `EXPORT`), on-demand file re-hashing verification, Section 65B electronic evidence certificate generation |
| **Frontend** | Evidence integrity badge (green `INTACT` vs red `TAMPERED`), interactive chain-of-custody audit log table, one-click "Verify Now" re-hash trigger, downloadable cryptographic custody certificate |

---

## Key Invariants (Non-Negotiable)

1. **Strictly Append-Only**: Zero `UPDATE` or `DELETE` SQL operations ever executed on `ledger.db`. Database triggers and application guards enforce immutability.
2. **Documents Stay Off-Chain**: The physical files remain stored in `backend/data/uploads/`; only cryptographic SHA-256 digests and audit metadata reside on the ledger.
3. **Deterministic Verification**: File integrity is verified by streaming disk bytes through SHA-256 on demand and comparing the result with the original `UPLOAD` transaction digest.
4. **Full Custody Trail**: Every touchpoint (upload, view/read, verify, export) generates a signed transaction entry.

---

## Backend Files

| File | Purpose |
|---|---|
| `services/blockchain_service.py` | Ledger initialization, block mining/creation, SHA-256 computation, hash chain validation, file verification |
| `services/certificate_service.py` | Generates Indian Evidence Act Section 65B compliance certificates (JSON/PDF) |
| `routers/blockchain.py` | POST /evidence/{id}/verify, GET /evidence/{id}/audit-trail, GET /cases/{id}/integrity, GET /blockchain/status |

---

## Cryptographic Ledger Architecture

The system implements a permissioned, append-only cryptographic block log stored in SQLite (`backend/data/ledger.db`).

```
Block 0 (Genesis)              Block 1                        Block 2
┌──────────────────────┐       ┌──────────────────────┐       ┌──────────────────────┐
│ Index: 0             │       │ Index: 1             │       │ Index: 2             │
│ PrevHash: "0"*64     │◄──────│ PrevHash: Hash(B0)   │◄──────│ PrevHash: Hash(B1)   │
│ Timestamp: T0        │       │ Timestamp: T1        │       │ Timestamp: T2        │
│ MerkleRoot: MR0      │       │ MerkleRoot: MR1      │       │ MerkleRoot: MR2      │
│ BlockHash: Hash(B0)  │       │ BlockHash: Hash(B1)  │       │ BlockHash: Hash(B2)  │
└──────────┬───────────┘       └──────────┬───────────┘       └──────────┬───────────┘
           │                              │                              │
     [Tx: Genesis]               [Tx: Doc1 UPLOAD]              [Tx: Doc1 VERIFY]
                                 [Tx: Doc2 UPLOAD]              [Tx: Doc1 ACCESS]
```

### Hash Formulae
- **Transaction Hash**:  
  `tx_hash = SHA256(tx_id + doc_id + action + file_hash + performed_by + timestamp)`
- **Block Hash**:  
  `block_hash = SHA256(str(block_index) + prev_hash + merkle_root + timestamp + str(nonce))`

---

## Ledger Database Schema (`ledger.db`)

### `blocks` Table
```sql
CREATE TABLE IF NOT EXISTS blocks (
    block_index INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    merkle_root TEXT NOT NULL,
    block_hash TEXT NOT NULL UNIQUE,
    nonce INTEGER DEFAULT 0
);
```

### `custody_events` Table
```sql
CREATE TABLE IF NOT EXISTS custody_events (
    tx_id TEXT PRIMARY KEY,
    block_index INTEGER NOT NULL,
    doc_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    action TEXT NOT NULL, -- 'UPLOAD' | 'ACCESS' | 'VERIFY' | 'TRANSFER' | 'EXPORT'
    performed_by TEXT NOT NULL,
    client_ip TEXT,
    timestamp TEXT NOT NULL,
    details TEXT, -- JSON string with extra context
    tx_hash TEXT NOT NULL,
    FOREIGN KEY(block_index) REFERENCES blocks(block_index)
);
```

---

## Verification Algorithms

### 1. Ledger Chain Integrity Check
Validates that the blockchain itself has not been tampered with:
```python
def validate_chain() -> bool:
    blocks = get_all_blocks_ordered()
    for i in range(1, len(blocks)):
        prev = blocks[i - 1]
        curr = blocks[i]
        
        # Check parent pointer
        if curr.prev_hash != prev.block_hash:
            return False
            
        # Re-compute block hash
        expected_hash = compute_block_hash(curr)
        if curr.block_hash != expected_hash:
            return False
            
    return True
```

### 2. Document Byte Integrity Check
Validates whether a physical document on disk has been modified since upload:
```python
def verify_document_integrity(doc_id: str, file_path: Path) -> dict:
    # 1. Compute current SHA-256 from disk in 64KB chunks
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    current_hash = hasher.hexdigest()

    # 2. Query initial UPLOAD transaction from ledger
    upload_tx = get_initial_upload_tx(doc_id)
    genesis_hash = upload_tx["file_hash"]

    # 3. Compare hashes
    is_intact = (current_hash == genesis_hash)

    # 4. Log VERIFY event to ledger
    log_custody_event(
        doc_id=doc_id,
        action="VERIFY",
        file_hash=current_hash,
        status="INTACT" if is_intact else "TAMPERED"
    )

    return {
        "status": "INTACT" if is_intact else "TAMPERED",
        "current_hash": current_hash,
        "genesis_hash": genesis_hash,
        "tamper_detected": not is_intact
    }
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/evidence/{doc_id}/verify` | JWT | Re-computes file hash on disk and compares with ledger |
| GET | `/api/evidence/{doc_id}/audit-trail` | JWT | Returns complete custody history for the document |
| GET | `/api/cases/{id}/integrity-summary` | JWT | Status of all documents in the case (`X of Y intact`) |
| GET | `/api/evidence/{doc_id}/certificate` | JWT | Download Section 65B Indian Evidence Act certificate (JSON/PDF) |
| GET | `/api/blockchain/chain-status` | JWT | Validates entire block sequence and returns ledger health |

---

## Request & Response Examples

### POST `/api/evidence/{doc_id}/verify`
```json
// Response (Intact)
{
  "doc_id": "671ad48f12c98001",
  "filename": "FIR_001.pdf",
  "status": "INTACT",
  "genesis_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "verified_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "last_verified_at": "2026-10-24T22:45:10Z",
  "chain_valid": true
}
```

### GET `/api/evidence/{doc_id}/audit-trail`
```json
// Response
{
  "doc_id": "671ad48f12c98001",
  "total_events": 3,
  "events": [
    {
      "tx_id": "tx_9a8f21...",
      "block_index": 1,
      "action": "UPLOAD",
      "file_hash": "e3b0c44298fc...",
      "performed_by": "advocate_ashab@casecrypt.in",
      "timestamp": "2026-10-24T18:00:00Z"
    },
    {
      "tx_id": "tx_1b7c44...",
      "block_index": 4,
      "action": "ACCESS",
      "file_hash": "e3b0c44298fc...",
      "performed_by": "advocate_ashab@casecrypt.in",
      "timestamp": "2026-10-24T19:30:12Z"
    },
    {
      "tx_id": "tx_3c9d88...",
      "block_index": 7,
      "action": "VERIFY",
      "file_hash": "e3b0c44298fc...",
      "performed_by": "advocate_ashab@casecrypt.in",
      "timestamp": "2026-10-24T22:45:10Z"
    }
  ]
}
```

---

## Section 65B Electronic Evidence Certificate

Under Section 65B of the Indian Evidence Act, 1872 (and Section 63 of Bharatiya Sakshya Adhiniyam, 2023), electronic records are admissible only when accompanied by a certificate certifying device provenance and uncorrupted transmission.

The certificate output includes:
1. **Case Identifier & Court Details**
2. **Document Metadata**: Original file name, MIME type, file size in bytes
3. **Cryptographic Proof**: Genesis SHA-256 digest, block index, transaction ID, timestamp
4. **Chain-of-Custody Log**: Chronological listing of every user access, inspection, or verification
5. **System Certification**: Affirmation that the ledger software operated without interruption or undetected tampering

---

## Frontend Components

| Component | File | Description |
|---|---|---|
| Integrity Badge | `components/blockchain/EvidenceIntegrityBadge.tsx` | Visual status pill (Green: `INTACT`, Red: `TAMPERED`, Gray: `UNVERIFIED`) |
| Audit Trail Table | `components/blockchain/AuditTrailTable.tsx` | Chronological custody timeline showing timestamp, action, actor, and hash |
| Verify Action Button | `components/blockchain/VerifyButton.tsx` | On-demand button triggering live server-side SHA-256 verification |
| Certificate Modal | `components/blockchain/CertificateModal.tsx` | Preview and download window for Section 65B compliance certificate |

---

## Deliverable / Definition of Done

- [ ] Every document upload automatically records a genesis `UPLOAD` transaction in `ledger.db`
- [ ] Blocks are created and cryptographically chained via `prev_hash` and `block_hash`
- [ ] On-demand `/verify` endpoint calculates fresh SHA-256 of file on disk and detects modifications
- [ ] Modifying a single byte in a file on disk causes `/verify` to immediately return `TAMPERED`
- [ ] Chain validation endpoint detects if any past block in `ledger.db` was altered
- [ ] Audit trail endpoint returns complete historical log of all custody actions for any document
- [ ] Frontend displays live integrity badges and opens printable Section 65B certificate
- [ ] Case overview displays overall integrity summary (`All X documents intact`)

---

## Known Limitations

- Phase I implements an append-only SQLite permissioned ledger simulating blockchain immutability; distributed consensus (Hyperledger Fabric / Ethereum private testnet) is designated for Phase II.
- Digital signatures in Phase I use server-side keys; hardware token (e-Mudhra / USB crypto-token) integration is reserved for future enterprise deployment.
- The system proves integrity only from the moment of upload onward; it cannot attest to the authenticity or chain-of-custody prior to digital intake.
