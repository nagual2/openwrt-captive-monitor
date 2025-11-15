# Security Contact Email Investigation

---

## 🌐 Language / Язык
**English** | [Русский](#русский)

---

## Summary
- Completed repository-wide search (including hidden directories) and located 10 occurrences of `security@nagual2.com`, all within documentation.
- Address appears only in policy/support documents as the designated security contact; no workflows, configs, or executable code reference it.
- Git history shows the address first entered the repository in commit `d6d4e101cf984f8d52be85c892fdb2483c60d572` (merge of PR #224) on 2025-11-15 by `cto-new[bot]`; no earlier commits contain the string, and other tracked branches inherit the same history.

## File occurrences
| File | Lines | Purpose |
| --- | --- | --- |
| `.github/SECURITY.md` | 200, 264 | Alternate private vulnerability contact (EN/RU sections). |
| `.github/SUPPORT.md` | 103, 139, 241, 277 | Security contact information in support guide (EN/RU). |
| `docs/contributing/CODE_OF_CONDUCT.md` | 72, 217 | Incident reporting mailbox for code-of-conduct violations (EN/RU). |
| `docs/security/README.md` | 32 | Listed as secondary disclosure channel. |
| `docs/security/SECURITY_AUDIT_REPORT.md` | 240 | Emergency contact in audit report appendix. |
| `docs/security/SECURITY_CLEANUP_SUMMARY.md` | 157 | Contact in token exposure follow-up checklist. |
| `docs/reports/SENSITIVE_INFO_REMOVAL_REPORT.md` | 79 | Categorized as intentional contact info. |

All other project files, including `.github/settings.yml`, workflows, scripts, and source code, do not reference this address.

## Git history analysis
- Command: `git --no-pager log -S "security@nagual2.com" --oneline --all`
- Result: only commit `d6d4e10` (tag `v2025.11.15.12`, merge of PR #224`).
- Commit metadata:
  - Author: `cto-new[bot] <140088366+cto-new[bot]@users.noreply.github.com>`
  - Author/Commit date: 2025-11-15 11:37:57 +0000
  - Committer: GitHub (merge commit)
- This merge introduced the policy/support documentation bundle where the address appears. No earlier ancestor commits exist (current repository history is grafted to this commit), and the only other tracked branch (`origin/actionlint-diagnostics-pr224`) is downstream and does not modify documentation.

## Threat evaluation
- The address is string-literal documentation and is not consumed by automation, build scripts, or runtime code; compromise impact is limited to misdirected email correspondence.
- The domain `nagual2.com` matches the repository owner handle (`nagual2`), suggesting it is maintainer-controlled. No sign of malicious insertion or unauthorized access in commit metadata.
- Conclusion: low technical security risk. Primary consideration is whether maintainers actually control this mailbox; if not, vulnerability reports could leak to third parties.

## Recommended actions
1. **Ownership verification:** Confirm that project maintainers control `security@nagual2.com` (DNS MX records / mailbox access). If unverified, treat as potential misconfiguration.
2. **Decide on official contact channel:** If the mailbox is legitimate, document who monitors it and ensure spam/abuse filtering. If not, replace references with trusted channels (e.g., GitHub security advisories only or an organizational mailbox).
3. **If removal is required:** Update each file listed above to remove or replace the address, keeping bilingual sections in sync. Prefer referencing the GitHub private vulnerability reporting form to avoid exposing unmanaged addresses.
4. **Communicate change:** Note the update in changelog / security docs and inform contributors so they stop using the retired address.

No additional security remediation is required unless the address is confirmed to be unauthorized.

---

## <a id="русский"></a> Расследование адреса security@nagual2.com

---

## Краткое содержание
- Выполнен полный поиск по репозиторию (включая скрытые каталоги) — найдено 10 упоминаний `security@nagual2.com`, все в текстовой документации.
- Адрес используется только в политиках и инструкциях как контакт для вопросов безопасности; в конфигурации, рабочих процессах и коде он не используется.
- История git показывает, что адрес впервые попал в репозиторий в коммите `d6d4e101cf984f8d52be85c892fdb2483c60d572` (слияние PR #224) от 15.11.2025, автор — `cto-new[bot]`. Более ранних коммитов с этой строкой нет, остальные ветки содержат ту же историю.

## Файлы с упоминанием
| Файл | Строки | Назначение |
| --- | --- | --- |
| `.github/SECURITY.md` | 200, 264 | Альтернативный канал приватного раскрытия уязвимостей (EN/RU). |
| `.github/SUPPORT.md` | 103, 139, 241, 277 | Контакты по безопасности в руководстве поддержки (EN/RU). |
| `docs/contributing/CODE_OF_CONDUCT.md` | 72, 217 | Почта для сообщений о нарушениях кодекса поведения (EN/RU). |
| `docs/security/README.md` | 32 | Дополнительный канал раскрытия. |
| `docs/security/SECURITY_AUDIT_REPORT.md` | 240 | Контакт в приложении по аудиту безопасности. |
| `docs/security/SECURITY_CLEANUP_SUMMARY.md` | 157 | Контакт в чек-листе по отзыву токена. |
| `docs/reports/SENSITIVE_INFO_REMOVAL_REPORT.md` | 79 | Отмечен как намеренно опубликованный контакт. |

Других упоминаний (настройки, скрипты, рабочие процессы) не обнаружено.

## Анализ истории git
- Команда: `git --no-pager log -S "security@nagual2.com" --oneline --all`
- Результат: единственный коммит `d6d4e10` (тег `v2025.11.15.12`, слияние PR #224`).
- Метаданные коммита:
  - Автор: `cto-new[bot] <140088366+cto-new[bot]@users.noreply.github.com>`
  - Дата автора и фиксации: 15.11.2025 11:37:57 +0000
  - Коммиттер: GitHub (merge commit)
- Именно этот коммит добавил пакет документации с рассматриваемым адресом. История репозитория начинается с него; другие ветки (например, `origin/actionlint-diagnostics-pr224`) основаны на нём и не меняют документацию.

## Оценка рисков
- Адрес присутствует только в текстовых файлах и никуда не подставляется программно; технических уязвимостей не создаёт.
- Домен `nagual2.com` совпадает с владельцем репозитория (`@nagual2`), что указывает на вероятный контроль со стороны мейнтейнера. Признаков компрометации или несанкционированных изменений нет.
- Вывод: низкий уровень риска; главная задача — убедиться, что почтовый ящик принадлежит проекту, иначе возможна утечка конфиденциальных отчётов.

## Рекомендации
1. **Проверить владение адресом:** подтвердить, что команда проекта управляет почтовым ящиком `security@nagual2.com`.
2. **Определить официальный канал связи:** при подтверждении владения оставить почту и обеспечить её мониторинг; при отсутствии доступа заменить ссылки на контролируемый канал (например, форму частного сообщения об уязвимостях GitHub).
3. **При необходимости удаления:** синхронно обновить все перечисленные файлы, удалив или заменив адрес в английской и русской версиях.
4. **Проинформировать участников:** после изменения сообщить сообществу и обновить документацию по процессам безопасности.

Дополнительных мер по защите не требуется, если владение адресом подтверждено.
