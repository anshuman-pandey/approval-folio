# Approval Folio local preview

Open-source alternative for Filestage workflows: versioned PDF/image files, reviewer decisions, revocable access and approval-history export. Independent MIT-licensed source; no public repository, release or deployment is claimed.

## Run locally

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python3 scripts/setup.py
docker compose up --build -d
```

Read the private `.env` locally for the owner key. Open http://127.0.0.1:8093, unlock, create a project and save its private reviewer invitations. Upload a PDF/image, open each invitation, download and review the file, and submit decisions. A newer version resets approval. Localhost invitations work on the same machine only. See [deployment and recovery](docs/DEPLOYMENT.md).

English, German, Spanish, Japanese, Simplified Chinese and Traditional Chinese interfaces are included. User-authored names and notes remain unchanged. Native-speaker review and public HTTPS acceptance remain pending.

Automated evidence: Python core/API/catalog checks; Chromium full approval workflow and language preference, storage, draft/file preservation and narrow layout checks. Previous container acceptance verifies PDF bytes, approvals/history and new writes after restart/clean-volume restore. No real human review, legal signature, malware scan or public launch is implied.

## Owner publication handoff

[Prefilled GitHub repository form](https://github.com/new?name=approval-folio&description=Open-source%20alternative%20to%20Filestage%20for%20versioned%20PDF%20and%20image%20approvals.%20Reviewer%20decisions%2C%20revocable%20access%2C%20approval%20history%20and%20JSON%20export.%20Self-hosted%2C%20six%20languages%2C%20MIT%20licensed.&visibility=public)

Create the empty repository under anshuman-pandey without an initial README/license, then give the product-specific go-ahead to push. Existing work will be inspected first. Name remains provisional pending owner review. Repository publication is separate from a tested release or hosted deployment.
