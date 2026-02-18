# Шпаргалка команд

## Основные

- Git (WSL): `wsl git status`, `wsl git diff --staged`, `wsl git commit -m "feat: msg"`.
- Ветки (WSL): `wsl git checkout -b branch`, `wsl git push origin branch`.
- OpenWrt: `wsl ssh root@dev-openwrt`.
- CI (WSL): `wsl gh run list`, `wsl gh run view <id> --log`.

## Дополнительные

- Копия ipk: `wsl scp package.ipk root@dev-openwrt:/tmp/`.
- Установка ipk: `wsl ssh root@dev-openwrt "opkg install /tmp/package.ipk"`.
 - Ruff (Python линтер): `wsl ruff .`.
 - MyPy (типы Python): `wsl mypy tools/`.
 - mitmproxy (прокси/трассы): `wsl mitmproxy -p 8080`.
 - HTTPie (HTTP проверки): `wsl http GET https://example.com`.
 - Символьная карта: `wsl python3 tools/analysis/build_symbol_map.py`.
 - Сниппет‑индекс: `wsl python3 tools/analysis/build_snippet_index.py`.
 - Поиск сниппетов: `wsl python3 tools/analysis/query_snippets.py "WbsTokenBuilder PHPSESSID"`.
 - TUI‑клиенты Git (WSL): `wsl ~/.local/bin/lazygit`, `wsl ~/.local/bin/gitui`.


## WiFi Airtime Keeper

- Статус: `wsl ssh root@prod-openwrt "ps w | grep wifi-airtime-keeper | grep -v grep"`.
- Логи: `wsl ssh root@prod-openwrt "logread | grep wifi-airtime-keeper | tail -10"`.
- Мониторинг: `wsl ssh root@prod-openwrt "logread -f | grep wifi-airtime-keeper"`.
- Остановить: `wsl ssh root@prod-openwrt "killall wifi-airtime-keeper.sh"`.
- Запустить: `wsl ssh root@prod-openwrt "/usr/local/bin/wifi-airtime-keeper.sh > /dev/null 2>&1 &"`.
- WiFi статистика: `wsl ssh root@prod-openwrt "ip -s link show phy1-sta0"`.
- WiFi соединение: `wsl ssh root@prod-openwrt "iw dev phy1-sta0 link"`.
