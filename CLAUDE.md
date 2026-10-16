# CLAUDE.md

Instructions for Claude Code sessions working in this repository.

## Architecture rules (strictly enforced)

- Business logic lives in `app/services/` only — never in routes
- Routes handle session + service calls + `render_template` only
- All external API calls wrapped in try/except with a fallback
- No inline styles in templates
- No JS fetch on page load
- `url_for()` always uses the blueprint prefix: `'blueprint_name.function_name'`
- New models are added to the existing `app/models.py` until the codebase warrants separation
- Flask-Migrate manages all schema changes — `db.create_all()` is never used
- CSS scoped to a layout class (e.g. `.forum-layout`) — no Bootstrap utility dependencies for custom layouts

## Git workflow

Every feature or fix is built on its own branch off `master`, never committed directly to `master`.

1. **Branch**: `git checkout -b <type>/<short-description>` off an up-to-date `master` (`feature/...`, `fix/...`, `chore/...`).
2. **Issue — judgment call, not a reflex**: open a GitHub issue first only for work that's genuinely non-trivial to scope (multi-part features, anything with open design questions, anything likely to span more than one session). For a small, well-understood change, skip the issue and go straight to the branch — filing one adds process without adding clarity.
3. **Implement** on the branch, following the architecture rules above. Verify before committing: compile/import-check changed Python, and for anything touching a template or route, boot the app and render the affected page(s) rather than trusting it will work.
4. **Commit** with a message that explains *why*, not just *what*.
5. **Push and open a PR** against `master` — always, even for small changes. Reference the issue number in the PR description when one exists.
6. **Migrations**: any schema change ships as its own Flask-Migrate revision in the same PR as the model change, chained onto the current head revision.

### Known constraint: this session's GitHub access

A Claude Code cloud session's GitHub access is governed by the Claude GitHub App installation, which does **not** always match what the repo owner's own GitHub permissions show:

- `gh api repos/<owner>/<repo> -q .permissions` reporting `push: true` is **not** proof that pushing will work — it reflects Kat's own GitHub permissions, not the App's granted scope. A session can have read-only repo access regardless of what that field says, and this has recurred across sessions even after reconnecting GitHub.
- The Issues REST endpoint and the GraphQL API both return 403 "Resource not accessible by integration" in this session — the App installation isn't granted Issues write scope. Don't spend time retrying `gh issue create` or GraphQL; go straight to the branch + PR.
- If `git push` is refused with a 403 naming the GitHub App, don't treat that as the task failing: create a git bundle of the feature branch's new commits (`git bundle create <name>.bundle <branch> ^origin/master`) and deliver it so it can be pushed from a machine with real access. This has reliably recovered delivery before — prefer it over `git format-patch` + `git am`, which can stall.
- Before attempting a push, always `git fetch origin master` and rebase/merge onto it first, so a working push sends a thin pack rather than re-uploading the whole tree.

If PR creation is also blocked by the same scope gap, say so plainly and hand over the branch (or bundle) with a ready-to-use PR title and description instead of silently stopping.
