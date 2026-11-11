# store_ai_crew: project plan

Last updated: 2026-11-11

## 1. Overview

store_ai_crew is an AI team for a small Shopify store. It finds where the store is quietly
losing sales, drafts the fix, and waits for the owner's approval before anything changes.

It is for store owners who have no operations team. Nobody is watching stock levels at
midnight, nobody reads every review the day it arrives, and nobody checks whether an AI
shopping assistant can even find the products. Each of those is a sale lost without the
owner ever seeing it.

**One purpose:** stop a store from losing sales the owner never sees.

**Scope test:** a workflow belongs in this project only if it serves that purpose. This
test is how features get rejected. Anything that fails it goes in the extras list
(section 8) and waits until phase 4 is done.

**What kind of project this is:** a portfolio and learning project. Mohammad writes all the
code and config. It is built in four phases, and each phase ends in something that can be
shown working, with a written post about what was learned.

**Why this project:**

- It covers the patterns that real automation work asks for: workflow automation, agents,
  human approval, retries, no duplicate runs, evals and cost control.
- It reuses three earlier projects instead of starting from zero (section 7).
- It gives the planned n8n freelance gig one real, running workflow to show as proof.
- Every workflow is its own article or post.

## 2. Example scenario

This is the low-stock workflow as it should work at the end of phase 2.

1. **Trigger:** a customer buys the last but two Merino Wool Scarves. Shopify sends an
   `inventory_levels/update` webhook to n8n.
2. **Check it is real:** n8n verifies the webhook signature and drops it if this exact
   event was already handled (Shopify can deliver the same event more than once).
3. **Decide if it matters:** stock is 2, the threshold is 5, so it continues. Above the
   threshold, the run ends here and costs nothing.
4. **Think:** n8n calls the ops agent. The agent looks up the product, checks how fast it
   has been selling, and works out how many days of stock are left.
5. **Draft:** the agent writes a reorder email to the supplier with a suggested quantity
   and its reasoning.
6. **Ask:** the owner gets a Telegram message: the product, days of stock left, the drafted
   email, and Approve / Reject buttons.
7. **Act:** on Approve, n8n sends the email. On Reject, nothing is sent. Either way the
   decision is logged.

In phase 1 this stops after step 3 with a plain Telegram alert. No AI is involved until
phase 2. That is on purpose: the plumbing has to be trustworthy before an agent sits on it.

## 3. Architecture

```
   Shopify dev store                              Owner's phone
   (webhooks, Admin API)                          (Telegram)
          |    ^                                    ^    |
  webhook |    | approved action           alert /  |    | Approve /
          v    |                           draft    |    v Reject
   +---------------------------------------------------------+
   |  n8n  (the backbone)                                    |
   |  triggers, schedules, signature check, no duplicates,   |
   |  retries, approvals, and carrying out the action        |
   +---------------------------------------------------------+
                         |   ^
          "think about   |   |  draft + reasoning
           this event"   v   |
   +---------------------------------------------------------+
   |  Rails agents  (from phase 2)                           |
   |  ops agent, mystery shoppers, diagnosis agent           |
   +---------------------------------------------------------+
                         |
                         v
                 store tools (MCP)          LLM (Gemini or Groq free tier)
```

Everything in the two boxes runs in Docker Compose. It is built locally on the laptop,
rehearsed on a Multipass virtual machine, then run on an Oracle Cloud Always Free machine.
The same compose file is used in all three places.

**The split, and why:**

- **n8n does the reliable, boring part.** When to run, whether this event was already
  handled, what to do if a step fails, waiting days for a human, and performing the final
  action. These are solved problems in a workflow tool and painful to rebuild by hand.
- **Rails agents do the thinking.** Reading context, using tools, drafting. This is code
  that needs tests and evals, which is awkward inside a visual workflow.
- **The owner decides.** No agent writes to the store or contacts anyone outside it without
  an approval. The agent drafts, n8n waits, the human approves, n8n acts.
- **Code does the math, the model writes the words.** Thresholds, sales speed and pass
  rates are computed in code. The model is not asked to do arithmetic.

## 4. Tech stack

| Area | Choice | Why |
| --- | --- | --- |
| Workflow engine | n8n, self-hosted in Docker | Free to self-host, common in automation job posts, visual runs are easy to demo |
| Store | Shopify development store | Free, real webhooks and Admin API |
| Owner channel | Telegram bot | Free, works from a phone, supports buttons for approvals |
| Agents | Ruby on Rails (phase 2 onward) | Main language, reuses earlier agent code |
| LLM | Gemini or Groq free tier | Free, both already used in earlier projects |
| Store tools | MCP, via shop_mcp_server or Shopify's own endpoints | See open question Q1 in [DECISIONS.md](DECISIONS.md) |
| Development | Docker Compose on the laptop | Already installed, fastest way to learn n8n and webhooks |
| Server rehearsal | Multipass VM (Ubuntu LTS) | Free, behaves like a real remote server, mistakes cost nothing |
| Server, cloud | Oracle Cloud Always Free | Free, always on |
| Deploy | Docker Compose for n8n, Kamal for the Rails app | Kamal is the Rails 8 default |
| Public URL for webhooks | Cloudflare Tunnel | Shopify needs an HTTPS address to call |
| Private access | Tailscale | SSH to the server without opening ports |

**Constraint: free tiers only.** Each tier's terms get checked at the step that first uses
it, and the result is written into [DECISIONS.md](DECISIONS.md). Nothing in this table has
been verified yet except what is marked done in the phase pages.

## 5. The four phases

Each phase has its own page in [phases/](phases/) once it starts. Phase 1 is planned in
detail. Later phases are outlines and get broken into steps when they begin, because what
phase 1 teaches will change them.

### Phase 1: Backbone (no AI)

**Goal:** stock drops on the dev store, and a Telegram alert arrives on the phone within
seconds, exactly once, even if Shopify sends the event twice or a step fails.

- Self-hosted server running n8n in Docker
- Shopify webhook reaching n8n over a public HTTPS address
- Signature check, duplicate protection, threshold check, product lookup
- Telegram alert, plus an alert when the workflow itself fails
- Workflow exported to the repo as JSON

**Showable:** a short recording of changing stock in Shopify admin and the alert arriving.
**Post:** what a webhook receiver has to get right before any AI is added.
**Steps:** [phases/01-backbone.md](phases/01-backbone.md)

### Phase 2: Ops agent

**Goal:** the alert becomes a drafted fix the owner approves from the phone.

- A Rails agent with store tools, called by n8n over HTTP
- Low stock: sales speed check, drafted supplier reorder, approve, send
- Bad review: read the review and its order, draft a reply plus a refund or discount
  suggestion, approve
- Approval flow in Telegram with buttons, and a log of every decision
- Daily 9 AM brief of what happened and what is waiting
- Rails app deployed with Kamal beside n8n

**Showable:** approving a drafted reorder from a phone.
**Post:** an agent that drafts and a human who decides.

To settle at the start of this phase: where the store tools come from (Q1), where reviews
come from since Shopify has no built-in reviews (Q2), and where the Rails app lives in the
repo (Q4).

### Phase 3: AI mystery shopper

**Goal:** find out where the store fails for AI shopping assistants, fix it, and prove the
fix worked.

1. A nightly n8n run sends shopper agents to the store. Each has a persona and a goal, for
   example "waterproof jacket under $100, needs it by Friday".
2. Each shopper uses the store through its agent-facing tools and logs where it got stuck:
   product not found, missing size information, unclear returns policy.
3. A second agent groups the failures and drafts fixes.
4. The owner approves in Telegram.
5. n8n writes the fix to Shopify.
6. The same shoppers run again. The pass rate shows whether the fix worked.

The shopper runs are the evals. The same run that finds the problem measures the fix.

**Showable:** "20 AI shoppers, 7 failed, here is why", then the same 20 after the fix.
**Post:** testing a store the way an AI assistant sees it.

To settle at the start: which agent-facing tools a Shopify development store exposes (Q3).

### Phase 4: Proof page

**Goal:** one public page that shows the system works, with numbers.

- Pass rate over time
- Cost per run
- Traces of real runs
- The same shopper set run on two models, compared

**Showable:** the page itself.
**Post:** what it costs and how often it is right.

## 6. Workflows

| # | Workflow | Phase | Serves the purpose by |
| --- | --- | --- | --- |
| 1 | Low stock | 1 (alert), 2 (drafted reorder) | Not running out of a product that is selling |
| 2 | Bad review | 2 | Answering an unhappy customer before others read it |
| 3 | Daily 9 AM brief | 2 | Making sure nothing waits unseen |
| 4 | AI mystery shopper | 3 | Fixing products AI assistants cannot find or explain |

## 7. What it reuses

| Project | What it gives this one | Caveat |
| --- | --- | --- |
| [shop_mcp_server](https://github.com/mjesar/shop_mcp_server) | The MCP server pattern and seven store tools | Its tools read its own seeded database, not Shopify. See Q1 |
| [ai_shop_assistant](https://github.com/mjesar/ai_shop_assistant) | A shopping agent with tool calling over MCP | Basis for the phase 3 shoppers |
| [product_geo_agent](https://github.com/mjesar/product_geo_agent) | Audit logic for how discoverable a product is to AI, and Shopify auth setup notes | Basis for the phase 3 diagnosis agent |

## 8. Extras, after phase 4

These came up during planning and fail the scope test, or serve the purpose only
indirectly. They are listed so they are not lost, and so they are not started early.

- **Risky-order flag:** flag a suspicious order before it ships.
- **Product copy claims checker:** on a `products/update` webhook, an agent checks the new
  text against the store's approved claims list, risky words, missing facts and brand
  voice. Flags go to a person, plus a random sample of unflagged copy. The same check can
  flag AI-discoverability gaps such as no FAQ or vague specs.
- **Experiment health monitor:** a daily run pulls A/B test numbers, Ruby computes split
  drift (sample ratio mismatch) and guardrail drops, and the model only writes the
  plain-language note. May become its own small project.
- **AI visibility watchdog:** a weekly run asks several AI assistants buyer questions and
  tracks which products get mentioned.
- **Bargain agent:** an agent negotiates price inside limits the owner sets, code enforces
  the floor, n8n creates the discount code.

## 9. How progress is tracked

- [phases/](phases/) has one page per phase with a step checklist, decisions, what broke
  and proof. That page is the place to look for "where are we".
- [DECISIONS.md](DECISIONS.md) records every decision with its reason, and every open
  question until it is answered.
- [CONCEPTS.md](CONCEPTS.md) holds the learning notes, written as each idea is met.
- `CLAUDE.md` at the repo root has one "Current status" line naming the current step.
