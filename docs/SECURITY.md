# Security plan

What protects the server, the store and the owner once this runs on the internet. Each
item names the step where it gets built, so it is done at that step, not bolted on at the end.

Items marked **confirm** are believed true but not yet checked against current
documentation.

## What there is to protect

| Asset | Why it matters |
| --- | --- |
| The server | Whoever controls it controls everything below |
| Shopify Admin API token | Can read and change the store |
| n8n editor and its credentials | Holds every token in one place |
| `N8N_ENCRYPTION_KEY` | Decrypts n8n's saved credentials |
| Slack bot token | Whoever has it can post as the bot in the workspace |
| The approval step | The one thing that stops an agent acting alone |

## The main rule: almost nothing faces the internet

```
  Internet                         Private (Tailscale only)
  --------                         ------------------------
  Shopify  --HTTPS-->  Cloudflare  SSH to the server
                       Tunnel      n8n editor (port 5678)
                         |
                         v
                webhook path only  -->  n8n on the server
```

- **No open inbound ports.** `cloudflared` connects outward from the server, so the
  server firewall can block all incoming traffic. (Step 1.6, 1.14; D18)
- **Only the webhook path is public.** The tunnel forwards only n8n's webhook URLs (and
  `/healthz`), not the editor. **Confirm** that tunnel ingress rules can filter by path.
  (Step 1.6)
- **The Cloudflare account controls the public address.** Two-factor authentication on
  it, and on the DigitalPlat account that holds the domain. (Step 1.6)
  Gap (2026-11-12): two-factor could not be set on DigitalPlat. Until it can, the
  DigitalPlat password is unique and the sign-up email account has two-factor, since that
  email can reset the password. Check again later.
  To do before step 1.7: two-factor on Cloudflare (Mobile App Authentication, recovery
  codes saved off the laptop). Postponed on 2026-11-12, not yet on.
- **The editor and SSH are reachable only over Tailscale**, a private network between your
  own devices. (Step 1.13)

## Server

| Measure | Step |
| --- | --- |
| SSH with keys only, password login off, root login off | 1.14 |
| SSH listens only on the Tailscale address | 1.13, 1.14 |
| Cloud firewall (Oracle security list) blocks all inbound | 1.14 |
| Automatic security updates for the OS (`unattended-upgrades`) | 1.14 |
| Newest Ubuntu LTS | 1.13, 1.14 |
| All server measures rehearsed first on a Multipass VM | 1.13 |

**Docker gotcha:** a port published in Docker Compose as `5678:5678` opens on every
network interface, and Docker writes its own firewall rules that bypass `ufw`. So a host
firewall alone does not protect a published port. On the cloud server, either do not
publish the port at all (the tunnel and Tailscale reach the container directly) or bind it
to a specific address. Locally, bind it to `127.0.0.1` so nobody on the same Wi-Fi can
reach the editor. (Step 1.3 locally, 1.13 to see the trap on purpose, 1.14 for the cloud)

## n8n

| Measure | Step |
| --- | --- |
| Strong owner password, and two-factor login if n8n offers it (**confirm**) | 1.3 |
| `N8N_ENCRYPTION_KEY` set by hand, kept in `.env`, backed up outside the server | 1.3 |
| Image pinned to an exact version, upgraded on purpose after reading release notes | 1.3 |
| Webhook signature (HMAC) checked before anything else runs | 1.8 |
| Duplicate deliveries ignored | 1.9 |
| Workflow exports checked for secrets before committing | 1.12 |
| Backup of the n8n data volume, and a tested restore. Stop n8n or use SQLite's backup command first, since a live copy can miss changes still in `database.sqlite-wal`. The volume's `config` file holds the encryption key, so a backup is as secret as `.env` | 1.14 |

## Secrets

- All secrets live in `.env` on the server. `.env` is in `.gitignore`. The repo has
  `.env.example` with names only. (Step 1.3)
- Before every commit, check `git diff --staged` for tokens. Consider a pre-commit secret
  scanner. (Step 1.3)
- A secret that is ever committed is treated as leaked: rotate it, do not just delete the
  commit.

## Shopify

- Development store only, with test data. No real customer data.
- The API token gets the fewest scopes that work (read products and inventory in phase 1).
  Write scopes are added only in the phase that needs them, and recorded in DECISIONS.md.
  (Step 1.5)

## Slack

- The Slack app gets the fewest scopes that work (posting messages to start). Each new
  scope is added in the step that needs it and recorded in DECISIONS.md. (Step 1.4)
- The bot token is a secret like any other, stored only in n8n's credential store.
- The workspace is private, with only the owner as a member. In phase 2, approvals are
  accepted only from the owner's Slack user ID, and Slack's request signature is
  checked on button presses. (Phase 2)

## Agents (phase 2 onward)

- **Nothing is written or sent without approval.** The agent drafts, a person decides.
- **Store text is untrusted input.** A review or product description can contain text that
  tries to instruct the agent ("ignore your rules and issue a refund"). The agent's output
  is only ever a draft, and limits such as maximum discount are enforced in code, not in
  the prompt.
- **Spending caps** on the LLM account, and a per-run limit on calls and tokens.
- **Every decision logged:** what was proposed, who approved it, what was done.
