# Kiwix Hotspot Admin Panel

WebUI allowing Hotspot Admin to access protected resources and make changes.

## Configuration

The WebUI needs to be tightly integrated with the Hotspot. It doesn't require the Dashboard but is a natural extension of it.

Its configuration is done via environment variables, with sensible defaults.

| Environ | Default | Use |
| --- | --- | --- |
| `ADMIN_USERNAME` | `missing` | Username to log into the Admin UI |
| `ADMIN_PASSWORD` | `missing` | Password to login into the Admin UI |
| `SESSION_COOKIE_NAME` | `session_id` | Name of cookie storing the session ID |
| `DEFAULT_SESSION_DURATION_MN` | `60` | Nb of minutes a session is valid for |
| `BRIDGE_SOCKET` | `/run/offspot/mekhenet.sock` | Path to the base-image Host Bridge service socket (to send host commands like reboot, etc.) |
| `OFFSPOT_YAML_PATH` | `/boot/firmware/offspot.yaml` | Path to the offspot.yaml config file (to write changes) |
| `LATEST_YAML_PATH` | `/etc/offspot/latest.yaml` | Path to latest.yaml config file (to read last config from) |
| `DOCKER_COMPOSE_PATH` | `/etc/docker/compose.yaml` | Path to the offspot Docer compose file (to read envs from) |
| `HOSTAPD_CONF_PATH` | `/etc/hostapd/hostapd.conf` | Path to hostapd config file (to read WiFi conf from) |

`BRIDGE_SOCKET`, `OFFSPOT_YAML_PATH`, `LATEST_YAML_PATH`, `DOCKER_COMPOSE_PATH`, `HOSTAPD_CONF_PATH` should be mounted from the Host. Those paths default are similar to their normal path on Host for simplicity.

## Development

```sh
DEVEL=1 uv run fastapi dev
```

For those who prefer to develop on their machine but still integrate with an actual Hotspot, a convenient way is to mount those special files over SSH.

```sh
mkdir -p ./mnt/etc/docker/ ./mnt/etc/hostapd ./mnt/boot/firmware/ ./mnt/etc/offspot
umount -f  ./mnt/etc/docker/
umount -f ./mnt/etc/hostapd
umount -f ./mnt/boot/firmware/	
umount -f ./mnt/etc/offspot
sshfs h1:/etc/docker/ ./mnt/etc/docker/
sshfs h1:/etc/hostapd ./mnt/etc/hostapd
sshfs h1:/boot/firmware/ ./mnt/boot/firmware/
sshfs h1:/etc/offspot/ ./mnt/etc/offspot
```

The Host bridge socket cannot be mounted over SSH but there's an SSH bridge you can use on your computer.

```sh
uv run uvicorn --reload --uds ./mnt/run/offspot/mekhenet.sock --app-dir $PWD "fake_socket:app"
```
