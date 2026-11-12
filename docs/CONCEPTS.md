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

- **Why n8n is already running after a reboot** (1.3, noticed at 1.6): two settings
  together. The Docker engine is a systemd service set to `enabled`, so Ubuntu starts it
  at boot. Then the engine restarts every container whose restart policy says so, and the
  compose file gives n8n `restart: unless-stopped`. Proof: the laptop booted at 16:08:43
  and n8n started ten seconds later with no command typed. The default policy is `no`,
  which is why containers in older projects needed `docker compose up` after every boot.
  "Unless stopped" means `docker compose stop` keeps it down across reboots, and `down`
  removes the container (the volume stays). The same two settings bring n8n back on the
  Oracle server after a crash or reboot. VS Code's Container Tools extension shows all
  of this: compose containers grouped by project, plain `docker run` ones apart.
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

### Shopify access

- **A Shopify "app" with no code** (1.5): in the Dev Dashboard an app is a registration,
  not a program. It holds an identity (client ID and secret), permissions (scopes) and an
  install record (the store owner approved those scopes on this store). Nothing runs on
  Shopify. The code that uses it is ours: `curl` on the laptop now, n8n in phase 1, the
  Rails agents later. Shopify also uses it the other way round, signing webhooks with the
  app's secret. The App Store apps built before were different: they had a page inside
  the admin and needed hosting, which is why this one's app URL is just a placeholder.
- **Client credentials grant** (1.5): the app proves who it is with its client ID and
  secret and gets an Admin API token back, with no user, no browser and no redirect. It
  only works for stores in the app's own Dev Dashboard organization. The token lasts 24
  hours and there is no refresh token, because asking again with the ID and secret *is*
  the refresh. So the ID and secret are the real secrets; a token is short-lived and
  cheap to replace. The surprise: the product_geo_agent notes from earlier in 2026
  describe a manual OAuth dance (redirect to example.com, copy a code from the URL bar,
  swap it for a token) that this replaces entirely.
- **Scopes match the data model** (1.5): stock is not on the product. A product has
  variants, each variant has an inventory item, and the inventory item has a quantity per
  location. So reading stock needs `read_inventory`, and naming the product in an alert
  needs `read_products`. The webhook at 1.7 only carries the inventory item ID, which is
  why the query asks for `inventoryItem { id }`.

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

- **Domain, DNS, nameservers and a tunnel** (1.6): four pieces that together give n8n a
  public address. The *domain* (`mjesar.dpdns.org`) is a name you hold; it came free from
  DigitalPlat and lasts a year at a time. *DNS* is the internet's phone book: when Shopify
  wants `hooks.mjesar.dpdns.org`, it asks "where is that?". The *nameservers* are whoever
  answers that question for your domain. They were DigitalPlat's; switching them to
  `nataly` and `nitin.ns.cloudflare.com` made Cloudflare the one that answers, so Cloudflare
  can create `hooks.` and point it where it likes. The *tunnel* is where it points: a small
  program, `cloudflared`, runs next to n8n and opens a connection *out* to Cloudflare.
  Cloudflare receives Shopify's request at `hooks.mjesar.dpdns.org` and sends it back down
  that connection to n8n. Because the connection starts from our side, nothing on the
  laptop or server is opened to the internet, and the config decides which paths are let
  through (webhooks yes, the editor no). The domain decides the *address*; the machine
  running `cloudflared` decides *where it lands*: the laptop for now, the Oracle server
  from 1.14, with the same address throughout. The surprise: the free domain was the easy
  part; Cloudflare's dashboard wanted a card to create the tunnel, so it is made from the
  command line instead.

- **A named tunnel is set up in pieces, unlike ngrok** (1.6): `ngrok http --url=x 3000`
  packs the account, the tunnel, the address, the destination and running it into one
  line. Cloudflare splits them: `login` (the account), `create` (an empty tunnel with an
  ID, stored at Cloudflare), `route dns` (a CNAME from `hooks.` to
  `<id>.cfargotunnel.com`), `config.yml` (where requests land, with rules per path), and
  `tunnel run` (the only part that is "running"; `tunnel list` shows connections only
  then). The name `store-ai-crew` is just a label for the ID. Because the address belongs
  to the tunnel and not to a machine, it does not change when the laptop restarts or the
  tunnel moves to the server. Running, it holds four connections at once (two to
  Karachi, two to Singapore), so one can drop without the address going down.

- **Three keys with different powers** (1.6): `cert.pem`, from `login`, is account level:
  it can create, delete and route tunnels, so it stays on the laptop and never goes to a
  server. The `.json` file, from `create`, can only run this one tunnel. The token, from
  `tunnel token`, is the same secret as the `.json` written as one line; it sits in
  `.env` and is what the container uses (D19), because the container runs as its own
  non-root user and cannot read a file only the user who created it can read. A leaked token means delete
  and recreate the tunnel; a leaked `cert.pem` means revoke it and log in again. Path rules
  were proven by two different 404s: `/signin` gets an empty 404 from the tunnel's
  catch-all (n8n never sees it), while `/webhook/unknown` gets n8n's own "not registered"
  404, so webhook paths do reach n8n.

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
