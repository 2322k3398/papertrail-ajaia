# AI-native workflow note

> Personalize this note before submission so it accurately describes the tools and actions actually used.

## Tools used
- ChatGPT: requirement decomposition, implementation planning, scaffold generation, and review checklist.
- [Add any other tool actually used, such as VS Code, browser devtools, or a coding assistant.]

## Where AI accelerated the work
AI helped turn a broad prompt into a narrow product slice, identify a practical data model, draft the Flask/SQLite route structure, and outline validation and test cases. It also helped organize README, architecture, and tradeoff documentation.

## Human judgment and changes
The scope was intentionally reduced to the essential document lifecycle, text/Markdown import, and seeded-user sharing. Real-time collaboration, external invitations, DOCX parsing, and full authentication were not attempted because they would risk core functionality within the timebox. The deployed storage configuration must be treated as a demo unless durable persistence is configured.

## Verification
- Run `pytest -q` and resolve any failures before submission.
- Manually verify create, rename, format, autosave, refresh/reopen, import, sharing, switching users, and view-only save denial.
- Check upload size/type validation and save API errors.
- Replace this section with the exact checks performed and any issues still open.

## Limitations
The app is an assessment prototype, not a production-ready collaboration platform. Demo account switching is not secure authentication, and contenteditable HTML requires sanitization before accepting untrusted users.
