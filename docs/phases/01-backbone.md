# Phase 1: Backbone (no AI)

**Status:** in progress, started 2026-11-11. Current step: 1.3.

**Environment:** parts A to E run locally on the laptop, part F on a server.

## Goal

Stock drops on the Shopify dev store, and a Telegram alert arrives on the phone within
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
| Multipass, Tailscale, cloudflared | Not installed |
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

- [ ] **1.3 Run n8n with Docker Compose**
  - Goal: n8n running locally, with its data surviving a restart.
  - Build: a `docker-compose.yml` with one n8n service: the image pinned to the latest
    stable n8n version (not `latest`), port 5678 bound to `127.0.0.1` only, a named
    volume for `/home/node/.n8n`, and `env_file: .env`. Look up the current version on
    n8n's release notes or Docker Hub.
  - Why `127.0.0.1`: without it, anyone on the same Wi-Fi can reach the editor.
  - Done when: the editor opens at `http://localhost:5678`, you create the owner account,
    run `docker compose down` then `up` again, and the account is still there.

### Part B: first workflow and the owner channel

- [ ] **1.4 Send a Telegram message from n8n**
  - Goal: prove the output side works before touching Shopify.
  - Build: create a bot with BotFather, find your chat ID, add a Telegram credential in
    n8n, and build a two-node workflow: Manual Trigger, then Telegram "send message".
  - Done when: clicking "Execute workflow" makes your phone buzz.
  - Learn here: nodes, credentials, executions and the execution log.

### Part C: Shopify talks to n8n

- [ ] **1.5 Dev store, API access and test products**
  - Goal: a store to test against and a token n8n can use.
  - Build: a Shopify development store with a few products that track inventory, and an
    app with Admin API access to read products and inventory.
  - **Confirm:** how a dev store app gets an Admin API token today. The notes in
    `product_geo_agent/docs/shopify-auth-setup.md` cover this from an earlier project and
    are the starting point. Record which scopes were needed.
  - Done when: a `curl` call to the Admin API from the laptop returns your products.

- [ ] **1.6 Give n8n a public HTTPS address**
  - Goal: Shopify's servers can reach n8n. A VM on a laptop is not reachable from the
    internet, and Shopify only calls HTTPS addresses.
  - Build: run Cloudflare Tunnel (`cloudflared`) on the laptop so a public HTTPS address
    forwards to n8n. Set
    `WEBHOOK_URL` in `.env` so n8n shows the public address in its webhook nodes.
  - **Confirm:** Cloudflare's free quick tunnels give a random address that changes on
    every restart. A stable address needs a named tunnel and a domain on Cloudflare. See
    Q5 in [../DECISIONS.md](../DECISIONS.md).
  - Done when: opening `https://<public-address>/healthz` in your phone's browser on
    mobile data (so the request really comes from outside) gets a reply from n8n.

- [ ] **1.7 Receive the first webhook**
  - Goal: see a real Shopify event arrive.
  - Build: a new workflow starting with a Webhook node (POST). Register an
    `inventory_levels/update` webhook in Shopify pointing at it. Change a product's stock
    in Shopify admin.
  - Done when: the execution log shows the payload. Read it closely: it carries an
    inventory item ID, a location ID and the available quantity. It does not carry the
    product title. That gap is step 1.10.

### Part D: making it trustworthy

- [ ] **1.8 Verify the signature**
  - Goal: reject anything that did not come from Shopify. The address is public, so anyone
    who finds it can post to it.
  - Build: Shopify signs each webhook with an HMAC-SHA256 of the raw request body, using
    the app's secret, and sends it in the `X-Shopify-Hmac-Sha256` header. Compute the same
    value in n8n and compare. Stop the run if they differ.
  - Watch out: the signature is over the raw bytes of the body. If n8n parses the JSON
    first and you sign the re-serialized version, it will not match.
  - Done when: a real webhook passes, and a `curl` POST with a made-up body is rejected.

- [ ] **1.9 Handle duplicates**
  - Goal: one stock change, one alert. Shopify promises to deliver each event at least
    once, which means sometimes twice.
  - Build: each delivery carries an ID in its headers (**confirm** the exact header name).
    Remember handled IDs and end the run early on a repeat. Decide where to remember them.
  - Done when: replaying the same delivery twice sends one Telegram message.

- [ ] **1.10 Threshold, product lookup and the alert**
  - Goal: a useful message, only when it matters.
  - Build: an If node on the available quantity against a threshold. Below it, look up the
    product title and variant from the inventory item ID through the Admin API, then send
    a Telegram message with product, quantity left and a link to it in Shopify admin.
  - Decide: where the threshold lives (one number for the store to start).
  - Think about: stock going 4 to 3 to 2 sends three alerts for one problem. Decide
    whether that is acceptable in phase 1 or needs a "already alerted" memory.
  - Done when: dropping stock below the threshold alerts once with the right product, and
    a change above the threshold sends nothing.

- [ ] **1.11 When things fail**
  - Goal: a failure is seen, not silent.
  - Build: reply to Shopify quickly, before the slow steps (**confirm** Shopify's response
    time limit and retry policy). Add retries on the nodes that call outside services. Add
    an error workflow that sends a Telegram message when any run fails.
  - Done when: breaking the Shopify credential on purpose produces a failure alert on the
    phone, and fixing it recovers without a restart.

### Part E: keep it and show it

- [ ] **1.12 Workflows into the repo**
  - Goal: the repo is the source of truth. n8n stores workflows in its own database, which
    is not in git.
  - Build: export each workflow as JSON into `n8n/workflows/`. Check that no secret is in
    the export. Write down how to import them into a fresh n8n.
  - Done when: a brand new n8n container can be brought to the same state from the repo
    plus `.env`.

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
    firewall (Oracle security list) blocking all inbound, a named Cloudflare Tunnel, and an
    n8n volume backup with a tested restore. Point the Shopify webhook at the new address.
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
docker-compose.yml      n8n service
.env.example            every variable the stack needs, without values
.gitignore              ignores .env
n8n/workflows/          exported workflow JSON
docs/                   this documentation
```

## Decisions made in this phase

Short version here, full reasoning in [../DECISIONS.md](../DECISIONS.md).

_None yet._

## What broke

Every real problem hit, what the cause turned out to be, and how it was found. This is the
most useful section for the post, so write it when it happens.

_Nothing yet._

## Proof

Real runs only. If a number has not been measured, it does not go here.

| Date | What was done | Result |
| --- | --- | --- |
| 2026-11-11 | 1.1: `apt upgrade`, then checked versions and source | Docker Engine 29.9.3 and Compose v5.7.1, both from Docker's official stable apt repository (download.docker.com), installed version equals newest available |
| 2026-11-11 | 1.2: `.gitignore`, `.env.example`, `.env` with a key from `openssl rand -hex 32` | `git status` lists `.gitignore` and `.env.example`, not `.env`. `.env` has permissions 600 (owner only) |
