# План авторизации на портале conn4.com

Этот файл фиксирует не только последовательность HTTP‑запросов, но и сам алгоритм работы портала: какие сущности участвуют, как браузер приходит к успешной авторизации и как это воспроизводится скриптами Selenium и NoJS.

## Высокоуровневый алгоритм

Упрощённо авторизация состоит из семи фаз:

1. Обнаружение портала
   - Клиент обращается к «зондирующему» URL (обычно `msftconnecttest` или аналог).
   - Если интернет уже открыт, происходит редирект на нормальный сайт (например, `msn.com`), и никаких запросов к `*.conn4.com` не видно.
   - Если интернет закрыт, зонд получает 30x на `https://<site>.rdr.conn4.com/...`, что и запускает портал.

2. Первичная загрузка портала и установка cookies
   - Первый `GET https://<site>.rdr.conn4.com/` отдаёт HTML и устанавливает минимум три cookie:
     - `PHPSESSID` — идентификатор сессии, ключевой для авторизации.
     - `himalaya-site-ident` — сериализованный blob с информацией о MAC/IP/сайте.
     - `ngx_conn4_portal` — дополнительная служебная метка.
   - Эти cookies автоматически прикрепляются ко всем последующим запросам к порталу.

3. Загрузка JS/CSS‑бандлов и сцены
   - HTML подтягивает набор статики с хешами в именах (пример: `/admon/js/18060ac1afc6812c781241c871bbaaf05e5c.js`).
   - JS‑код:
     - загружает сцену `/scenes/<id>/`,
     - читает cookies и параметры,
     - подготавливает данные для последующих API‑вызовов.
   - Сами хеши в именах файлов **не используются** как вход для подписи; они служат для версиирования ресурсов. Важна именно логика внутри JS, а не имя файла.

4. Генерация `wbsApiAuthToken` и вызов `create-session`
   - JS‑код формирует структуру, включающую:
     - `siteId` (например, `1096`),
     - `remoteAddress` (IP клиента по версии портала),
     - `macAddress` (MAC клиента в портальном формате),
     - `origin` (`https://<site>.rdr.conn4.com`),
     - временную метку и таймзону.
   - Эта структура сериализуется (php‑формат), оборачивается подписью и отправляется в `authorization=token=...` при `POST /wbs/api/v1/create-session/`.
   - Ответ `200 application/json` создаёт серверную сессию и даёт вводные для дальнейшей работы.
   - В NoJS это воспроизводится через `WbsTokenBuilder` и `PhpSerializer` ([conn4_auth_lib.py](file:///c:/git/openwrt-captive-monitor/tools/conn4_auth_lib.py)) и вызов `_call_create_session_api` в [test_conn4_portal_nojs.py](file:///c:/git/openwrt-captive-monitor/tools/test_conn4_portal_nojs.py#L2440-L2487).

5. Синхронизация времени
   - После успешного `create-session` портал делает одиночный запрос `GET /_time?t=<ts>`.
   - Это простой текстовый ответ, используемый для проверки доступности и, возможно, грубой синхронизации.
   - В обоих скриптах этот шаг используется как дополнительная проверка доступности портала через SOCKS.

6. Построение тела согласия (consent body)
   - На основе:
     - исходного query‑string (параметры redirect‑страницы портала),
     - JS‑токенов (из scene и бандлов),
     - cookies (`PHPSESSID`, `himalaya-site-ident`),
     - вычисленных IP/MAC клиентского устройства
   - Формируется тело «согласия» (consent), которое включает:
     - флаги согласия: `agree`, `accept`, `terms`, `policy`, `consent`,
     - поля состояния: `loggedin`, `remembered_mac` (+ их camelCase‑варианты),
     - идентификаторы: `client_ip`/`clientIp`, `client_mac`/`clientMac`, `site_id`/`siteId`,
     - сессионные параметры: `apiSessionId`/`api_session_id`, `paymentReturnProxyUrl`/`payment_return_proxy_url`,
     - `authorization=session=<PHPSESSID>` (при наличии PHPSESSID) либо `authorization=session=<apiSessionId>` в устаревшем варианте,
     - `tariff=<id тарифа>` (в текущих трассах `381`).
   - В Selenium‑скрипте вычисление consent вынесено в отдельную функцию (см. [captive_portal_wsl_selenium.py](file:///c:/git/openwrt-captive-monitor/tools/captive_portal_wsl_selenium.py#L1438-L1485)).
   - В NoJS за это отвечает `_build_consent_body` ([test_conn4_portal_nojs.py](file:///c:/git/openwrt-captive-monitor/tools/test_conn4_portal_nojs.py#L2850-L2905)), которая использует общую функцию `build_consent_body` ([conn4_shared.py](file:///c:/git/openwrt-captive-monitor/tools/conn4_shared.py)).

7. Авторизация через `login/free` и финальный редирект
   - Основной шаг: `POST /wbs/api/v1/login/free/` с уже собранным consent‑payload.
     - Критично, что в рабочем варианте `authorization=session=<PHPSESSID>` — это поведение живого браузера, подтверждённое трассами Selenium.
   - Сервер возвращает `200 application/json` с признаками успеха (`success`, `authorized`, `status=ok`) и/или инициирует редирект.
   - После успешного `login/free` портал выполняет переходы, которые в итоге приводят к внешнему сайту (`https://www.leonardo-hotels.com/destinations` и т.п.).
   - В NoJS это реализовано двумя путями:
     - чистый API‑флоу (`_run_api_flow`, [test_conn4_portal_nojs.py](file:///c:/git/openwrt-captive-monitor/tools/test_conn4_portal_nojs.py#L2489-L2595)),
     - «форменный» `single_post_authorize`, который выбирает подходящий endpoint из HTML и отправляет POST с тем же consent‑payload ([там же](file:///c:/git/openwrt-captive-monitor/tools/test_conn4_portal_nojs.py#L2686-L2754)).

Практически полезно помнить:

- `PHPSESSID` — основной источник `authorization` для `login/free`.
- `apiSessionId` важен для `/wbs/authenticate-me/` и связанных редиректов, но не должен подменять `PHPSESSID` в `authorization`.
- Хеши в именах JS/CSS — это индикатор версии и источник логики, но не параметр подписи.

## Детализированный план фактических обменов Selenium

1. GET http://www.msftconnecttest.com/redirect и GET https://www.msftconnecttest.com/redirect
- Отправляет: стандартные заголовки браузера через SOCKS
- Получает: 302 Redirect на портал (https://1096.rdr.conn4.com/ident?...), без портальных cookies
- Подтверждение: [conn4_compare_selenium.json](file:///c:/git/openwrt-captive-monitor/conn4_compare_selenium.json#L24-L36)

2. GET https://1096.rdr.conn4.com/
- Отправляет: без портальных cookies при первом заходе
- Получает: 200 text/html; Set-Cookie: PHPSESSID, himalaya-site-ident, ngx_conn4_portal; далее браузер прикрепляет их к последующим запросам
- Подтверждение: [conn4_compare_selenium.json](file:///c:/git/openwrt-captive-monitor/conn4_compare_selenium.json#L49-L52), [conn4_debug_before_auth.json](file:///c:/git/openwrt-captive-monitor/conn4_debug_before_auth.json#L6-L35)
- Ссылки из index (полный список, найденный в HTML на момент артефакта):
  - https://1096.rdr.conn4.com/admon/js/18060ac1afc6812c781241c871bbaaf05e5c.js?c=default&a=0 — статический объект (хеш в имени)
  - https://1096.rdr.conn4.com/admon/css/screen/180661e382fde5836fb3ccc300352657af15.css?c=default&a=0 — статический объект (хеш в имени)
  - https://1096.rdr.conn4.com/favicon.ico — статический объект
  - (доп.) Второй линк на тот же CSS для media=print — статический объект

3. GET https://1096.rdr.conn4.com/cache/js-file-gz-5219199afcc85d21759284dc5bc6e377b8176b3-5b0c67083cd97bc60fa1375c3492f93a.js
- Статический объект (хеш в имени)
- Отправляет: cookies (браузер добавляет автоматически)
- Получает: 200 text/javascript
- Подтверждение: [conn4_compare_selenium.json](file:///c:/git/openwrt-captive-monitor/conn4_compare_selenium.json#L54-L121), [conn4_debug_before_auth.json](file:///c:/git/openwrt-captive-monitor/conn4_debug_before_auth.json#L75-L126)
- Ссылки из JS (статический парсинг без эмуляции):
  - https://1096.rdr.conn4.com/scenes/OShmYJu0Z4lFYbW1/
  - https://1096.rdr.conn4.com/favicon.ico
  - https://1096.rdr.conn4.com/admon/css/screen/180653ed3175bf58ffa4c15f538e3c899856.css?c=default&a=0
  - https://1096.rdr.conn4.com/admon/css/screen/180661e382fde5836fb3ccc300352657af15.css?c=default&a=0
  - https://1096.rdr.conn4.com/admon/js/1806c29b6340dd844c47870c673e2f9a7a20.js?c=default&a=0
  - https://1096.rdr.conn4.com/admon/js/18060ac1afc6812c781241c871bbaaf05e5c.js?c=default&a=0
  - https://1096.rdr.conn4.com/_time?t=<ts> (в реальных событиях вызывается один раз после create-session)
- Примечание: имена файлов включают хеши и могут меняться

4. GET https://1096.rdr.conn4.com/cache/js-file-gz-bcc095d6dd593f0295cbaf5f1cccabff713cd00-f94f8813bf76b3effdfddbb1144d36e9.js
- Статический объект (хеш в имени)
- Отправляет: cookies
- Получает: 200 text/javascript
- Подтверждение: те же артефакты
- Ссылки из JS (статический парсинг без эмуляции):
  - https://1096.rdr.conn4.com/scenes/OShmYJu0Z4lFYbW1/
  - https://1096.rdr.conn4.com/favicon.ico
  - https://1096.rdr.conn4.com/admon/css/screen/180653ed3175bf58ffa4c15f538e3c899856.css?c=default&a=0
  - https://1096.rdr.conn4.com/admon/css/screen/180661e382fde5836fb3ccc300352657af15.css?c=default&a=0
  - https://1096.rdr.conn4.com/admon/js/1806c29b6340dd844c47870c673e2f9a7a20.js?c=default&a=0
  - https://1096.rdr.conn4.com/admon/js/18060ac1afc6812c781241c871bbaaf05e5c.js?c=default&a=0
  - https://1096.rdr.conn4.com/_time?t=<ts> (в реальных событиях вызывается один раз после create-session)
- Примечание: имена файлов включают хеши и могут меняться

5. GET https://1096.rdr.conn4.com/scenes/OShmYJu0Z4lFYbW1/
- Контейнер сцены (динамический маршрут; содержит статические ассеты внутри)
- Отправляет: cookies
- Получает: 200 text/html
- Подтверждение: те же артефакты

6. GET https://1096.rdr.conn4.com/favicon.ico
- Статический объект
- Отправляет: cookies
- Получает: 200 image/x-icon
- Подтверждение: те же артефакты

7. GET https://1096.rdr.conn4.com/admon/css/screen/180653ed3175bf58ffa4c15f538e3c899856.css?c=default&a=0
- Статический объект (хеш в имени)
- Отправляет: cookies
- Получает: 200 text/css
- Подтверждение: те же артефакты

8. GET https://1096.rdr.conn4.com/admon/css/screen/180661e382fde5836fb3ccc300352657af15.css?c=default&a=0
- Статический объект (хеш в имени)
- Отправляет: cookies
- Получает: 200 text/css
- Подтверждение: те же артефакты

9. GET https://1096.rdr.conn4.com/admon/js/1806c29b6340dd844c47870c673e2f9a7a20.js?c=default&a=0
- Статический объект (хеш в имени)
- Отправляет: cookies
- Получает: 200 text/javascript
- Подтверждение: те же артефакты
- Ссылки из JS (статический парсинг без эмуляции):
  - https://1096.rdr.conn4.com/scenes/OShmYJu0Z4lFYbW1/
  - https://1096.rdr.conn4.com/favicon.ico
  - https://1096.rdr.conn4.com/admon/css/screen/180653ed3175bf58ffa4c15f538e3c899856.css?c=default&a=0
  - https://1096.rdr.conn4.com/admon/css/screen/180661e382fde5836fb3ccc300352657af15.css?c=default&a=0
  - https://1096.rdr.conn4.com/_time?t=<ts> (в реальных событиях вызывается один раз после create-session)
- Примечание: имена файлов включают хеши и могут меняться

10. GET https://1096.rdr.conn4.com/admon/js/18060ac1afc6812c781241c871bbaaf05e5c.js?c=default&a=0
- Статический объект (хеш в имени)
- Отправляет: cookies
- Получает: 200 text/javascript
- Подтверждение: те же артефакты
- Ссылки из JS (статический парсинг без эмуляции):
  - https://1096.rdr.conn4.com/scenes/OShmYJu0Z4lFYbW1/
  - https://1096.rdr.conn4.com/favicon.ico
  - https://1096.rdr.conn4.com/admon/css/screen/180653ed3175bf58ffa4c15f538e3c899856.css?c=default&a=0
  - https://1096.rdr.conn4.com/admon/css/screen/180661e382fde5836fb3ccc300352657af15.css?c=default&a=0
  - https://1096.rdr.conn4.com/_time?t=<ts> (в реальных событиях вызывается один раз после create-session)
- Примечание: имена файлов включают хеши и могут меняться

11. JS инициализация токенов в sessionStorage
- Получает: conn4-hotspot-storage-apiSessionId, conn4-hotspot-storage-paymentReturnProxyUrl
- Подтверждение: [computedTokens](file:///c:/git/openwrt-captive-monitor/conn4_compare_selenium.json#L2-L5)

12. (Опционально) GET /admon-assets/cookie-challenge.php
- Отправляет: текущие cookies
- Получает: Set-Cookie подтверждения himalaya-site-ident; HTML перезагрузки
- Использование: при сборе токенов, если cookie-челлендж не пройден

13. POST https://1096.rdr.conn4.com/wbs/api/v1/create-session/
- Отправляет: application/x-www-form-urlencoded
  - session_id=
  - with-tariffs=1
  - locationId=1096
  - locale=en_US
  - authorization=token=… (структурированный объект, включает как минимум):
    - siteId=1096
    - remoteAddress=<клиентский IP по версии портала>
    - macAddress=<клиентский MAC в портальном формате>
    - origin=https://1096.rdr.conn4.com
    - created=<UTC дата/время + timezone>
- Получает: 200 application/json (успешное создание серверной сессии)
- Подтверждение: [conn4_compare_selenium.json](file:///c:/git/openwrt-captive-monitor/conn4_compare_selenium.json#L122-L131)

14. GET https://1096.rdr.conn4.com/_time?t=<ts>
- Отправляет: cookies; параметр t как анти‑кэш/синхронизация
- Получает: 200 text/plain
- Примечание: единичный вызов после create-session; вызов без t относится к тестовому инжекту и в план не включается
- Подтверждение: [conn4_debug_before_auth.json](file:///c:/git/openwrt-captive-monitor/conn4_debug_before_auth.json#L158-L166)

15. Повторная загрузка / и ресурсов
- GET /, GET js/css/scenes
- Отправляет: cookies
- Получает: 200; подготовка UI
- Ссылки на ресурсы в индексе (примеры, содержат динамические хеши):
  - https://1096.rdr.conn4.com/cache/js-file-gz-5219199afcc85d21759284dc5bc6e377b8176b3-5b0c67083cd97bc60fa1375c3492f93a.js
  - https://1096.rdr.conn4.com/cache/js-file-gz-bcc095d6dd593f0295cbaf5f1cccabff713cd00-f94f8813bf76b3effdfddbb1144d36e9.js
  - https://1096.rdr.conn4.com/scenes/OShmYJu0Z4lFYbW1/
  - https://1096.rdr.conn4.com/favicon.ico
  - https://1096.rdr.conn4.com/admon/css/screen/180653ed3175bf58ffa4c15f538e3c899856.css?c=default&a=0
  - https://1096.rdr.conn4.com/admon/css/screen/180661e382fde5836fb3ccc300352657af15.css?c=default&a=0
  - https://1096.rdr.conn4.com/admon/js/1806c29b6340dd844c47870c673e2f9a7a20.js?c=default&a=0
  - https://1096.rdr.conn4.com/admon/js/18060ac1afc6812c781241c871bbaaf05e5c.js?c=default&a=0
- Примечание: имена файлов включают хеши (напр. `180653ed...`), которые меняются при обновлении портала или сессии.
- Подтверждение: [conn4_compare_selenium.json](file:///c:/git/openwrt-captive-monitor/conn4_compare_selenium.json#L136-L199)

16. Расчёт consent тела (готово для форм/запросов портала)
- Содержимое:
  - agree=1, accept=1, terms=1, policy=1, consent=1
  - loggedin, remembered_mac, signature
  - client_ip, client_mac, site_id
  - Дублирующие пары (оба формата): clientIp↔client_ip, clientMac↔client_mac, siteId↔site_id, rememberedMac↔remembered_mac, loggedIn↔loggedin, apiSessionId↔api_session_id, paymentReturnProxyUrl↔payment_return_proxy_url
  - authorization=session=<apiSessionId> (если нет apiSessionId → PHPSESSID)
  - tariff=381
- Подтверждение: [computedConsent](file:///c:/git/openwrt-captive-monitor/conn4_compare_selenium.json#L6-L21), реализация: [captive_portal_wsl_selenium.py](file:///c:/git/openwrt-captive-monitor/tools/captive_portal_wsl_selenium.py#L1438-L1485)

17. Пользовательское действие: «Get Free Wi‑Fi»
- Отправляет: портальные запросы (fetch/XHR/форма) с cookies и полями из consent
- Получает: 302 Redirect → https://www.leonardo-hotels.com/destinations
- Подтверждение: успешный редирект в логах теста

18. Состояние после авторизации
- Cookies: в контексте целевой страницы — отсутствуют (портальные cookies не требуются на конечном домене)
- sessionStorage: очищён
- localStorage: ad_user=new_user
- Подтверждение: итоговые логи успешного прогона
