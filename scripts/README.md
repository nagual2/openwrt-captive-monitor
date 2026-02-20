# Scripts

## build_deb_docker.sh

Сборка deb-пакета с Docker-образом captive portal daemon.

```bash
wsl bash scripts/build_deb_docker.sh
```

## update-version-metadata.sh

Синхронизация версии из `VERSION` в `package/openwrt-captive-monitor/Makefile`.

```bash
wsl bash scripts/update-version-metadata.sh
```

## Связанные документы

- [docs/debian-installation.md](../docs/debian-installation.md) — установка deb-пакета
- [docker/daemon/README.md](../docker/daemon/README.md) — Docker-образ daemon
