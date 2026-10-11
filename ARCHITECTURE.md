# Architecture and prioritization

## Product slice
Papertrail focuses on a coherent document lifecycle: create → edit → autosave → reopen → share. A clean document library distinguishes owned files from files shared by others. File import is limited to text and Markdown so the content can be safely represented without adding a DOCX parsing dependency.

## Components
- **Flask routes** render the workspace/editor and expose a small JSON save endpoint.
- **SQLite** stores users, documents, and share grants. Foreign keys and unique constraints keep sharing relationships consistent.
- **Browser editor** uses `contenteditable` with a small formatting toolbar. A debounced save reduces unnecessary requests while preserving the editing flow.
- **Demo identity** uses seeded accounts selected on the login screen. This makes access scenarios testable without introducing an incomplete auth system.

## Access model
The document owner can edit and grant `view` or `edit` access. Shared users see the document in a separate library section. Authorization is checked on document rendering and on every save request; view-only users receive HTTP 403 on attempted writes.

## Tradeoffs
1. Prioritized lifecycle and sharing over real-time collaboration.
2. Used SQLite and seeded identities to keep setup simple and free.
3. Limited import to `.txt` and `.md`; unsupported files receive a clear validation message.
4. Used browser-native rich-text commands instead of adding a heavy editor dependency under the timebox.
5. Avoided a claim of production-grade auth or durable cloud persistence.

## Next 2–4 hours
- Add a production authentication provider and CSRF protection.
- Move deployed persistence to a managed database or persistent disk.
- Sanitize stored HTML with a robust allowlist before rendering.
- Add autosave conflict handling and document version history.
- Add end-to-end browser tests and keyboard accessibility checks.
