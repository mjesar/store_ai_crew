# Concepts: learning notes

The ideas this project teaches, each written up in plain words when it is first met in a
real step. A heading with no note under it has not been reached yet.

The rule for a note: what it is, why it matters here, and the thing that was surprising or
went wrong. Notes come from doing the step, not from reading about it.

## Phase 1: Backbone

### Servers and containers

- **Virtual machine vs container** (step 1.13): a VM is a whole computer, a container is
  one program in a sealed box. Why the server rehearsal uses a VM with containers inside.

  A VM pretends to be a full computer: its own kernel, its own disk, its own network
  address, its own users. A container shares the kernel of the machine it runs on and
  only seals off one program and its files. So a VM is a flat in a building, with its own
  front door and its own locks; a container is a room inside a flat. The rehearsal needed
  the flat, because the things being practised (SSH, a firewall, updates that reboot the
  machine) belong to a whole computer, and a container cannot reboot or have its own
  firewall. Multipass makes one in a minute from Canonical's Ubuntu image, and
  `multipass delete --purge` throws it away, which is what made a full rebuild cheap
  enough to actually do. Inside, Docker runs the containers exactly as on the laptop.

- **Running a server** (1.13, 1.14): SSH keys, `apt`, `systemd`, logs, firewall.

  *SSH with a key.* SSH gives you a terminal on another machine. A key pair replaces the
  password: the private key never leaves the laptop, and the server keeps only the public
  half in `~/.ssh/authorized_keys`. Like a padlock you hand out: anyone may hold the open
  padlock (public key), only you hold the key that opens it (private key). The first
  connection shows the server's *host key fingerprint*, the server's own ID. SSH saves it,
  and if a different machine ever answers at that address it refuses loudly. On the
  rebuild the fingerprint was new (`4dZAlfRi...`, a new VM makes a new ID) and the same
  over both addresses, which is how you know the Tailscale address reaches the same VM.
  `sshd -T` prints the settings SSH really uses after reading every config file; for SSH
  the *first* value read wins, so the project's file is named `10-hardening.conf` to come
  before Ubuntu's `60-cloudimg-settings.conf`. Restarting SSH does not drop the session
  you are in, so the safe habit is: change, test with `sshd -t`, restart, then log in from
  a second terminal before closing the first.

  *Updates on their own.* `apt` is Ubuntu's package manager: `apt update` refreshes the
  list of what exists, `apt upgrade` installs it. `unattended-upgrades` does that every day
  for security fixes only, from Ubuntu's own sources and not Docker's, so Docker upgrades
  stay a choice. A new kernel only takes effect after a reboot, and by default nothing
  reboots, so the project's own file turns on a reboot at 04:00 when a fix needs it (D29).
  The test that matters: after `sudo reboot`, both containers were "Up" again with no one
  logged in, because systemd starts Docker at boot and Docker restarts every container
  marked `restart: unless-stopped`.

  *A firewall, and the trap Docker sets.* `ufw` is Ubuntu's simple firewall. The rule is
  "deny everything coming in, allow everything going out, except SSH arriving on the
  Tailscale interface" (D30). Going out stays open because the tunnel, Slack, Shopify,
  updates and Tailscale all work by the server calling out. Two surprises. First,
  `ufw enable` asks "Proceed? (y|n)" and, when commands are pasted together, reads the
  next pasted line as the answer and cancels, leaving the firewall off; it has to be
  typed alone. Second, the Docker port trap: a port published as `5678:5678` opens on
  every address, and Docker writes its own firewall rules that are checked before ufw's.
  Seen on purpose: with ufw active and no rule for 5678, the editor still answered from
  the laptop. The fix is in the compose file, not the firewall: publish on `127.0.0.1`
  only, so the port exists inside the server and nowhere else. A test of a firewall must
  run from outside: run on the server itself, the VM connected to itself, which no
  firewall filters, and the result looked like a failure but proved nothing.
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

  *Each container gets only what it uses* (1.13, D31). `env_file: .env` copies every value
  in the file into the container. Compose's `environment:` list with `${NAME}` still reads
  `.env`, but passes in only the names listed. n8n needed four of nine; the Shopify secret
  and the tunnel token had been sitting inside it for no reason. n8n blocks `$env` in nodes
  by default since 2.0 (found by reading its code, because two of its doc pages disagree),
  but a secret that is not in the container cannot leak by any route, blocked or not. The
  change needed `docker compose up -d`, not `restart`: a container's environment is fixed
  when it is created, and a restart reuses the same container.

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
- **Branches, and where a run ends** (1.10): an If node sends each item out of its
  **true** or its **false** output. An output with nothing connected is a quiet stop: the
  item goes nowhere and the run ends as a success. That is how a stock change above the
  threshold "sends nothing" without any extra node.
- **Expressions and `$('Node name')`** (1.10): a field in Expression mode is plain text
  except what sits inside `{{ }}`, which is JavaScript evaluated on every run. `$json` is
  the item that came into *this* node, which changes as the item moves along: after
  `Get Shopify token`, `$json` is the token reply, not the webhook. To reach an earlier
  node's data, name it: `$('Shopify inventory webhook').item.json.body.inventory_item_id`.
  That is why node names are worth choosing well; they are part of the code. Renaming a
  node rewrites the expressions that point at it.
- **Saved is not published** (1.10): saving changes the draft in the editor. The
  production webhook URL always runs the **published** version, so a real Shopify
  delivery ignores unpublished work.
- **Cheap checks first** (1.10): order a workflow so that steps that cost nothing (the
  signature, the duplicate check, the threshold) come before steps that call another
  service. Most stock changes stop at the threshold and never touch Shopify's API, runs
  that stop early answer in milliseconds, and a forged request can never make the
  workflow use a secret.
- **Locking a credential to one host** (1.10): n8n credentials have "Allowed HTTP Request
  Domains". Set to the store's exact host, n8n refuses to attach the client secret to a
  request anywhere else, so a typo in a URL cannot leak it.
- **Trigger nodes** (1.4, 1.7): manual, webhook, schedule.
- **Test URL vs production URL** (1.7): why a webhook node has two addresses.
- **Retries, and what they cannot fix** (1.11): a node's Settings tab has **Retry On
  Fail** (here 3 tries, 2 s apart). Most failures calling another service are brief (a
  dropped connection, a 502), and a second try a moment later works. A wrong setting
  fails the same way every time, so retries only delay it: the broken credential in the
  test failed three times in 4.05 s, then the run failed. Retries belong only on nodes
  that call something outside n8n; repeating an If node gives the same answer. Retrying
  an action that may have half-worked can repeat it (Slack posts, the reply is lost, the
  retry posts again), so it suits actions where a repeat is harmless.
- **HTTP 200 is not success** (1.11): n8n marks an HTTP node red only on an error
  status. GraphQL answers 200 even when the query fails and puts the problem in an
  `errors` array, and a lookup that finds nothing returns `null` with no error at all.
  So the result has to be checked in the workflow (`Product found?`), and a bad result
  turned into a real failure with a Stop and Error node. Otherwise the run is green, the
  error workflow never hears of it, and the owner gets an alert with blanks in it.
- **Error workflows** (1.11): a workflow can name another as its **error workflow**
  (workflow Settings). When a production run of the first fails, n8n starts the second
  with an **Error Trigger** and hands it the workflow name, the last node run, the error
  message and a link to the run. Here it posts those to Slack, so a failure reaches the
  phone instead of waiting in the Executions list. It does not fire for runs started by
  hand in the editor. n8n hides credential values in the error data (`**hidden**`), so
  the alert cannot leak a secret. The run link is built from `N8N_EDITOR_BASE_URL`,
  falling back to the webhook URL when it is unset.
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
- **A token per run** (1.10): with no refresh token, the simplest safe pattern is to ask
  for a new token right before the call that needs it, use it once and let it expire.
  There is nothing to store between runs and nothing that goes stale. The client ID and
  secret stay in an n8n credential, and the token itself is short-lived and read only.
- **GraphQL from n8n** (1.10): a GraphQL call is always a `POST` with a JSON body of two
  keys, `query` and `variables`. Values go in as variables (`$id: ID!`), not pasted into
  the query text, the same idea as parameterized SQL: Shopify checks the type, and data
  from a webhook cannot change the shape of the query. Shopify's GraphQL IDs name the
  type (`gid://shopify/InventoryItem/48683436081313`), while webhooks and admin URLs use
  the bare number, which GraphQL also returns as `legacyResourceId`. Every query has a
  cost in points from a bucket that refills each second (`extensions.cost`); this lookup
  costs 3 of 20,000. And a bad query still answers HTTP 200, with the problem in an
  `errors` array, so "the node is green" does not mean "the data is there".

### Webhooks

- **What a webhook is** (1.7): the store calls you, you do not ask the store.
- **Why a public HTTPS address is needed, and what a tunnel does** (1.6).
- **Signature verification (HMAC)** (1.8): proving who sent a request, and why it must be
  computed over the raw body.

  The webhook address is public, so anyone can post to it. Shopify and the app share one
  secret (the app's client secret). For each delivery Shopify runs HMAC-SHA256 over the
  body with that secret and sends the result, Base64-encoded, in the
  `X-Shopify-Hmac-Sha256` header. The receiver runs the same function over the body it
  got, with its copy of the secret, and compares. Without the secret nobody can produce
  a matching value, and changing a single byte of the body changes the whole result. So
  a match proves two things: the sender knew the secret, and the body was not altered.

  A plain hash (SHA-256 alone) would prove nothing, because anyone can compute it. The
  secret is what turns a checksum into a signature.

  It must be the raw body: the exact bytes that arrived. Parsing the JSON and turning it
  back into text can change spacing, key order or how characters are escaped, and then
  the HMAC no longer matches even though the data is the same. In n8n that is the
  Webhook node's **Raw Body** option.

  Two smaller points: compare case-sensitively (Base64 uses both cases), and a missing
  header must count as a failure, not be skipped.
- **At-least-once delivery and idempotency** (1.9): why the same event can arrive twice,
  and how to make handling it twice harmless.

  A sender only knows a delivery worked when it gets the reply. If the reply is lost or
  late (a timeout, a dropped connection), the sender cannot tell "never arrived" from
  "arrived, but the answer got lost", so it sends again. Shopify chooses to resend: a
  missed event is worse than a repeated one. That is **at-least-once** delivery. Exactly
  once is not something a sender can promise over a network, so the receiver has to make
  a repeat harmless.

  Handling something twice with the same effect as once is called **idempotency**. Two
  ways to get it:
  1. Make the action itself safe to repeat ("set stock to 2" is; "send a Slack message"
     is not).
  2. Remember what was already handled and skip repeats. That needs an ID that stays the
     same on every resend. Shopify sends one per delivery in `X-Shopify-Webhook-Id`.

  An alert cannot be made repeat-safe, so this project uses the second way: n8n's Remove
  Duplicates node keeps the IDs it has seen and drops an item whose ID is already known.
  Two details matter. The memory has to outlive a restart, or a retry arriving after one
  gets through (tested: it does survive). And the check comes after the signature check,
  so only IDs Shopify really sent are remembered.

  A replay attack is the same thing done on purpose: someone captures a real signed
  request and sends it again. The signature still matches, because the body is unchanged,
  so a signature check alone does not stop it. The duplicate check does, as long as the
  ID is still in the history.
- **Answer fast, work later** (1.11): Shopify waits at most 5 seconds for a reply (1
  second to connect), treats anything but a 2xx as a failure, retries 8 times over 4
  hours, and then deletes a subscription made through the Admin API. So the Webhook node
  replies at once (Respond Immediately) and the slow steps run after. The other side of
  that choice: once Shopify has its 200 it considers the delivery done, so any failure
  later in the run is the workflow's own problem to retry and report (D25).
- **Thin payloads** (1.7, 1.10): the event says what changed, not everything about it.

  The first real `inventory_levels/update` delivery (1.7) carried five fields: an
  inventory item ID, a location ID, the new `available` quantity, a timestamp and a
  GraphQL ID. No product title, no variant, no price. In Shopify, stock belongs to an
  *inventory item* (one per variant) at a *location*, not to the product, so the event
  describes exactly that. An alert needs the product's name, so the workflow has to look
  it up through the Admin API from the inventory item ID (1.10). Thin payloads keep
  deliveries small and fast, and avoid sending stale copies of data: the receiver fetches
  the current state when it needs it.

- **Test URL vs production URL, in practice** (1.7): the editor's "Execute workflow" waits
  on `/webhook-test/` for one call, which the tunnel does not forward. Shopify calls the
  production URL `/webhook/...`, which only answers once the workflow is published, and
  each call appears in the workflow's Executions tab, not on the editor canvas.

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

  Tailscale puts your own devices on one private network (a *tailnet*), wherever they
  are. Each gets a `100.x.x.x` address that only the other members can reach. Tailscale's
  servers keep the member list and hand out keys; the traffic itself goes straight between
  the devices, encrypted with WireGuard, so Tailscale cannot read it. For this project it
  means the server needs no open door on the internet for SSH: the firewall allows SSH
  only on the `tailscale0` interface, and from anywhere else the server does not answer at
  all, so a connection just times out. A server's login to the tailnet expires after 180
  days by default; on a server reachable only over Tailscale that would be a silent
  lockout, so key expiry is turned off for the server alone. A rebuilt server is a new
  device: it gets a new address, and the old entry has to be removed first or the new one
  joins as `store-ai-crew-1`.

- **An SSH tunnel to a private editor** (1.13): the n8n editor listens on `127.0.0.1:5678`
  inside the server, which nothing outside can reach. `ssh -N -L 5680:localhost:5678
  ubuntu@<tailscale-ip>` builds a pipe: whatever the laptop sends to its own port 5680
  comes out at port 5678 inside the server. `-N` means "no shell, only the pipe", so the
  terminal looks frozen while it works. The browser opens `127.0.0.1:5680`, not
  `localhost:5680`, because n8n's login cookie belongs to a host name and not a port, so a
  second n8n on `localhost` would log the first one out.

- **Public in, private admin** (1.13): only the webhook path faces the internet.

  The server has exactly two ways in, and they are separate on purpose. Shopify's
  webhooks come through Cloudflare and the tunnel, which `cloudflared` opened from the
  inside, and only `/webhook/` and `/healthz` are let through. Everything an owner does
  (SSH, the editor) comes over Tailscale, which only the owner's devices can join.
  Nothing listens on a public address at all. So the public road cannot reach the admin
  tools, and the admin road is invisible to the public. The picture of both roads is at
  the top of [SERVER_SETUP.md](SERVER_SETUP.md).

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
