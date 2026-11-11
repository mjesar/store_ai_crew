# store_ai_crew

**An AI team that finds where a Shopify store is quietly losing sales, drafts the fix, and
waits for the owner's approval.**

> Status: early. Phase 1 of 4 is in progress and nothing here runs yet. This README is the
> plan, and it gets replaced with real results as each phase is finished.

## The problem

A small store has no operations team. A product sells out at midnight and stays sold out
for three days. A one-star review sits unanswered where every visitor can read it. An AI
shopping assistant is asked for a waterproof jacket and cannot find the one the store
sells, because the size and returns details are missing.

None of these show up as an error. They are sales the owner never knew were lost.

## The idea

A small crew of AI agents watches for those moments. Each one drafts a fix: a reorder
email, a reply to the review, a corrected product description. Then it stops and asks. The
owner gets a message on their phone and taps Approve or Reject. Nothing changes in the
store without that tap.

Two parts do the work:

- **[n8n](https://n8n.io)** is the backbone. It listens for store events, makes sure each
  one is handled once, retries what fails, waits for the owner and carries out the
  approved action.
- **Ruby on Rails agents** do the thinking: read the store data, work out what matters and
  write the draft.

## Roadmap

| Phase | What it adds | Status |
| --- | --- | --- |
| 1. Backbone | Self-hosted n8n, Shopify webhooks, Slack alerts, one low-stock workflow. No AI yet. | In progress |
| 2. Ops agent | An agent drafts a supplier reorder or a review reply, the owner approves from the phone. | Planned |
| 3. AI mystery shopper | AI shoppers test the store every night, a second agent drafts fixes, the same shoppers run again to prove the fix. | Planned |
| 4. Proof page | Pass rate over time, cost per run, traces, and two models compared. | Planned |

Phase 1 has no AI on purpose. The part that receives events, avoids duplicates and
recovers from failures has to be trusted before an agent depends on it.

## Built on free tiers

Shopify development store, self-hosted n8n, a free Slack workspace, a free LLM tier, a local
virtual machine and then a free cloud machine. The aim is that anyone can run all of it at
no cost.

## Learn more

- [Project plan](docs/PROJECT_PLAN.md): purpose, architecture, stack and all four phases
- [Phase 1 step by step](docs/phases/01-backbone.md)
- [Decisions and open questions](docs/DECISIONS.md)
- [Concepts and learning notes](docs/CONCEPTS.md)

## Related projects

- [shop_mcp_server](https://github.com/mjesar/shop_mcp_server): a Rails MCP server that exposes a store to AI assistants
- [ai_shop_assistant](https://github.com/mjesar/ai_shop_assistant): an AI shopping assistant with tool calling over MCP
- [product_geo_agent](https://github.com/mjesar/product_geo_agent): an agent that scores how discoverable a Shopify product is to AI

This is a learning project, built step by step and documented as it goes.
