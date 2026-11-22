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
