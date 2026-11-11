# Decisions and open questions

Every decision that shaped the project, with the reason, so a later reader (or a later me)
can tell whether the reason still holds. Open questions live here until they are answered,
then move up into the decisions table.

## Decisions

| # | Date | Decision | Why |
| --- | --- | --- | --- |
| D1 | 2026-11-11 | One purpose: stop a store from losing sales the owner never sees. A workflow is in scope only if it serves that. | Ideas kept arriving during planning. Without a test, the project becomes a pile of unrelated automations with no story. |
| D2 | 2026-11-11 | Four phases: backbone, ops agent, AI mystery shopper, proof page. Each ends showable, with a post. | A long project with nothing to show until the end tends to stall. Each phase is a finished thing on its own. |
| D3 | 2026-11-11 | Phase 1 has no AI. | The trigger, duplicate protection, retries and approval path have to be trusted before an agent depends on them. It also makes the phase 1 post about webhooks, which stands alone. |
| D4 | 2026-11-11 | n8n is the backbone, Rails agents do the thinking. | Scheduling, retries and waiting days for a human are solved in a workflow tool. Agent logic needs tests and evals, which is easier in code. |
| D5 | 2026-11-11 | Nothing is written to the store or sent outside without the owner's approval. | An agent that drafts is useful on day one. An agent that acts alone has to earn it with numbers, which is what phase 4 produces. |
| D6 | 2026-11-11 | Code does the math, the model writes the words. | Models are unreliable at arithmetic. Thresholds, sales speed and pass rates are computed and passed in. |
| D7 | 2026-11-11 | Free tiers only. | It is a learning and portfolio project. It also means a reader can run all of it at no cost. |
| D8 | 2026-11-11 (revised same day) | Build phase 1 locally with Docker Compose, then rehearse the server on a Multipass VM, then run it on Oracle Cloud. | First plan was the VM from the start. Changed because n8n and webhooks are learned the same way locally, with one less layer and less memory. The VM is kept as a rehearsal right before Oracle, where server mistakes such as an SSH lockout are free, and as the target for the first Kamal deploy in phase 2. It is also the fallback if Oracle has no free capacity. |
| D9 | 2026-11-11 (replaced by D16) | Telegram for alerts and approvals. | Free, on the phone, and supports buttons. Slack was the alternative and can be added later. |
| D10 | 2026-11-11 | Learning mode: Mohammad writes all code and config, guided one step at a time. | The point is to be able to explain and rebuild every part. |
| D11 | 2026-11-11 | n8n workflows are exported as JSON and committed. | Otherwise the real work lives only in n8n's database and the repo shows nothing. |
| D13 | 2026-11-11 | Latest stable version of everything, looked up at install time and pinned exactly. Newest LTS for Ubuntu. | Mohammad's choice: learn current tools, not outdated ones. Pinning keeps rebuilds identical, so an upgrade is a deliberate step. |
| D14 | 2026-11-11 | Almost nothing faces the internet: only the webhook path, through Cloudflare Tunnel. Editor and SSH over Tailscale only. | The editor holds every credential. See [SECURITY.md](SECURITY.md). |
| D15 | 2026-11-11 (channel order updated by D16) | Telegram first. Other channels (WhatsApp, Slack, Teams) are extras after phase 4. Every workflow keeps the owner channel as its last step, so adding a channel means swapping one node, not redesigning. | Compared Telegram, Slack, Discord, WhatsApp, email, SMS, push apps and Teams. Telegram is free, needs no business verification and has approval buttons, so time goes into learning n8n, not platform setup. WhatsApp is what real store owners use, so it is the most valuable extra. |
| D16 | 2026-11-11 | Slack is the owner channel for phases 1 and 2. Teams, Telegram (from the server outside Pakistan) and WhatsApp are extras. | Telegram's bot API is blocked from Pakistan (PTA-directed, on major providers), and Mohammad ruled out VPN software. Slack needs no workaround, is free, has approval buttons, and is what small businesses and freelance n8n clients use, so it is the stronger portfolio choice. Teams fits corporate clients but needs a Microsoft 365 setup, so it comes later as a second channel. The bot `@mjesar_store_crew_bot` is kept for the Telegram extra. |
| D17 | 2026-11-12 | Shopify access through a new Dev Dashboard app, `Store AI Crew`, with custom distribution and only `read_products,read_inventory`. Tokens come from the client credentials grant. Admin API version `2026-10` (latest stable on 2026-11-12). | Since 2026-01-01 apps can no longer be created in the store admin; Dev Dashboard apps acting on stores in their own organization use the client credentials grant (client ID and secret in, token out, no redirect). A new app instead of reusing product_geo_agent's: that token only has Storefront scopes, a separate app keeps each project's secret and scopes separate, and this app's secret signs the webhooks checked at 1.8. Custom, not public: it only acts on one store, and public distribution cannot be undone. Write scopes come in phase 2 (SECURITY.md). |
| D12 | 2026-11-11 | Competitors for the mystery shopper idea were not researched. | This is for portfolio and learning, so whether a product already exists does not change the plan. |

## Open questions

### Q1: where do the agents' store tools come from? (needed at the start of phase 2)

The plan said "Rails agents use store tools through shop_mcp_server". Checked on
2026-11-11: shop_mcp_server's seven tools read its own seeded PostgreSQL store. It has no
Shopify connection and no webhook code. So the agents cannot reach the dev store through
it as it stands.

Options:

1. Add a Shopify-backed data source to shop_mcp_server, so the same tools read the real
   store. Most work, strongest reuse story.
2. Keep shop_mcp_server's database and fill it from Shopify webhooks through n8n. The
   agents read a local copy. Simple tools, but the copy can go stale.
3. Give the agents tools that call the Shopify Admin API directly, and keep
   shop_mcp_server only as the pattern they were modelled on.
4. Use an MCP endpoint Shopify itself provides, if one covers what the agents need.

Not decided. Phase 1 does not depend on it, because Shopify sends webhooks straight to n8n.

### Q2: where do reviews come from? (phase 2, bad-review workflow)

Shopify has no built-in product reviews. They come from a reviews app. To find out: which
free reviews app works on a dev store and can send a webhook or be polled. If none does,
seed reviews as store data (a metaobject, for example) and say so honestly in the README.

### Q3: which agent-facing tools does a dev store expose? (phase 3)

The mystery shoppers should use the store the way a real AI assistant would. To find out
at the start of phase 3: what a development store exposes for agents (storefront MCP
endpoint, catalog API, or neither), and whether ai_shop_assistant's approach still applies.

### Q4: where does the Rails app live? (phase 2)

Same repo as the n8n config (in a subfolder or at the root), or its own repo. Affects how
Kamal and Compose share one server.

### Q5: what public address do the webhooks use? (phase 1, step 1.6)

A free quick tunnel address changes on restart, which means re-registering the Shopify
webhook each time. A stable address needs a domain on Cloudflare. To decide: use an
existing domain, accept the changing address during phase 1, or use another free option
with a stable name.

### Q6: where does n8n remember handled events? (phase 1, step 1.9)

Duplicate protection needs somewhere to store event IDs. Options depend on what n8n
offers out of the box, to be explored at that step.

### Q7: do repeat low-stock alerts need suppressing in phase 1? (step 1.10)

Stock going 4, 3, 2 sends three alerts for one problem. Decide whether phase 1 accepts
that or remembers "already alerted for this product".

### Q8: which database, self-hosted or managed? (phase 2)

n8n uses SQLite by default: a single file inside its Docker volume. Phase 2 adds a Rails
app that needs PostgreSQL. To decide: run PostgreSQL as a container in the same compose
file with its own volume (free, backups are our job), or use a managed free tier (like
Heroku Postgres, backups are theirs). Also whether n8n moves from SQLite to the same
PostgreSQL (**confirm** what n8n's docs recommend for production).

### Q9: how does n8n get its Shopify token? (step 1.10)

Tokens from the client credentials grant last 24 hours and there is no refresh token: you
ask again with the client ID and secret. Options:

1. Each run starts with an HTTP Request node that asks for a fresh token, and the next
   node uses it. One extra call per run, never stale, easy to see in the execution log.
2. n8n's generic OAuth2 credential with the client credentials grant, which fetches and
   renews tokens by itself. **Confirm** whether n8n can send the token in Shopify's
   `X-Shopify-Access-Token` header (or Shopify accepts `Authorization: Bearer`).

Leaning to option 1. Either way it is automatic; nobody renews tokens by hand.

## Things to confirm against current documentation

Believed true from memory, not yet checked. Each gets checked at the step that uses it and
the answer recorded here with the date.

| What | Used at | Confirmed |
| --- | --- | --- |
| How a dev store app gets an Admin API token today | 1.5 | 2026-11-12, shopify.dev ("Authenticate an app for stores in your organization"): a Dev Dashboard app uses the client credentials grant, `POST https://{shop}.myshopify.com/admin/oauth/access_token` with `grant_type=client_credentials`, `client_id`, `client_secret`. Token valid 24 hours (`expires_in` 86399), no refresh token. Only for stores in the same Dev Dashboard organization (else `shop_not_permitted`); a dev store made from the Shopify admin is not in it. Scopes: `read_products,read_inventory`. Verified with a real call |
| Cloudflare Tunnel free terms, quick tunnel vs named tunnel | 1.6 | |
| Header name of Shopify's per-delivery webhook ID | 1.9 | |
| Shopify's webhook response time limit and retry policy | 1.11 | |
| n8n self-hosted licence terms for this use | 1.3 | |
| n8n's recommended image registry (`docker.n8n.io` vs Docker Hub) | 1.3 | Image 2.47.4 exists on both (checked 2026-11-11); which one the docs recommend not yet confirmed |
| Oracle Cloud Always Free machine sizes and limits | 1.14 | |
| Tailscale free plan limits | 1.13 | |
| Gemini and Groq free tier limits | Phase 2 | |
| How n8n sets the timezone for schedule triggers (containers run on UTC) | First schedule (daily brief, phase 2) | |
| Slack approval buttons in n8n, and how a paused run resumes | Phase 2 | |
| Slack free plan limits (message history, number of apps) | 1.4 | |
