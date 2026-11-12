# Documentation index

Everything that explains how this project is built and why. Start with the plan, then open
the page for the current phase.

| Page | What it is for |
| --- | --- |
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | The whole project: purpose, scope test, example scenario, architecture, stack, the four phases, extras. |
| [phases/01-backbone.md](phases/01-backbone.md) | Phase 1 step by step: server, n8n, Shopify webhook, Slack alert. Checklist, decisions, what broke, proof. |
| [DECISIONS.md](DECISIONS.md) | Every decision with its reason, the open questions, and the facts still to confirm. |
| [SECURITY.md](SECURITY.md) | What faces the internet and what does not, and each security measure with the step that builds it. |
| [CONCEPTS.md](CONCEPTS.md) | Learning notes, one per idea, written when the idea is first met. |

Pages for phases 2 to 4 are added when each phase starts.

## Picking the project back up

1. Open the current phase's page (see the Status line at its top) and find the first
   unticked step.
2. Check [DECISIONS.md](DECISIONS.md) for an open question tied to that step.

## Conventions

- **One page per phase** in `phases/`, named `NN-short-topic.md`. Each has the same parts:
  status, goal, steps with a "done when" check, decisions, what broke, and proof.
- **Facts only.** Numbers come from a real run. Anything not yet checked is marked
  "confirm" and listed in DECISIONS.md.
- **The repo is the source of truth.** If a page and the running system disagree, fix the
  page.
- **Written for a stranger.** Three readers: someone learning to build the same thing, a
  reviewer or hiring manager judging the work, and the author months later. Every
  sentence should help one of them. Decisions with reasons, what broke, real proof and
  concepts go in; personal circumstances and session chatter stay out. No shorthand
  that only makes sense with the chat history.
