# Agent instructions

This repo is a Claude plugin marketplace with one plugin, `dashboard-finanze`, which holds one Agent Skill of the same name. People add the repo once (claude.ai *Customize > Plugins > Add marketplace*, or `/plugin marketplace add` in Claude Code) and receive each new release. Free-plan users upload the zip from GitHub Releases instead.

## Layout

- `.claude-plugin/marketplace.json`: the catalog. One entry, `source: "./"`, so the repo root is also the plugin root.
- `.claude-plugin/plugin.json`: the plugin manifest. The **only** place the version lives.
- `skills/dashboard-finanze/`: the skill. `SKILL.md` is the router; the details are in `references/`, the code in `scripts/`, the starter files in `templates/`, the invented demo in `examples/demo/`.
- `tools/`: maintainer scripts. Not part of the skill.
- `README.md` is for readers, in Italian. Everything else is in English.

## Rules

- **Never commit real financial data.** No real statements, ledgers, balances or names. The demo is invented, and screenshots and reels use only the demo.
- The skill is written in English and speaks the person's language. It names capabilities ("your question tool", "the Artifact tool") and must work for anyone: one person or a household, a student or a freelancer.
- `tools/test-demo.sh` must pass before every release. It runs the demo end to end and fails unless every month reconciles.
- Never change `name` in either manifest: it is the install id and breaks every existing install. To change the label people see, set `displayName` in `plugin.json`.
- Don't add `version` to the marketplace entry, and don't add a top-level `bin/` folder (claude.ai rejects it).

## Releasing

Users get a change only when `version` in `plugin.json` changes. Pushing to `main` without a new version reaches nobody.

1. Commit the changes.
2. Add a `## X.Y.Z (date)` section at the top of `CHANGELOG.md`: what changed, in a line each.
3. Run `tools/release.sh X.Y.Z`. It sets the version, validates the manifests, runs the demo, builds the zip, commits and tags.
4. `git push origin main --tags`. The Release workflow tests again, builds `dashboard-finanze.zip` and attaches it to a GitHub release. The guide links to `releases/latest/download/dashboard-finanze.zip`, so the link never changes.

Semver: a fix is a patch, a new section or importer is a minor, a change to the ledger layout that old ledgers can't follow is a major (and the skill must say how to migrate).

## Testing a change locally

- Demo: `pip install beancount`, then `tools/test-demo.sh` (or `tools/test-demo.sh /tmp/demo` to keep the output and open `finanze-demo.html`).
- Plugin: `claude plugin validate .`, then `claude --plugin-dir .` to load it in a session.
- Zip: `tools/build-zip.sh`, then upload `dist/dashboard-finanze.zip` to a test account.
