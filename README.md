# Approval Folio · development component

**An open-source Filestage alternative in preparation for versioned PDF and image approvals.**

> Local library only. No browser workspace, HTTP service, hosted demo, or public release yet.

```mermaid
flowchart LR
    A[Upload a file version] --> B[Reviewer retrieves exact bytes]
    B --> C{Decision on current version}
    C --> D[Approve]
    C --> E[Request changes with a note]
    D --> F{All reviewers approved?}
    F --> G[Current version approved]
    E --> H[Upload next version]
    H --> B
```

The implemented core stores immutable PDF/PNG/JPEG versions in SQLite. Each reviewer has a separate revocable key. Decisions refer to a version number and SHA-256 digest; a new version requires fresh decisions from everyone, even if the file content is identical. History remains available for export.

| Implemented | Still required |
| :--- | :--- |
| Independent reviewer credentials | Owner-authenticated HTTP boundary |
| Immutable files and decision history | Bounded PDF-processing worker |
| Approve or request changes with a note | Polished owner/reviewer browser UI |
| Stale-version, wrong-hash and cross-project rejection | Six languages and browser acceptance |
| JSON history export and old-version retrieval | WSGI/container setup and recovery tests |

## Run the core checks

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Fifteen tests cover reviewer consensus, new-version reset, stale uploads/decisions, byte-digest matching, per-reviewer retrieval, change-request notes, token revocation, project isolation, storage limits, persistence and file validation.

## Exact boundaries

- Owner methods (`create`, `upload`, `rotate`, `view`, `export`) rely on their caller for authentication. Do not expose this library directly over HTTP.
- Reviewer keys identify an assigned review slot, not a verified human identity. These decisions are not legal signatures.
- The core requires a recorded file retrieval before a reviewer can decide. Retrieval does not prove that the person read or understood the file.
- Up to 20 fixed reviewers per project; 10 MiB per file and 100 MiB per project including history. PDFs must be unencrypted and have 1–100 pages. Images are normalized to metadata-free PNG, at most 16 megapixels and 10 MiB after normalization.
- PDFs are parsed for structural acceptance but are **not sanitized or malware-scanned**. Resource-bounded PDF processing and attachment-only HTTP delivery must be added before a server is offered. No in-browser PDF rendering exists yet.
- No email delivery, reviewer groups, threaded annotations, version comparison UI, or full Filestage parity is claimed.

[Scope and distribution plan](docs/SCOPE.md) · [MIT license](LICENSE)
