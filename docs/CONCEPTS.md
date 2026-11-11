# Concepts: learning notes

The ideas this project teaches, each written up in plain words when it is first met in a
real step. A heading with no note under it has not been reached yet.

The rule for a note: what it is, why it matters here, and the thing that was surprising or
went wrong. Notes come from doing the step, not from reading about it.

## Phase 1: Backbone

### Servers and containers

- **Virtual machine vs container** (step 1.1): why the project uses a VM and runs
  containers inside it.
- **Docker Compose** (1.3): describing a running service in a file.
- **Volumes** (1.3): where a container's data lives when the container is replaced.
- **Environment files and secrets** (1.3): what goes in `.env`, what goes in git.

### n8n

- **Workflow, node, execution** (1.4): the three words everything else builds on.
- **Credentials and the encryption key** (1.3, 1.4): how n8n stores secrets, and what
  happens if the key is lost.
- **Trigger nodes** (1.4, 1.7): manual, webhook, schedule.
- **Test URL vs production URL** (1.7): why a webhook node has two addresses.
- **Error workflows and retries** (1.11).
- **Exporting workflows** (1.12): what is and is not in the JSON.

### Webhooks

- **What a webhook is** (1.7): the store calls you, you do not ask the store.
- **Why a public HTTPS address is needed, and what a tunnel does** (1.6).
- **Signature verification (HMAC)** (1.8): proving who sent a request, and why it must be
  computed over the raw body.
- **At-least-once delivery and idempotency** (1.9): why the same event can arrive twice,
  and how to make handling it twice harmless.
- **Answer fast, work later** (1.11): why the reply to Shopify comes before the slow steps.
- **Thin payloads** (1.7, 1.10): the event says what changed, not everything about it.

### Networking

- **Private network with Tailscale** (1.13): reaching a server without exposing it.
- **Public in, private admin**: only the webhook path faces the internet.

## Phase 2: Ops agent

- **Human in the loop**: a workflow that pauses for a person and resumes days later.
- **Calling an agent from a workflow**: what n8n sends, what the agent returns, timeouts.
- **Tools and MCP**: how an agent reads store data.
- **Code for math, model for words**: what to compute before the model sees it.
- **Kamal**: deploying the Rails app to the same server.
- **Decision log**: recording what was proposed, who approved it and what happened.

## Phase 3: AI mystery shopper

- **Personas and goals as test cases**.
- **Evals**: what counts as a pass, and why the same run finds problems and measures fixes.
- **Diagnosis agent**: grouping many failures into few causes.
- **Verify after fix**: rerunning the same cases.

## Phase 4: Proof page

- **Tracing**: recording every step of an agent run.
- **Cost per run**: tokens, calls and what a nightly run costs.
- **Comparing two models** on the same cases.
