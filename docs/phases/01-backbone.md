# Phase 1: Backbone (no AI)

**Status:** in progress, started 2026-11-11. Current step: 1.12.

**Environment:** parts A to E run locally on the laptop, part F on a server.

## Goal

Stock drops on the Shopify dev store, and a Slack alert arrives on the phone within
seconds, exactly once, even if Shopify sends the event twice or a step fails.

There is no AI in this phase. An agent is only as reliable as the thing that triggers it,
feeds it and acts on its output, so that part is built and trusted first.

## How to work through this page

Each step has a goal, what to build, and a "done when" check. Do them in order. Tick the
box when the check passes, then fill in the three sections at the bottom (decisions, what
broke, proof) as things happen, not at the end.

Anything marked **confirm** is something believed to be true but not yet checked against
current documentation. Check it at that step and note the answer in
[../DECISIONS.md](../DECISIONS.md).

## Starting point (checked 2026-11-11)

| On the laptop | State |
| --- | --- |
| OS | Ubuntu 26.04.1 LTS |
| Docker | 29.9.3, Compose v5.7.0 (upgraded to v5.7.1 in step 1.1) |
| Ruby, Node, Kamal | Installed |
| Multipass, Tailscale, cloudflared | Not installed (cloudflared CLI added in step 1.6 for tunnel setup; the running tunnel is a container, D18) |
| Port 5678 | Free |
| Resources | 8 cores, 14 GB RAM (about 6 GB free), 95 GB free disk, CPU virtualization on |

## Order of work

Parts A to E are built **locally on the laptop with Docker Compose**. That is where n8n,
webhooks and the workflow are learned, without a server in the way. Part F then
**rehearses the server on a Multipass VM**, where mistakes such as locking yourself out
cost nothing, and only then repeats it on **Oracle Cloud**. The compose file is the same
in all three places. See D8 in [../DECISIONS.md](../DECISIONS.md).

## Steps

### Part A: n8n running locally

- [x] **1.1 Confirm the local toolchain is current**
  - Goal: start on the latest stable Docker and Compose (rule D13).
  - Build: compare `docker version` and `docker compose version` with the latest stable
    releases on Docker's release notes. Upgrade if behind.
  - Done when: both are on the latest stable release, and the versions are written in the
    Proof table.

- [x] **1.2 Prepare the repo for secrets**
  - Goal: make it impossible to commit a secret by accident, before any secret exists.
  - Build: a `.gitignore` that ignores `.env`, and a `.env.example` listing variable
    names with no values. Generate a long random `N8N_ENCRYPTION_KEY` (for example with
    `openssl rand -hex 32`) into your real `.env`, and keep a copy in your password
    manager.
  - Why the key matters: n8n encrypts saved credentials with it. If it is lost or
    changes, every saved credential becomes unreadable. The server later needs the same
    key.
  - Done when: `git status` does not show `.env`, and `.env.example` is committed.

- [x] **1.3 Run n8n with Docker Compose**
  - Goal: n8n running locally, with its data surviving a restart.
  - Build: a `docker-compose.yml` with one n8n service: the image pinned to the latest
    stable n8n version (not `latest`), port 5678 bound to `127.0.0.1` only, a named
    volume for `/home/node/.n8n`, and `env_file: .env`. Look up the current version on
    n8n's release notes or Docker Hub.
  - Why `127.0.0.1`: without it, anyone on the same Wi-Fi can reach the editor.
  - Done when: the editor opens at `http://localhost:5678`, you create the owner account,
    run `docker compose down` then `up` again, and the account is still there.

### Part B: first workflow and the owner channel

- [x] **1.4 Send a Slack message from n8n** (done 2026-11-12)
  - Goal: prove the output side works before touching Shopify.
  - Changed from Telegram on 2026-11-11: Telegram's bot API is blocked from Pakistan
    (see "What broke" and D16).
  - Build: a free Slack workspace with an alerts channel and the Slack app on your
    phone. A Slack app (at api.slack.com/apps) with a bot token that may post messages,
    installed to the workspace and invited to the channel. A Slack credential in n8n,
    and a two-node workflow: Manual Trigger, then Slack "send message" to the channel.
  - **Confirm:** which bot token scopes n8n's Slack node needs to post (start with the
    fewest), and which credential type n8n recommends (bot token or OAuth2).
    Checked 2026-11-12: `chat:write` alone is enough to post when the channel is given
    by ID. The "Slack API" credential with the bot access token works; its Signature
    Secret field is left empty until phase 2 (incoming Slack requests).
  - Done when: clicking "Execute workflow" makes your phone buzz with a Slack
    notification, and the run appears in the execution log.
  - Learn here: nodes, credentials, executions and the execution log.

### Part C: Shopify talks to n8n

- [x] **1.5 Dev store, API access and test products**
  - Goal: a store to test against and a token n8n can use.
  - Build: a Shopify development store with a few products that track inventory, and an
    app with Admin API access to read products and inventory.
  - **Confirm:** how a dev store app gets an Admin API token today. The notes in
    `product_geo_agent/docs/shopify-auth-setup.md` cover this from an earlier project and
    are the starting point. Record which scopes were needed.
  - Done when: a `curl` call to the Admin API from the laptop returns your products.

- [x] **1.6 Give n8n a public HTTPS address** (done 2026-11-13)
  - Goal: Shopify's servers can reach n8n. A VM on a laptop is not reachable from the
    internet, and Shopify only calls HTTPS addresses.
  - Build: put the free domain `mjesar.dpdns.org` (DigitalPlat) on Cloudflare's free plan
    by pointing its nameservers at Cloudflare. Create a named tunnel from the CLI
    (`cloudflared tunnel login`, `create`, `route dns`), because the dashboard route needs
    Cloudflare Zero Trust, whose sign-up asks for a payment method even on the free plan.
    Run `cloudflared` as a compose service next to n8n, with the tunnel token from `.env`
    (D19) and a committed `cloudflared/config.yml` whose ingress rules let only n8n's
    webhook paths and `/healthz` through, with a 404 catch-all, so the editor is not on the
    internet. Set `N8N_WEBHOOK_URL` (and `N8N_PROXY_HOPS=1`) in `.env` so n8n shows the
    public address in its webhook nodes. `WEBHOOK_URL` is the older name, deprecated since
    n8n 2.35.
  - **Confirm:** the latest stable `cloudflare/cloudflared` image tag; Cloudflare's free
    plan terms for tunnels; that ingress rules can filter by path. All checked, see
    [../DECISIONS.md](../DECISIONS.md) and the Proof table.
  - Done when: opening `https://hooks.mjesar.dpdns.org/healthz` from a phone gets a reply
    from n8n, and the editor's address (`/signin`) gets a 404. The phone can be on the same
    Wi-Fi as the laptop: through a tunnel every request goes out to Cloudflare and back.
    Shopify's own call at 1.7 is the fully outside test.

- [x] **1.7 Receive the first webhook** (done 2026-11-13)
  - Goal: see a real Shopify event arrive.
  - Build: a new workflow starting with a Webhook node (POST). Register an
    `inventory_levels/update` webhook in Shopify pointing at it (D20: the
    `webhookSubscriptionCreate` mutation with `curl`). Change a product's stock in Shopify
    admin. Publish the workflow first and read the payload in its Executions tab: the
    tunnel only forwards production `/webhook/` paths, not `/webhook-test/`, and Shopify
    drops a subscription whose deliveries keep failing.
  - Done when: the execution log shows the payload. Read it closely: it carries an
    inventory item ID, a location ID and the available quantity. It does not carry the
    product title. That gap is step 1.10.

### Part D: making it trustworthy

- [x] **1.8 Verify the signature** (done 2026-11-14)
  - Goal: reject anything that did not come from Shopify. The address is public, so anyone
    who finds it can post to it.
  - Build: Shopify signs each webhook with an HMAC-SHA256 of the raw request body, using
    the app's secret, and sends it in the `X-Shopify-Hmac-Sha256` header. Compute the same
    value in n8n and compare. Stop the run if they differ.
  - Watch out: the signature is over the raw bytes of the body. If n8n parses the JSON
    first and you sign the re-serialized version, it will not match.
  - Done when: a real webhook passes, and a `curl` POST with a made-up body is rejected.
  - As built: Webhook node with the **Raw Body** option, so the exact bytes arrive as the
    binary property `data`. Then a Crypto node, action **Hmac**, Binary File on, property
    `data`, SHA256, Base64, secret from a Crypto credential (D21), result in
    `computedHmac`. Then an If node: `{{ $json.computedHmac }}` is equal to
    `{{ $json.headers['x-shopify-hmac-sha256'] }}`, strict types, case-sensitive (Base64
    is). True carries on (1.10); false goes to **Stop and Error** "Webhook signature
    mismatch", so a forged request shows as a failed execution. A missing header also
    lands on false.
  - Known limits: the caller still gets `200 {"message":"Workflow was started"}`, because
    the Webhook node answers before the check runs, so the rejection is visible in n8n,
    not to the sender (revisit with the reply timing at 1.11). The If node's comparison is
    not constant-time, unlike Shopify's examples; over the internet and through
    Cloudflare the timing difference is buried in network noise, so it is accepted here.

- [x] **1.9 Handle duplicates** (done 2026-11-16)
  - Goal: one stock change, one alert. Shopify promises to deliver each event at least
    once, which means sometimes twice.
  - Build: each delivery carries an ID in its headers (confirmed: `X-Shopify-Webhook-Id`).
    Remember handled IDs and end the run early on a repeat. Decide where to remember them.
  - Done when: replaying the same delivery twice sends one Slack message.
  - As built: on the If node's true branch, a **Remove Duplicates** node named
    `Skip repeat deliveries`, operation **Remove Items Processed in Previous
    Executions**, Keep Items Where **Value Is New**, value
    `{{ $json.headers['x-shopify-webhook-id'] }}` (n8n lowercases header names), scope
    Node, history size 10,000 (the default). A repeat leaves the node with no items, so
    the run ends there and nothing after it runs (D22).
  - Why after the signature check: an ID is only remembered once Shopify is known to have
    sent it. Placed first, anyone could post made-up IDs to the public URL and fill the
    history.
  - Tested by replaying a real delivery with `curl` (same raw body, same signature, same
    webhook ID): the replay passes the signature check and is discarded, also after
    restarting n8n. There is no Slack node yet; 1.10 adds it after this node, so a
    discarded repeat never reaches it.
  - Known limits: the history holds the last 10,000 IDs. Shopify retries a failed
    delivery 8 times over 4 hours, so a repeat would have to arrive after 10,000 newer
    deliveries to get through, which a single store will not reach in 4 hours. Whether
    runs from the editor's test URL share this history was not tested; Shopify only calls
    the production URL.

- [x] **1.10 Threshold, product lookup and the alert** (done 2026-11-18)
  - Goal: a useful message, only when it matters.
  - Build: an If node on the available quantity against a threshold. Below it, look up the
    product title and variant from the inventory item ID through the Admin API, then send
    a Slack message with product, quantity left and a link to it in Shopify admin.
  - Decide: where the threshold lives (one number for the store to start).
  - Think about: stock going 4 to 3 to 2 sends three alerts for one problem. Decide
    whether that is acceptable in phase 1 or needs a "already alerted" memory.
  - Done when: dropping stock below the threshold alerts once with the right product, and
    a change above the threshold sends nothing.
  - As built, after `Skip repeat deliveries`:
    1. **If** node `Below threshold?`: `{{ $json.body.available }}` Number "is less than"
       `5`. A Number comparison, because as strings `"10"` sorts before `"5"`. The
       threshold sits in the node: `$env` is to be blocked at 1.13, and n8n Variables are
       a paid feature. The false branch is left empty, so the run simply ends there.
    2. **HTTP Request** `Get Shopify token`: `POST` to
       `https://<store>.myshopify.com/admin/oauth/access_token`, with the client ID and
       secret coming from a **Custom Auth** credential (`{"body": {...}}`) that may only
       be sent to the store's host (D23).
    3. **HTTP Request** `Look up product`: `POST` to `/admin/api/2026-10/graphql.json`
       with header `X-Shopify-Access-Token: {{ $('Get Shopify token').item.json.access_token }}`
       and the query `inventoryItem(id: $id) { variant { title inventoryQuantity product
       { title legacyResourceId } } }`. The ID goes in as a GraphQL variable, built as
       `gid://shopify/InventoryItem/` plus the webhook's `inventory_item_id`.
    4. **Slack** `Send low stock alert`: Message → Send, channel by ID, "Include Link to
       Workflow" off (its link points at the private editor, D14). Text: product title,
       units left at this location, total across locations, and
       `<https://admin.shopify.com/store/<store>/products/<legacyResourceId>|Open in Shopify>`.
  - Why this order: everything up to the threshold runs inside n8n and costs nothing. The
    token and the lookup are the first calls out to Shopify, so they only happen for a
    delivery that will alert. A forged request never reaches them, so it cannot make n8n
    use the client secret.
  - Repeat alerts: every change below the threshold alerts (D24), so "alerts once" in the
    check above means once per stock change, with duplicates of the same delivery still
    dropped by 1.9.
  - Known limits: `available` is per location, while the alert also shows the variant's
    total (`inventoryQuantity`), so the threshold is checked per location. A GraphQL
    error comes back as HTTP 200 with an `errors` array, so `Look up product` stays green
    and the alert would show empty values (a job for 1.11). The token shows in saved
    execution data (D23). Products with no options show the variant title "Default
    Title", which the message leaves out.

- [x] **1.11 When things fail**
  - Goal: a failure is seen, not silent.
  - Build: reply to Shopify quickly, before the slow steps (**confirm** Shopify's response
    time limit and retry policy). Add retries on the nodes that call outside services. Add
    an error workflow that sends a Slack message when any run fails.
  - Done when: breaking the Shopify credential on purpose produces a failure alert on the
    phone, and fixing it recovers without a restart.

### Part E: keep it and show it

- [ ] **1.12 Workflows into the repo**
  - Goal: the repo is the source of truth. n8n stores workflows in its own database, which
    is not in git.
  - Build: export each workflow as JSON into `n8n/workflows/`. Check that no secret is in
    the export. Write down how to import them into a fresh n8n. Also keep the Shopify
    webhook subscription as a small script (D20), since it lives in Shopify, not in n8n or
    the repo.
  - Done when: a brand new n8n container, and a fresh webhook subscription, can be brought
    to the same state from the repo plus `.env`.

### Part F: from laptop to server

- [ ] **1.13 Server rehearsal on a Multipass VM**
  - Goal: learn to set up and secure a server somewhere a mistake costs nothing.
  - Build:
    1. Install Multipass, run `multipass find`, and launch the newest Ubuntu LTS
       (2 CPUs, 2 GB memory, 10 GB disk).
    2. Install Docker inside it with Docker's official Ubuntu instructions (apt
       repository method).
    3. Get the repo and `.env` onto it, import the workflows (1.12), and run the stack.
    4. Install Tailscale on the laptop and the VM, and SSH over the Tailscale address.
    5. Apply the server measures in [../SECURITY.md](../SECURITY.md): keys-only SSH,
       root login off, firewall, automatic security updates.
    6. Try the Docker port trap on purpose: publish a port without `127.0.0.1`, turn on
       `ufw`, and see that the port is still reachable. Then fix it.
  - Write down every command that worked. That list is the script for 1.14.
  - Done when: the stack runs on the VM, SSH works only over Tailscale with keys, and the
    port trap has been seen and fixed. Then delete the VM and rebuild it from your notes
    once, to prove the notes are complete.

- [ ] **1.14 Move to Oracle Cloud Always Free**
  - Goal: always on, not only while the laptop is open.
  - Build: create the cloud machine and repeat the 1.13 script on it. Add the cloud
    firewall (Oracle security list) blocking all inbound, and an n8n volume backup with a
    tested restore. The `cloudflared` service comes along in the compose file: stop the
    stack on the laptop or VM first, so the tunnel runs in one place. The Shopify webhook
    address does not change.
  - **Confirm:** the current Always Free machine sizes and limits before signing up.
  - If Oracle sign-up fails or has no free capacity, keep running on the Multipass VM
    and record that in DECISIONS.md.
  - This step can move to the start of phase 2 if phase 1 is otherwise ready to show.
  - Done when: the laptop is closed and a stock change still alerts.

- [ ] **1.15 Show it**
  - Record a short clip: change stock in Shopify admin, alert arrives on the phone.
  - Update the README with the clip, a real-runs table and Quick Start.
  - Fill in the proof section below.
  - Write the post.

## Repo layout at the end of this phase

```
docker-compose.yml      n8n and cloudflared services
cloudflared/config.yml  tunnel ingress rules (which paths are public)
.env.example            every variable the stack needs, without values
.gitignore              ignores .env
n8n/workflows/          exported workflow JSON
docs/                   this documentation
```

## Decisions made in this phase

Short version here, full reasoning in [../DECISIONS.md](../DECISIONS.md).

- D16 (1.4): Slack is the owner channel.
- D17 (1.5): Shopify access through a Dev Dashboard app, `Store AI Crew`, custom
  distribution, scopes `read_products,read_inventory`, tokens from the client
  credentials grant (24 hours each). Admin API version `2026-10`.
- D18 (1.6): free domain `mjesar.dpdns.org` on Cloudflare, named tunnel with
  `cloudflared` as a compose service, so laptop, VM and Oracle use the same address.
- D19 (1.6): the tunnel container gets its secret as a token from `.env`, not as a
  mounted credentials file.
- D20 (1.7): webhooks subscribed shop-specific with `webhookSubscriptionCreate`.
- D21 (1.8): the webhook signing secret lives in an n8n Crypto credential, and the
  built-in Crypto node computes the HMAC.
- D22 (1.9): duplicate deliveries are caught by n8n's built-in Remove Duplicates node on
  `X-Shopify-Webhook-Id`, with the history kept in n8n's own database.
- D23 (1.10): a fresh Shopify token on every alert, from an HTTP Request node whose
  client ID and secret come from a domain-locked Custom Auth credential.
- D24 (1.10): every stock change below the threshold alerts; suppression waits for
  phase 2's reorder state.
- D25 (1.11): failures after the reply are handled in n8n: retries on the three outside
  calls, a check that turns a GraphQL error into a failed run, and an error workflow that
  posts every failed run to Slack.
- D26 (1.12): the tunnel's rules file names no tunnel ID or hostname, so it is the same
  for every copy of the repo; the token in `.env` picks the tunnel.

## What broke

Every real problem hit, what the cause turned out to be, and how it was found. This is the
most useful section for the post, so write it when it happens.

- **2026-11-11, step 1.3: the encryption key was printed into an AI assistant chat.** While showing what
  n8n keeps in its data folder, a command meant to print only the field names of
  `/home/node/.n8n/config` failed to parse the file, and Node's error message quoted the
  offending line, which was the key. Lesson: a command that touches a secret file must be
  safe even when it fails, so read secrets only inside a `try` that prints nothing but a
  yes or no. Fix: nothing had been encrypted yet, so the volume was deleted and a new
  key generated. Also learned: n8n copies the key into `config` inside its volume, so
  volume backups are secret too.
- **2026-11-11, step 1.4: Telegram's bot API is blocked from the laptop in Pakistan.**
  `api.telegram.org` resolves to Telegram's real address (149.154.166.110), but every
  connection on ports 443 and 80 times out, while Google, GitHub, Slack, Discord, ntfy
  and Meta's API answer in under a second. Later `web.telegram.org` loaded, but the bot
  API stayed blocked. The phone app still works (slowly) because Telegram's apps have
  their own ways around blocks; n8n makes plain HTTPS calls and has none. Not yet known
  whether the block is country-wide or one provider (test: same `curl` over a phone
  hotspot). It only affects development on the laptop: from the Oracle server outside
  Pakistan the API is reachable directly. Workarounds considered: WARP or a VPN (ruled
  out, no VPN dependency for this project), a Cloudflare Worker relay (n8n 2.47.4's Telegram credential has a
  **Base URL** field, default `https://api.telegram.org`, checked in the container
  source), moving to the server sooner, or Slack while on the laptop (D15). Store owners
  in Pakistan would hit the same block, which makes the WhatsApp extra more valuable.

- **2026-11-12, step 1.5: an Admin API token was pasted into an AI assistant chat.** The
  first token request printed the whole JSON reply, token included, and it was copied into
  the conversation to show it worked. Low risk (read only, dev store, expires within 24
  hours), so it was left to expire. Lesson: capture tokens straight into a shell variable
  (`TOKEN=$(curl ... | jq -r .access_token)`) so they never reach the screen.

- **2026-11-12, step 1.6: creating a tunnel in the dashboard asks for a payment method.**
  Cloudflare's dashboard creates tunnels inside Zero Trust, and activating Zero Trust's
  free plan asks for a card or PayPal ($0 a month, usage above the allowance billed). The
  same named tunnel can be created from the CLI instead (`cloudflared tunnel login`,
  `create`, `route dns`), which needs no Zero Trust sign-up. The rules then live in a
  committed `config.yml` rather than the dashboard, which suits a repo that is the source
  of truth anyway.
- **2026-11-13, step 1.6: the container could not have read the tunnel's credentials
  file.** `cloudflared tunnel create` writes a `.json` key readable only by the user who
  ran it (uid 1000), but the `cloudflare/cloudflared` image runs as its own non-root user
  (uid 65532), so mounting the file would fail with permission denied. Found before it
  broke, by reading the image's Dockerfile (`USER 65532:65532`). Fix: pass the same secret
  as a token in `TUNNEL_TOKEN` from `.env` (D19), then prove the local ingress rules still
  apply with a token.
- **2026-11-16, step 1.9: the first replay failed the signature check.** The replay sent
  the original body and the original signature, yet the If node went false. Two values
  n8n already had told which half was wrong: the Crypto node's `computedHmac` in the
  original run and in the replay were identical, so the body bytes matched and the
  signature header had been copied wrong. With the header copied from the original run's
  `computedHmac` (equal to Shopify's header, since that run passed), the replay passed.
  Lesson: when a signature fails, compare the computed values first; they separate "the
  body changed" from "the signature changed" in one look.
- **2026-11-16, step 1.9: no way to download the raw body from an execution.** In n8n
  2.47.4 the Webhook node's binary `data` card in a past execution offers only **View**.
  The body was copied from the viewer and written with `printf '%s' '...' > file`, which
  adds no trailing newline (an editor usually adds one, and one extra byte breaks the
  signature). The escaped slashes Shopify sends (`gid:\/\/shopify`) were still in the
  viewer's text, a sign it showed the raw bytes and not re-serialized JSON. `curl` then
  sent it with `--data-binary`, because `-d` strips newlines.
- **2026-11-18, step 1.10: an edit that did not run.** After adding `Below threshold?`,
  the first stock change ran the old version of the workflow and stopped at
  `Skip repeat deliveries`. The node had been saved, not published, and the production
  URL that Shopify calls always runs the published version. Lesson: after any change,
  publish before testing with a real delivery.
- **2026-11-18, step 1.10: a header that would have sent a word, not a token.** The first
  value for `X-Shopify-Access-Token` was `access_token` in an Expression field without
  `{{ }}`. n8n only evaluates what is inside the braces, so the preview under the field
  showed the literal text, and Shopify would have answered 401. Caught by reading that
  preview before running. Fixed with `{{ $('Get Shopify token').item.json.access_token }}`.
- **2026-11-19, step 1.11: a saved credential cannot be read back.** To break the Shopify
  credential on purpose, the plan was to change one character of the client ID. But n8n
  shows a saved Custom Auth JSON as `"client_id": "***"`, and saving the field with those
  placeholders in it risked storing them in place of the real secret. The credential was
  broken through its Allowed Domains instead (an `x` added to the host), which is shown
  in plain text and is undone by deleting one character.
- **2026-11-19, step 1.11: the failure alert's link went to a 404.** The first failure
  alert linked to `https://hooks.mjesar.dpdns.org/workflow/.../executions/31`. n8n's
  `UrlService.getInstanceBaseUrl()` (read in the container's own code) uses
  `N8N_EDITOR_BASE_URL` and, when it is unset, falls back to the webhook URL. The tunnel
  only forwards `/webhook/` and `/healthz` (1.6), so the link hit its 404, which is right
  for a private editor and useless as a link. Fixed with
  `N8N_EDITOR_BASE_URL=http://localhost:5678/` and `docker compose up -d`. On the server
  (1.13) it becomes the Tailscale address.

## Proof

Real runs only. If a number has not been measured, it does not go here.

| Date | What was done | Result |
| --- | --- | --- |
| 2026-11-11 | 1.1: `apt upgrade`, then checked versions and source | Docker Engine 29.9.3 and Compose v5.7.1, both from Docker's official stable apt repository (download.docker.com), installed version equals newest available |
| 2026-11-11 | 1.2: `.gitignore`, `.env.example`, `.env` with a key from `openssl rand -hex 32` | `git status` lists `.gitignore` and `.env.example`, not `.env`. `.env` has permissions 600 (owner only) |
| 2026-11-11 | 1.3: n8n `docker.n8n.io/n8nio/n8n:2.47.4` (npm `stable` and `latest` tags; 2.48.1 was beta), port bound to 127.0.0.1, named volume `n8n_data` | `docker compose ps` shows `127.0.0.1:5678->5678/tcp`, `/healthz` returns 200. Owner account created, then `down` and `up -d`: new container (17:17:59 UTC) on the volume from 17:10:50 UTC, n8n reports setup no longer needed, so the data survived |
| 2026-11-12 | 1.4: Slack app `Store AI Crew` (bot scope `chat:write` only) invited to `#store-alerts`; n8n credential "Slack API" with the bot token; workflow `Slack test` = Manual Trigger, then Slack "Send a message" to the channel by ID | Message "Hello from n8n" posted by Store AI Crew in `#store-alerts`. n8n appended its default footer "Automated with this n8n workflow" |
| 2026-11-12 | 1.5 (part): reused dev store `test-store-plus-9eiwvuh4` (created from the Dev Dashboard, so it is in the same organization as the app). Track quantity on for 4 products | The Collection Snowboard: Liquid (`8559152267425`) 10, The Compare at Price Snowboard (`8559152005281`) 5, The 3p Fulfilled Snowboard (`8559152201889`) 20, The Collection Snowboard: Hydrogen (`8559151841441`) 3 |
| 2026-11-12 | 1.5: Dev Dashboard app `Store AI Crew` (custom distribution, scopes `read_products,read_inventory`, no redirect URLs, not embedded) installed on the store. Token from the client credentials grant, then a GraphQL `products(first: 10)` query on Admin API `2026-10` with `curl` | Token reply: `scope` `read_inventory,read_products`, `expires_in` 86399. Query returned 10 products with `totalInventory`, `tracksInventory` and inventory item IDs, including Hydrogen (3) and Compare at Price (5). Query cost 26 of 20000 available. Note: most sample products also track stock, some at 0 |
| 2026-11-12 | 1.6 (part): free domain `mjesar.dpdns.org` (DigitalPlat) added to Cloudflare's free plan; DigitalPlat nameservers replaced with `nataly.ns.cloudflare.com` and `nitin.ns.cloudflare.com` | `dig NS mjesar.dpdns.org @1.1.1.1` and the parent's `ns1.digitalplat.org` both return the two Cloudflare nameservers, minutes after the change |
| 2026-11-12 | 1.6 (part): `cloudflared` CLI from Cloudflare's apt repository (pkg.cloudflare.com, suite `any`, the recommended one; no 26.04-specific suite exists). Used only for setup (login, create, route dns); the tunnel itself runs from the `cloudflare/cloudflared` image | `cloudflared --version` prints `2026.11.0 (built 2026-11-12-12:17 UTC)`, the latest GitHub release (published the same day) |
| 2026-11-12 | 1.6 (part): `cloudflared tunnel login`, zone `mjesar.dpdns.org` chosen and authorized in the browser | Browser: "Cloudflared has installed a certificate allowing your origin to create a Tunnel on this zone." No Zero Trust sign-up or payment method needed |
| 2026-11-12 | 1.6 (part): `cloudflared tunnel create store-ai-crew`, one tunnel per project since the domain is shared | ID `48bdbbd9-e1c4-4eaf-9605-ff0ec1cd3894`, created 17:07:50 UTC, credentials file `~/.cloudflared/<id>.json` (secret, outside the repo). `cert.pem` is `-rw-------`. `cloudflared tunnel list` shows it with no connections yet |
| 2026-11-12 | 1.6 (part): `cloudflared tunnel route dns store-ai-crew hooks.mjesar.dpdns.org` | "Added CNAME hooks.mjesar.dpdns.org which will route to this tunnel" (17:16:52 UTC). `dig +short hooks.mjesar.dpdns.org @1.1.1.1` returns Cloudflare proxy IPs `104.21.15.170` and `172.67.163.80`, so the record is public and proxied |
| 2026-11-12 | 1.6 (part): `cloudflared/config.yml`: rule `^/webhook/` and rule `^/healthz$` on `hooks.mjesar.dpdns.org` to `http://n8n:5678`, catch-all `http_status:404` | `ingress validate` prints OK. `ingress rule .../signin` matches rule #2 (the 404 catch-all; rules count from 0), `ingress rule .../webhook/inventory-update` matches rule #0 to `http://n8n:5678`. So the editor is not reachable through the tunnel, and path rules do work on a locally-managed tunnel |
| 2026-11-13 | 1.6 (part): `cloudflared` compose service, image `cloudflare/cloudflared:2026.11.0` (amd64 and arm64), `TUNNEL_TOKEN` from `.env` (D19), rules file mounted read-only, `docker compose up -d` | Logs: 4 connections registered (2 `khi01` Karachi, 2 `sin12`/`sin15` Singapore, QUIC), all pre-checks PASS. From the laptop: `/healthz` 200 `{"status":"ok"}`; `/signin` 404 with an empty body (the tunnel's catch-all, n8n never saw it); `/webhook/does-not-exist` 404 from n8n ("webhook is not registered"), so webhook paths reach n8n. Local `config.yml` rules apply with a token |
| 2026-11-13 | 1.6 (part): phone browser | `https://hooks.mjesar.dpdns.org/healthz` shows `{"status": "ok"}`; `/health` (not in the rules) gets the catch-all's 404 |
| 2026-11-13 | 1.6 (part): `credentials-file` line removed from `config.yml` (unused with a token), `docker compose restart cloudflared` | Settings log shows only `config:/etc/cloudflared/config.yml`, 4 connections re-registered, `/healthz` 200, `/signin` 404 |
| 2026-11-13 | 1.6: `N8N_WEBHOOK_URL=https://hooks.mjesar.dpdns.org/` and `N8N_PROXY_HOPS=1` in `.env`, then `docker compose up -d` (recreates n8n; `restart` would keep the old environment) | n8n container recreated, `printenv` inside shows both values, `/healthz` still 200. A new Webhook node shows `https://hooks.mjesar.dpdns.org/webhook-test/<id>` after a full reload of the editor tab (a tab opened before the change still showed `http://localhost:5678/...`) |
| 2026-11-13 | 1.7 (part): n8n workflow `Low stock alert`, Webhook node `POST` at path `shopify/inventory-levels-update`, Respond Immediately, published. Test `curl -X POST` with a dummy JSON body through the tunnel | `{"message":"Workflow was started"}`, HTTP 200 |
| 2026-11-13 | 1.7 (part): token into a shell variable (`TOKEN=$(curl ... \| jq -r .access_token)`, only its length printed), then `webhookSubscriptionCreate` on Admin API `2026-10`, topic `INVENTORY_LEVELS_UPDATE`, `uri` the production URL, format JSON (D20) | Subscription `gid://shopify/WebhookSubscription/1722870104225`, `apiVersion` `2026-10`, `userErrors` empty. Query cost 10 |
| 2026-11-13 | 1.7: stock of The Collection Snowboard: Hydrogen changed from 3 to 2 in Shopify admin | Production execution #7 in n8n, succeeded in 17 ms. Headers: `user-agent: Shopify-Captain-Hook`, `host: hooks.mjesar.dpdns.org`, `cdn-loop: cloudflare`. Body: `inventory_item_id` 48683436081313, `location_id` 81985503393, `available` 2, `updated_at`, `admin_graphql_api_id` (an `InventoryLevel` gid). No product title or variant in the payload |
| 2026-11-14 | 1.8 (part): Crypto credential with the app's client secret as Hmac Secret (D21). Raw Body on in the Webhook node, Crypto node Hmac over binary `data` (SHA256, Base64). Stock changed in Shopify admin | Production execution #9 succeeded in 43 ms. `computedHmac` equal to the `x-shopify-hmac-sha256` header, so signing the raw bytes with the client secret reproduces Shopify's signature |
| 2026-11-14 | 1.8: If node compares the two, false goes to Stop and Error. Stock of the same item changed to 3 | Execution #10 succeeded in 111 ms, If node output: True Branch (1 item), Stop and Error not run |
| 2026-11-14 | 1.8: forged request, `curl -i -X POST` to the production URL with body `{"inventory_item_id":1,"available":0}` and header `X-Shopify-Hmac-Sha256: bm90LWEtcmVhbC1zaWduYXR1cmU=` (Base64 of `not-a-real-signature`) | curl: `HTTP/2 200`, `{"message":"Workflow was started"}`. In n8n the execution failed: If went false, Stop and Error "Webhook signature mismatch" |
| 2026-11-16 | 1.9 (part): `Skip repeat deliveries` (Remove Duplicates) added on the If node's true branch, published. Stock of The Collection Snowboard: Hydrogen changed to 2 in Shopify admin | Execution #13 succeeded in 200 ms. Headers include `x-shopify-webhook-id: e1cbe77c-bf2a-5c7d-9d9c-74f0fc222b8d`. Remove Duplicates output: Kept (1 item) |
| 2026-11-16 | 1.9 (part): replay of #13 with `curl -i -X POST` to the production URL, body from #13 (221 bytes, `--data-binary`), headers `X-Shopify-Hmac-Sha256` and `X-Shopify-Webhook-Id` from #13 | curl: `HTTP/2 200`. Execution #15 succeeded in 51 ms: `content-length: 221`, `user-agent: curl/8.18.0`, If true, Remove Duplicates output: Kept empty, Discarded (1 item) |
| 2026-11-16 | 1.9: `docker compose restart n8n`, then the same replay | Execution #16 succeeded in 284 ms, If true, Remove Duplicates: Discarded (1 item). The history survives a restart, so it is stored in n8n's database on the `n8n_data` volume |
| 2026-11-18 | 1.10 (part): If node `Below threshold?` (`available` Number less than 5), published. Stock of The 3p Fulfilled Snowboard changed from 20 to 19 | Execution #19: False Branch (1 item), `available` 19 |
| 2026-11-18 | 1.10 (part): stock of The Collection Snowboard: Hydrogen changed to 1 | Execution #20: True Branch (1 item), False Branch empty |
| 2026-11-18 | 1.10 (part): nodes renamed (`Shopify inventory webhook`, `Compute signature`, `Valid signature?`, `Reject bad signature`), published, stock changed | Execution #21: `Valid signature?` true, so the expressions followed the renames; `available` 3, True Branch |
| 2026-11-18 | 1.10 (part): Custom Auth credential `Shopify client credentials`, Allowed HTTP Request Domains set to the store's host only; `Get Shopify token` on the true branch | Node green, output fields `access_token`, `scope` `read_inventory,read_products`, `expires_in` 86399. The JSON body sent by Custom Auth was accepted |
| 2026-11-18 | 1.10 (part): `Look up product`, GraphQL `inventoryItem` on Admin API `2026-10` | Execution #23 succeeded in 1.595 s (the lookup 724 ms): product "The Collection Snowboard: Hydrogen", variant "Default Title", `inventoryQuantity` 3. Query cost 3 of 20000 available, restore rate 1000 per second |
| 2026-11-18 | 1.10 (part): Slack node `Send low stock alert` | In `#store-alerts`: "Low stock: The Collection Snowboard: Hydrogen. 2 left at this location, 2 in total." with n8n's footer; after turning off "Include Link to Workflow", the next alert (1 left) had none |
| 2026-11-18 | 1.10: `legacyResourceId` added to the query, admin link added to the message | `legacyResourceId` 8559151841441 (Hydrogen's product ID from 1.5). Alert "Low stock: The Collection Snowboard: Hydrogen. 3 left at this location, 3 in total. Open in Shopify"; tapping the link on the phone opened Hydrogen in Shopify |
| 2026-11-19 | 1.11 (part): Retry On Fail (3 tries, 2000 ms between, On Error still Stop Workflow) on `Get Shopify token`, `Look up product` and `Send low stock alert`, published. Stock of The Collection Snowboard: Hydrogen changed in Shopify admin | Execution #28 succeeded in 2.402 s, the normal alert arrived in Slack. On a good run the retries stay unused |
| 2026-11-19 | 1.11 (part): If node `Product found?` after `Look up product` (`$json.errors` Array does not exist AND `$json.data.inventoryItem` Object exists), false to Stop and Error `Lookup failed`, published. Stock of Hydrogen changed | Execution #29 succeeded in 2.228 s: `Product found?` true (1 item) to `Send low stock alert`, `Lookup failed` not run. Alert "4 left at this location, 4 in total" |
| 2026-11-19 | 1.11 (part): a field that does not exist (`notARealField`) added to the `Look up product` query on purpose, published, stock changed | Execution #30 failed in 1.742 s. `Look up product` stayed green (Shopify answered HTTP 200 with an `errors` array, so its retries did not fire either), `Product found?` false, `Lookup failed`: "Product lookup failed for inventory item 48683436081313: [{"message":"Field 'notARealField' doesn't exist on type 'InventoryItem'", ... "code":"undefinedField" ...}]". No Slack message with empty values |
| 2026-11-19 | 1.11 (part): workflow `Failure alert` (Error Trigger, then Slack `Send failure alert` with Retry On Fail) published, set as the Error Workflow of `Low stock alert`. Credential broken on purpose: its Allowed Domains changed to `test-store-plus-9eiwvuh4x.myshopify.com` (the saved JSON shows only `***`, so editing it risked overwriting the secret). Stock changed | Execution #31 failed in 4.116 s, `Get Shopify token` in 4.052 s with "Domain not allowed: This credential is restricted from accessing test-store-plus-9eiwvuh4.myshopify.com", so three tries with two 2 s waits. `Failure alert` execution #32 succeeded in 776 ms; Slack: ":rotating_light: Workflow failed: Low stock alert / Node: Get Shopify token / Error: Domain not allowed: ..." with a link to run 31. The error data shows the request body as `**hidden**`, so credential values do not reach the alert. The link uses the webhook host, which the tunnel answers with 404 |
| 2026-11-19 | 1.11 (part): Allowed Domains set back to `test-store-plus-9eiwvuh4.myshopify.com`, no restart, stock changed | Execution #33 succeeded; alert "Low stock: The Collection Snowboard: Hydrogen. 3 left at this location, 3 in total." n8n reads the credential on every run, so the fix applied at once |
| 2026-11-19 | 1.11: `N8N_EDITOR_BASE_URL=http://localhost:5678/` in `.env`, `docker compose up -d` (n8n recreated). Credential broken the same way, stock changed, then fixed again | Failure alert for execution #34 with "Run: http://localhost:5678/workflow/z4ONkVq96wVwMmsL/executions/34", which opens the failed run in the editor on the laptop |
| 2026-11-20 | 1.12 (part): `scripts/subscribe-webhook.sh` (client credentials token, then `webhookSubscriptions` filtered by topic `INVENTORY_LEVELS_UPDATE`, matched on `uri` with `jq`, `webhookSubscriptionCreate` only when no match), run against the live store | "Already subscribed: gid://shopify/WebhookSubscription/1722870104225 -> https://hooks.mjesar.dpdns.org/webhook/shopify/inventory-levels-update", the subscription made by hand at 1.7, so a second run creates no duplicate |
| 2026-11-20 | 1.12 (part): `tunnel:` line and both `hostname:` keys removed from `cloudflared/config.yml` (D26). Checked first on a copy with `ingress rule` against a made-up host, then `docker compose restart cloudflared` | `ingress validate` OK; for `https://hooks.example.com`, `/webhook/...` matched rule #0, `/healthz` rule #1, `/signin` and `/` the 404 catch-all. Live: "Starting tunnel tunnelID=48bdbbd9-..." taken from the token, 4 connections registered (`khi01` x2, `sin15`, `sin11`). `/healthz` 200 `{"status":"ok"}`, `/signin` 404 with an empty body (catch-all), `/webhook/does-not-exist` 404 from n8n ("webhook ... is not registered") |
