# Approval Folio

**An open-source Filestage alternative in preparation for versioned PDF and image approvals.**

> Local six-language browser preview. Native-speaker review and public HTTPS acceptance remain; no hosted demo or public release.

![Actual owner workspace showing version-specific reviewer decisions](docs/assets/workspace.png)

The implemented core stores immutable PDF/PNG/JPEG versions in SQLite. Each reviewer has a separate revocable key. Decisions refer to a version number and SHA-256 digest; a new version requires fresh decisions from everyone, even if the file content is identical. History remains available for export.

| Implemented | Still required |
| :--- | :--- |
| Independent reviewer credentials and owner authentication | Native-speaker review |
| Immutable files, bounded PDF checks, attachment-only downloads | Native-speaker review |
| Approve or request changes with a note | Production WSGI/container and backup recovery |
| Stale-version, wrong-hash and cross-project rejection | Public HTTPS acceptance |
| JSON history export, persistent container and backup recovery | Public HTTPS acceptance |

## Run the core checks

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Twenty-six tests cover reviewer consensus, new-version reset, stale uploads/decisions, byte-digest matching, per-reviewer retrieval, change-request notes, token revocation, project isolation, storage limits, persistence and file validation.

## Exact boundaries

- Owner methods (`create`, `upload`, `rotate`, `view`, `export`) rely on their caller for authentication. Use the authenticated boundary in `server.py`; do not expose these methods directly.
- Reviewer keys identify an assigned review slot, not a verified human identity. These decisions are not legal signatures.
- The core requires a recorded file retrieval before a reviewer can decide. Retrieval does not prove that the person read or understood the file.
- Up to 20 fixed reviewers per project; 10 MiB per file and 100 MiB per project including history. PDFs must be unencrypted and have 1–100 pages. Images are normalized to metadata-free PNG, at most 16 megapixels and 10 MiB after normalization.
- PDFs are parsed for structural acceptance but are **not sanitized or malware-scanned**. PDF structure checks run in a separate process with 256 MiB address-space and 3-second CPU limits, plus a 5-second parent timeout. These POSIX resource limits were tested on Linux; this is not a sandbox. HTTP downloads are attachment-only. PDF review uses attachment downloads rather than embedded rendering.
- No email delivery, reviewer groups, threaded annotations, version comparison UI, or full Filestage parity is claimed.

[Scope and distribution plan](docs/SCOPE.md) · [MIT license](LICENSE)

## Run the local development API

```sh
export APPROVAL_OWNER_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export APPROVAL_DATABASE=approval.sqlite3
python server.py
```

Listens on `127.0.0.1:8093`. Keep the generated owner key private. This development server is not a production deployment. [API routes and authentication](docs/API.md).

Open http://127.0.0.1:8093 after starting the server. Unlock with the owner key, create a project, save the private reviewer links, and upload a file. Reviewers download a version before submitting a decision. Localhost invitation links work only on the same computer; remote collaboration requires an authorized HTTPS deployment. Reviewer keys stay in tab memory and are removed from the address bar after opening the invitation. Reloading requires reopening the invitation.

[Persistent hosting, private setup and backup recovery](docs/DEPLOYMENT.md). Local container acceptance uses a real PDF and restores approvals and exact file bytes into a clean volume.

Interface languages: English, Deutsch, Español, 日本語, 简体中文 and 繁體中文. Language changes preserve drafts, selected files and user content. [Runnable preview and publication handoff](HANDOFF.md).
