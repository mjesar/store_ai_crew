# Setting up the server

Every command that turns a fresh Ubuntu machine into the server that runs this stack, in
order, with what each one is for. It was written while rehearsing on a local Multipass VM
(step 1.13 in [phases/01-backbone.md](phases/01-backbone.md)), and it is the script for the
real server at step 1.14.

The rehearsal VM is a stand-in for the cloud machine. It runs only while the laptop is on,
so it is somewhere to make mistakes for free, not a place to run the store from.

## 1. Create the machine

On the laptop. Multipass on Linux ships as a snap, from Canonical, who also make Ubuntu.

```
sudo snap install multipass
multipass find
multipass launch 26.04 --name store-ai-crew --cpus 2 --memory 2G --disk 10G
multipass info store-ai-crew
```

- `multipass find` lists the images. The server runs the newest **LTS** (5 years of
  updates), not the newest release: 26.10 was listed too, but it is not LTS.
- The image is launched as `26.04`, not by the alias `lts`. An alias moves to the next LTS
  when it ships, so a rebuild from these notes would get a different OS.
- The size (2 CPUs, 2 GB memory, 10 GB disk) is close to a small cloud machine. Memory and
  disk are upper limits, taken from the laptop only as the VM uses them.

Result:

| Item | Value |
| --- | --- |
| Multipass | 1.17.2 (snap, stable channel) |
| Image | Ubuntu 26.04.1 LTS, image hash `7b90593f5532` |
| Address | `10.97.0.38`, private, reachable only from the laptop |
| Memory at idle | 368 MiB of 1.9 GiB |
| Disk at start | 2.2 GiB of 9.6 GiB |

To pause and resume without losing anything: `multipass stop store-ai-crew` and
`multipass start store-ai-crew`. A stopped VM uses no memory.

To get a terminal inside the VM: `multipass shell store-ai-crew` (the prompt becomes
`ubuntu@store-ai-crew`, and `exit` goes back to the laptop). On the cloud machine this is
SSH instead.

## 2. Install Docker

On the server. This follows Docker's own guide for Ubuntu
([docs.docker.com/engine/install/ubuntu](https://docs.docker.com/engine/install/ubuntu/)),
the apt repository method. Ubuntu's own `docker.io` package is skipped because it lags
behind Docker's releases. A fresh machine has no old Docker packages, so the guide's
"uninstall old versions" step is skipped too.

Tools needed to fetch the key:

```
sudo apt update && sudo apt install ca-certificates curl
```

Docker's signing key, in its own folder, so apt trusts it only for Docker's repository:

```
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

The repository itself. The two `$(...)` parts fill in the Ubuntu codename and the CPU type,
so the same lines work on an x86 VM (`amd64`) and on an Arm cloud machine (`arm64`):

```
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt update
```

`apt update` must show a line for `download.docker.com/linux/ubuntu resolute InRelease`
with no signature error.

List the versions and install the newest one, pinned, so a rebuild gets the same engine:

```
apt list --all-versions docker-ce
VERSION_STRING=5:29.10.0-1~ubuntu.26.04~resolute
sudo apt install docker-ce=$VERSION_STRING docker-ce-cli=$VERSION_STRING containerd.io docker-buildx-plugin docker-compose-plugin
```

On an Arm machine the version string is the same, and apt picks the `arm64` build. Check
the list first, since a newer version may exist by then.

Check:

```
sudo docker run hello-world
sudo docker version
docker compose version
```

`hello-world` printing "Hello from Docker!" proves the whole chain: the client reaches the
engine, the engine pulls from Docker Hub, and a container runs.

| Piece | Version installed (2026-11-23) |
| --- | --- |
| Docker Engine and CLI | 29.10.0 (pinned) |
| containerd | 2.4.2 |
| runc | 1.5.3 |
| Docker Compose plugin | 5.8.0 |

## 3. Bring the project over

On the server. The repo is public, so a read-only HTTPS clone needs no keys. Updates later
are a `git pull` instead of copying files by hand.

```
git clone https://github.com/mjesar/store_ai_crew.git
```

The `.env` holds the secrets and is never in git, so it is copied from the laptop. On the
laptop, from the project folder:

```
multipass transfer .env store-ai-crew:/home/ubuntu/store_ai_crew/.env
```

(On the cloud machine this is `scp` over Tailscale instead.) Then, on the server, make it
readable by its owner only, so no other account or service on the machine can read the
secrets:

```
chmod 600 store_ai_crew/.env
ls -la store_ai_crew/.env    # -rw------- 1 ubuntu ubuntu ...
```

## 4. SSH with a key

The n8n editor listens only on `127.0.0.1` inside the server, so it is never public. To
open it from the laptop's browser, the laptop needs SSH into the server, and later an SSH
tunnel through it. SSH logs in with a key pair: the private key stays on the laptop, and
the server lists the matching public key in `~/.ssh/authorized_keys`.

On the laptop. `multipass transfer` cannot read `~/.ssh` (the snap is not allowed into
hidden folders in the home directory), so the laptop's shell reads the key and pipes it to
a command inside the VM. `>>` appends, so the key Multipass itself uses stays in the list:

```
multipass exec store-ai-crew -- bash -c 'cat >> ~/.ssh/authorized_keys' < ~/.ssh/id_ed25519.pub
ssh ubuntu@10.97.0.38
```

Done when the login works without a password. The first connection asks to trust the
server's fingerprint; after that, SSH warns if a different machine answers at that address.

On the cloud machine the public key is given at creation time instead, in the provider's
console.

## 5. Tailscale

Tailscale joins the laptop and the server into one private network (a "tailnet"). Each
device gets a `100.x.x.x` address that only other devices in the tailnet can reach, from
anywhere. SSH and the n8n editor will be reachable only this way, so the server shows the
internet no door to knock on. Shopify still reaches n8n through the Cloudflare Tunnel,
which is a separate, public path for the webhook only.

How it works: Tailscale's servers keep the member list and hand each device the others'
public keys. The traffic itself goes directly between the devices, encrypted with
WireGuard, or through a Tailscale relay when a direct path is blocked. Either way Tailscale
cannot read it.

Free "Personal" plan: up to 6 users, unlimited devices, non-commercial use (checked
2026-11-23 on tailscale.com/pricing).

On the laptop and then on the server, the install script from Tailscale's Linux guide
(it adds Tailscale's apt repository and installs the package):

```
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
tailscale ip -4
```

On the laptop, `tailscale up` opens a login (the first one creates the tailnet). On the
server it prints a link instead: open it in the laptop's browser and click Connect. Treat
that link as a secret until it is used, since whoever opens it can add a device to the
tailnet.

Then SSH over the Tailscale address, from the laptop:

```
ssh ubuntu@100.117.248.13
```

SSH asks again to trust the host, because it remembers hosts by address. The fingerprint
must match the one from the first login (`SHA256:qTlXUVyF...`); here it did, and SSH
also noted the key was already known under another address.

| Device | Tailnet name | Address | Tailscale |
| --- | --- | --- | --- |
| Laptop | `mj-01` | `100.102.132.58` | 1.104.7 |
| Rehearsal VM | `store-ai-crew` | `100.117.248.13` | 1.104.7 |

Last, in the Tailscale admin console (Machines, the `...` menu on the server's row):
**Disable key expiry** for the server only. A device's login expires after 180 days by
default, which is a good safety net for a laptop. On a server reachable only over
Tailscale, it would mean a silent lockout months later. The row then shows "Expiry
disabled".
