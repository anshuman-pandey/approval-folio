# Local development API

All credentials use `Authorization: Bearer <key>`. Credentials in URLs are not accepted. The owner key is set at startup; reviewer keys are generated per project and review slot. Reviewers can see their project's reviewer names and current decisions. This is a shared project review, not a confidential ballot. No CORS access is enabled.

| Method and path | Credential | Input/result |
| --- | --- | --- |
| GET /api/projects | Owner | Project list |
| POST /api/projects | Owner | JSON `title`, `reviewers` array of names; returns ID and reviewer credentials once |
| GET /api/projects/{project} | Owner | Versions and current decisions |
| POST /api/projects/{project}/versions | Owner | Multipart `expected` current version number and `file`; returns version and SHA-256 |
| POST /api/projects/{project}/reviewers/{reviewer}/rotate | Owner | Returns replacement reviewer key; old key immediately denied |
| GET /api/projects/{project}/export | Owner | JSON history attachment, excluding secrets |
| GET /api/review/{project}/{reviewer} | Reviewer | Scoped project state |
| GET /api/review/{project}/{reviewer}/versions/{number} | Reviewer | Attachment; records retrieval; X-Content-SHA256 header |
| POST /api/review/{project}/{reviewer}/decisions | Reviewer | JSON `version`, `sha256`, `decision` (`approved` or `changes_requested`), `note` |

A change request requires a note. Each reviewer must download the exact current version before deciding; uploading a newer version invalidates stale decisions. Retrieval does not prove that a person read the file. Reviewer credentials identify slots, not verified people.

Authentication failures return 401; validation and stale-state errors return 400; oversized requests return 413; malformed JSON/content types return 400/415. Errors are JSON. Clients must reload after stale-state errors. Responses prohibit caching and framing. PDF files remain unsanitized; download and inspect them using an appropriate viewer.

Verified using Flask’s HTTP test client and Chromium owner/reviewer workflow. The English workspace is served at `/`. Production server acceptance remains pending.
