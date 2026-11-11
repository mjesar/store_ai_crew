# Concepts: learning notes

The ideas this project teaches, each written up in plain words when it is first met in a
real step. A heading with no note under it has not been reached yet.

The rule for a note: what it is, why it matters here, and the thing that was surprising or
went wrong. Notes come from doing the step, not from reading about it.

## Phase 1: Backbone

### Servers and containers

- **Virtual machine vs container** (step 1.13): a VM is a whole computer, a container is
  one program in a sealed box. Why the server rehearsal uses a VM with containers inside.
- **Running a server** (1.13, 1.14): SSH keys, `apt`, `systemd`, logs, firewall.
- **Docker Compose** (1.3): describing a running service in a file.

  An image (`registry/name:tag`) is the packaged program, and a container is one
  running copy of it. Nothing is installed on the laptop: `docker compose up` pulls the
  image the first time, then creates the network, the volume and the container.
  `docker compose config` checks the file and prints how Compose read it, including
  things it adds itself: the project name (taken from the folder, and used as a prefix,
  so `n8n_data` becomes `store_ai_crew_n8n_data`) and a private network the services
  share. `up -d` runs in the background (detached). `down` removes containers and the
  network but keeps named volumes. `down -v` also deletes the volumes, which is how you
  throw the data away on purpose. YAML structure is indentation: a key that is two
  spaces too shallow belongs to a different parent, which is what the error
  `volumes.ports must be a mapping` meant. The version was found with
  `npm view n8n dist-tags` (n8n uses the same numbers on npm and Docker) and checked with
  `docker manifest inspect`, which asks the registry if a tag exists without
  downloading it.
- **Volumes** (1.3): where a container's data lives when the container is replaced.

  A container is disposable, like a Heroku dyno: whatever it writes inside itself is
  gone when it is removed. A named volume is a folder Docker keeps on the host disk
  (`/var/lib/docker/volumes/store_ai_crew_n8n_data/_data`), plugged into the container
  at `/home/node/.n8n`. n8n's database there is SQLite, a whole database in one file
  (`database.sqlite`, plus `-wal` and `-shm` files holding changes not yet merged in).
  It plays the role Heroku Postgres played, except it sits on our own disk, so backups
  are our job. Code and setup travel through git; data does not travel at all, each
  machine has its own volume. Proof it works: a new container started on the old volume
  still had the owner account.
- **Environment files and secrets** (1.2): what goes in `.env`, what goes in git.

  Secrets live in `.env`, which git ignores. `.env.example` is committed with the same
  variable names and empty values, so a stranger (or a new server) knows what to fill
  in. The `.gitignore` also ignores `.env.*`, which catches copies like `.env.backup`,
  with one exception for `.env.example`. A secret that reaches a commit counts as
  leaked even if the file is deleted later, because git history keeps it.

  The n8n encryption key was made with
  `(umask 077; printf 'N8N_ENCRYPTION_KEY=%s\n' "$(openssl rand -hex 32)" > .env)`:

  - `openssl rand -hex 32` gives 32 bytes from the system's cryptographic random
    generator, written as 64 hex characters (256 bits). Generated, not invented,
    because people pick guessable patterns.
  - `"$(...)"` runs the command and pastes its output in place.
  - `> .env` writes to the file, so the key never shows on screen or in a log.
  - `umask 077` makes the new file readable by its owner only (permissions 600). The
    parentheses run it in a subshell, so the setting does not leak into the shell.
  - Never overwrite an existing key: n8n's saved credentials are encrypted with it,
    and a new key cannot read them. Keep a copy in a password manager.

  Why the key exists: n8n stores tokens (Slack, Shopify) in its database, encrypted
  with this key. The database alone is useless to a thief. The database plus the key
  gives everything, so they are kept apart.

### n8n

- **Workflow, node, execution** (1.4): the three words everything else builds on.
  - A **workflow** is the whole recipe, drawn as boxes joined by lines. `Slack test` is
    one.
  - A **node** is one box: one job. Every workflow starts with a **trigger node** (what
    makes it run: a click, a webhook, a schedule) followed by action nodes (send a
    Slack message, call an API). Data flows along the lines from one node to the next.
  - An **execution** is one run of a workflow. n8n records each one in the Executions
    tab: when it ran, whether it succeeded, and what data passed through every node.
    That log is the first place to look when something goes wrong.

- **Credentials** (1.4): how n8n holds a secret it needs to call another service.
  - The Slack bot token is saved once as a credential and nodes refer to it by name.
    The token never appears inside the workflow, so a workflow can be exported and
    shared (step 1.12) without leaking it.
  - n8n encrypts saved credentials with `N8N_ENCRYPTION_KEY` from `.env`. Lose the key
    and every saved credential has to be entered again.
  - The token is pasted straight from Slack into n8n and kept out of `.env`, because
    `env_file` hands everything in `.env` to the container as plain environment
    variables.

- **Two directions, two secrets** (1.4): the Slack credential has two fields.
  - The **access token** (`xoxb-...`) is for n8n calling Slack. It proves n8n may post
    as the bot.
  - The **signing secret** is for Slack calling n8n. Slack signs each request with it,
    and n8n checks the signature, so nobody can pretend to be Slack. It is left empty
    until phase 2, when the Approve button makes Slack call n8n. Same idea as the
    Shopify HMAC check at step 1.8.

- **Bot token scopes, fewest first** (1.4): the bot has only `chat:write`, so all it
  can do is post in channels it has been invited to. That is why the channel is given
  **by ID** in the Slack node: picking it from a list would need an extra read scope
  (`channels:read`). A stolen token with one scope can do little damage.
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
