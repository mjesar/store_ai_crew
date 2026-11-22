# Rebuilding n8n from the repo

n8n keeps its workflows and credentials in its own database, inside a Docker volume. If
that volume is lost (a new server, a broken disk, a fresh clone of this repo), everything
built in n8n is gone with it. This page brings n8n back to a working state from two
things only: this repo and a filled-in `.env`.

If you still have a backup of the n8n volume and the same `N8N_ENCRYPTION_KEY`, restore
that instead. Credentials come back with their secrets, and none of the manual steps
below are needed. This page is for when only the repo is left.

## What lives where

| Piece | Where it is kept | How it comes back |
| --- | --- | --- |
| Workflows (`Low stock alert`, `Failure alert`) | `n8n/workflows/<id>.json` | `scripts/restore-n8n.sh` |
| Credentials: ID, name, type, Allowed Domains | `n8n/credentials/<id>.json` (stubs, no secrets) | `scripts/restore-n8n.sh` |
| Credential secrets (3 values) | `.env` and your password manager | pasted by hand in the editor |
| Tunnel rules | `cloudflared/config.yml` | already in place, read by the `cloudflared` container |
| Shopify webhook subscription | in Shopify, not in n8n | `scripts/subscribe-webhook.sh` |

Why the secrets are pasted by hand and not imported: see D28 in
[DECISIONS.md](DECISIONS.md). In short, the repo is public, and the only way to import a
secret is to write it in plain text to a file first.

## Before you start

You need these accounts, each set up once:

- **Shopify:** a development store, and a Dev Dashboard app in the same organization with
  the scopes `read_products,read_inventory`. Its client ID and secret go in `.env`.
- **Slack:** a workspace with an alerts channel, and a Slack app with a bot token that
  has the `chat:write` scope, invited to that channel.
- **Cloudflare:** a named tunnel, with the public hostname routed to it. Its token goes
  in `.env` (D19).
- **Docker** with Compose, and `jq` (the scripts use it).

## Steps

### 1. Fill in `.env`

```bash
cp .env.example .env
```

Fill in every value. The comments in `.env.example` say where each one comes from. Use
the same `N8N_ENCRYPTION_KEY` as before if you have it; a new one is fine on a fresh
start, since no encrypted data is carried over.

### 2. Point the repo at your store and Slack channel (only if they changed)

Three values are tied to one store and one Slack workspace. They sit in the `Settings`
node at the start of each workflow (D27) and in one credential stub. Edit them in the
JSON before the restore, so they arrive correct:

| File | Field | What it is |
| --- | --- | --- |
| `n8n/workflows/z4ONkVq96wVwMmsL.json` (`Low stock alert`) | `storeHandle` | store subdomain, without `.myshopify.com` |
| same file | `slackChannel` | Slack channel ID (starts with `C`) |
| same file | `lowStockThreshold` | alert when stock falls below this |
| `n8n/workflows/WpKTY8nfc7IWLV35.json` (`Failure alert`) | `slackChannel` | same channel ID |
| `n8n/credentials/EKWdezN7Hy7wqWWM.json` | `allowedDomains` | `<store>.myshopify.com` |

### 3. Start n8n and create the owner account

```bash
docker compose up -d
```

Open http://localhost:5678 and create the owner account.

### 4. Run the restore

```bash
./scripts/restore-n8n.sh
```

Expected output ends with:

```
Successfully imported 3 credentials.
Successfully imported 2 workflows.
```

The script only runs on an empty n8n. If n8n already has a credential or a workflow, it
stops with a message instead. That guard exists because an import overwrites by ID:
the secret-free stubs would replace credentials that already hold their secrets.

### 5. Paste the three secrets

Open **Credentials** in n8n. Each credential needs one value. Two of them show a "Needs
first setup" badge; `Shopify client credentials` does not (its Allowed Domains are
already filled), but its secret is still empty.

| Credential | Field to fill | Value |
| --- | --- | --- |
| `Slack account` | Access Token | the Slack app's bot token (`xoxb-...`) |
| `Shopify webhook signing (Store AI Crew)` | the secret field | `SHOPIFY_CLIENT_SECRET` from `.env` (Shopify signs webhooks with the app's client secret) |
| `Shopify client credentials` | JSON | the block below, with the values from `.env` |

```json
{"body": {"grant_type": "client_credentials", "client_id": "<SHOPIFY_CLIENT_ID>", "client_secret": "<SHOPIFY_CLIENT_SECRET>"}}
```

Do not change the names: the workflows find their credentials by ID, and the names are
what you see in the editor.

### 6. Check and publish the workflows

The workflows arrive unpublished on purpose, so nothing goes live before its credentials
are filled in. Open each one and check that no node shows a warning, then click
**Publish**:

1. `Failure alert` first, so it is ready to report the other workflow's failures.
2. `Low stock alert`. Its workflow settings already name `Failure alert` as the error
   workflow (kept by ID).

### 7. Subscribe the store to stock changes

```bash
./scripts/subscribe-webhook.sh
```

This goes last. Shopify should only start sending once n8n is ready to answer, because
after 8 failed deliveries in a row it deletes the subscription (D25). The script is safe
to run again; it only creates the subscription when it is missing.

### 8. Check it end to end

In the Shopify admin, lower a tracked product's stock below the threshold. A Slack
alert should arrive within seconds, and the run should show as green in n8n's
**Executions**.

## Rehearsing a restore without touching the real n8n

`docker-compose.restore-test.yml` starts a second, empty n8n on
http://localhost:5679, with its own volume and no tunnel, so Shopify cannot reach it.
Two variables point `docker compose`, and the scripts, at it:

```bash
export COMPOSE_FILE=docker-compose.restore-test.yml COMPOSE_PROJECT_NAME=store_ai_crew_restore_test
docker compose up -d
./scripts/restore-n8n.sh
```

Do steps 3, 5 and 6 at http://localhost:5679. Skip step 7, since the throwaway has no
public address. When done, delete it with its data, then go back to the real n8n:

```bash
docker compose down -v
unset COMPOSE_FILE COMPOSE_PROJECT_NAME
```

Inside its container the throwaway still listens on 5678. Only the laptop side is 5679,
because n8n uses port 5679 inside the container for its task broker.

## Keeping the repo current

- After changing a workflow in the editor, run `./scripts/export-workflows.sh` and commit
  the result. It exports the published workflows and strips the owner's name and email.
- After adding a credential, add a stub for it in `n8n/credentials/`, named by its ID.
  To see its ID, type and field names without showing any secret:

  ```bash
  docker compose exec -T n8n n8n export:credentials --all --decrypted 2>/dev/null \
    | sed -n '/^\[/,$p' \
    | jq '[.[] | {id, name, type, data: (.data | map_values("***"))}]'
  ```

  Copy the ID, name and type into the stub, and keep in `data` only fields that are not
  secret.
