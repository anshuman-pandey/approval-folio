# Approval Folio

### Know exactly which version was approved.

Share versioned PDFs and images, gather reviewer decisions, and export the approval history. A focused, self-hosted alternative to Filestage for file approvals.

[![CI](https://github.com/anshuman-pandey/approval-folio/actions/workflows/check.yml/badge.svg)](https://github.com/anshuman-pandey/approval-folio/actions/workflows/check.yml) · [MIT license](LICENSE) · Python + SQLite · Self-hosted

![Approval Folio: actual application workspace](docs/assets/workspace.png)

**Public source preview.** The local workflow and container recovery have been tested. There is no hosted demo or tagged product release yet; public HTTPS acceptance remains pending.

## How it works

1. Create a project and assign up to 20 reviewer slots with separate private invitations.
2. Upload a PDF, PNG or JPEG. Reviewers download that version and approve it or request changes with a note.
3. Upload a revision to start a fresh approval round, or export the complete JSON decision history.

## Try it locally

Requires Git, Python 3 and Docker with the Compose plugin.

```sh
git clone https://github.com/anshuman-pandey/approval-folio.git
cd approval-folio
python3 scripts/setup.py
docker compose up --build -d
```

Open **http://127.0.0.1:8093**. Read the generated private `.env` file locally and use its `APPROVAL_OWNER_KEY` value to unlock the owner workspace. Setup retains any existing `.env`; do not commit or share this file.

The app binds to localhost and stores data in a persistent Docker volume. Links pointing to localhost work only on your computer. For remote sharing, follow the [HTTPS deployment and backup guide](docs/DEPLOYMENT.md). Avoid `docker compose down -v` unless you intend to delete the stored data.

## Included

- Immutable versions with decisions tied to the exact file hash.
- A new upload resets unanimous approval, even when the file bytes are identical.
- Separate revocable reviewer credentials and persistent review history.

**Interface languages:** English, German, Spanish, Japanese, Simplified Chinese and Traditional Chinese. Native-speaker review is still pending. User-authored content is never translated.

## Know the boundaries

Files are limited to 10 MiB, projects to 100 MiB, PDFs to 1–100 unencrypted pages and images to 16 megapixels. Reviewer slots are not verified identities or legal signatures. Requiring a download does not prove that someone read the file. PDF structural checks are bounded but are not malware scanning or sanitization. No email delivery, threaded annotations, groups or visual version comparisons.

Private links and reviewer keys grant access to whoever holds them. Keep the owner key separate from participant credentials. This project covers the workflow above, not the full feature set of its commercial reference.

## Development and checks

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

The published baseline passed **26 Python tests**. Recorded browser acceptance covers: version upload, reviewer download and decisions, approval reset, history export and revocation. Container restart and clean-volume backup/restore were also checked. See the [validation record](artifacts/validation.json) for the exact evidence and remaining acceptance gates.

Bug reports should include reproduction steps and browser/runtime versions, with private keys and client data removed. Focused fixes and improvements are welcome through [issues](https://github.com/anshuman-pandey/approval-folio/issues) and pull requests.

## Documentation

[Deployment & backups](docs/DEPLOYMENT.md) · [Api guide](docs/API.md) · [Scope & comparison](docs/SCOPE.md) · [Validation evidence](artifacts/validation.json) · [License](LICENSE)

## Current verification

See the [26 November audit checkpoint](docs/AUDIT.md) for the verified repository, release links, fresh core test result and remaining deployment/browser gates. Earlier validation records remain dated evidence.
