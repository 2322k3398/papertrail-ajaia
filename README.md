# Papertrail — collaborative document workspace

Papertrail is a deliberately scoped, full-stack document editor built for the Ajaia AI-Native Full Stack Developer assignment. It supports document creation, renaming, browser editing, basic rich text, `.txt`/`.md` import, SQLite persistence, and seeded-user sharing with view/edit permissions.

## Features
- Create, rename, edit, save, and reopen documents.
- Basic formatting: bold, italic, underline, headings, bullets, and numbered lists.
- Debounced autosave to a Flask JSON API.
- Import `.txt` and `.md` files (up to 1 MB); imported content is escaped and placed into a preformatted block.
- Demo accounts, owner/shared document lists, and share permissions (`view` or `edit`).
- SQLite persistence and automated tests for save/persistence and sharing authorization.

## Run locally
Requires Python 3.11+.

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## Demo accounts
No passwords are used; select an account on the login screen:
- Vishnu Priya — `vishnupriya200636@gmail.com` (owner account)
- Alex Morgan — `alex@example.com`
- Sam Taylor — `sam@example.com`

To demonstrate sharing: sign in as Vishnu Priya, create a document, share it with Alex or Sam, then use **Switch user** to sign in as the invited user. View-only access is enforced by the save API.

## Tests
```bash
pytest -q
```

## Deployment
The repository includes a `Procfile` and `render.yaml` for a Render web service. Set `SECRET_KEY` to a strong random value. **Important:** the provided Render configuration uses `/tmp/documents.db` as a simple demo database path. Some hosting environments clear temporary storage on restart/redeploy, so this is suitable only for a review demo and not durable production storage. For a durable deployment, use a persistent disk or managed database. A free hosted instance may sleep when idle.

## Scope and limitations
- Demo identity selection is not real authentication. Anyone can switch accounts.
- Rich text uses the browser's `contenteditable` and `execCommand` for a lightweight assessment implementation; this is not a full editor framework.
- No real-time simultaneous editing, comments, version history, or external email invitations.
- Only `.txt` and `.md` are imported; DOCX and PDF are not supported.
- Formatting HTML is stored as document content. This is a small internal-demo app, not hardened for untrusted multi-tenant production input.

## Architecture
See `ARCHITECTURE.md` and `AI_WORKFLOW.md`.
