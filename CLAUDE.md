# store_ai_crew

An AI team that finds where a Shopify store is quietly losing sales, drafts the fix,
and waits for the owner's approval.

**Scope test:** a workflow belongs here only if it serves that one purpose (stop a
store from losing sales the owner never sees). Anything else is an extra for after
phase 4.

## Mode: learning project

This is a portfolio and learning project. The learning-project rules in the global
`CLAUDE.md` apply in full:

- Mohammad writes all code and config (compose files, n8n workflows, Rails code,
  specs, deploy config). Claude describes what is needed and why, shows at most a
  2 to 5 line reference snippet for unfamiliar syntax, then reviews what was written.
- One small piece at a time. Pause after each piece so it can be run and questioned.
- Claude may write and maintain docs (`README.md`, `docs/`, this file).

## Phases

Each phase ends in something showable, with a post.

1. **Backbone (no AI):** self-hosted server, n8n, Shopify webhooks, Slack alerts,
   one low-stock workflow.
2. **Ops agent:** drafts a supplier reorder or a bad-review reply, owner approves
   from the phone, n8n carries out the action.
3. **AI mystery shopper:** nightly shopper agents with a persona and a goal, a second
   agent groups failures and drafts fixes, owner approves, n8n writes the fix, the
   same shoppers run again.
4. **Proof page:** pass rate over time, cost per run, traces, two-model comparison.

Extras after phase 4: risky-order flag, product copy claims checker.

## Architecture (intended)

- **n8n** is the backbone: triggers, schedules, retries, no duplicate runs, approvals,
  and carrying out the approved action.
- **Rails agents** do the thinking, using store tools through `shop_mcp_server`
  (from phase 2).
- **The owner** approves in Slack (D16; Telegram is blocked from Pakistan, so it is a
  later extra from the server).
- **Hosting:** built locally with Docker Compose, rehearsed on a Multipass VM, then
  run on Oracle Cloud Always Free (D8).
  n8n self-hosted in Docker, Kamal for the Rails app, Tailscale for SSH,
  Cloudflare Tunnel so Shopify webhooks can reach n8n.

## Versions: latest stable, always (Mohammad, 2026-11-11)

Use the newest stable release of everything: Ruby, Rails, Docker, n8n, Ubuntu, gems,
images. Look the current version up at the step that installs it (release page or
registry), never from memory. For the server OS, stable means the newest Ubuntu LTS.
Pin the exact version that was installed (image tags, Gemfile.lock), never a floating
tag like `latest`, so a rebuild gives the same result. Record the versions used in the
phase page.

## Security

`docs/SECURITY.md` is the plan. Each measure names the step that builds it; do it at
that step.

## Constraints

- Free tiers only: Shopify dev store, self-hosted n8n, Gemini or Groq free tier,
  Slack free plan, Cloudflare Tunnel, Tailscale. Confirm each tier's current terms at
  the step that first uses it, not from memory.
- Secrets (Shopify tokens, Slack bot token, n8n encryption key) never go in git.
  Use an untracked `.env` and commit a `.env.example`.
- n8n workflows are exported to JSON and committed, so the repo is the source of
  truth and not the n8n database.

## Docs (read these at the start of a session)

- `docs/PROJECT_PLAN.md`: the whole plan, phases, architecture, extras.
- `docs/phases/NN-*.md`: the current phase's step checklist. The first unticked step
  is where to continue.
- `docs/DECISIONS.md`: decisions with reasons, open questions (Q1 to Q7), and facts
  still to confirm against current documentation.
- `docs/CONCEPTS.md`: learning notes, filled in when each idea is first met.

Keeping them current is part of every step:

- Tick the step in the phase page once its "done when" check passes.
- Record any decision in `DECISIONS.md` and move answered questions into the table.
- Add what broke and real proof to the phase page as it happens.
- Write the concept note after Mohammad has done the step, in plain words.
- Anything marked "confirm" must be checked against current docs at that step, never
  answered from memory.
- A README that follows the README playbook (hero, demo, real runs, Quick Start)
  comes at step 1.15, when there is something real to show.

## Known gap

`shop_mcp_server` reads its own seeded database, not Shopify (checked 2026-11-11).
Phase 2 must settle where the agents' store tools come from (Q1 in `DECISIONS.md`).

## Current status

Phase 1, step 1.4: first Slack message from n8n (switched from Telegram, D16). Paused
2026-11-11. Done: 1.1 to 1.3 (n8n 2.47.4 running locally on 127.0.0.1:5678); Slack
workspace `mjesar` created on the free plan (declined the Business+ trial); Slack app
`Store AI Crew` created from scratch ("Pick features") with only the bot scope
`chat:write`, no user scopes, no events, no app-level token; installed to the
workspace. Next: `/invite @Store AI Crew` in `#store-alerts`, copy the Channel ID,
create the n8n Slack credential (access token, pasted straight from Slack's OAuth &
Permissions page), build Manual Trigger then Slack "Send a message" by channel ID,
execute. Mohammad has no password manager yet: Bitwarden suggested, so the encryption
key in `.env` currently has no backup. Slack token goes into n8n's credential store,
not `.env` (env_file passes everything in `.env` into the container). Multipass comes
at 1.13. Update this line as steps complete.
