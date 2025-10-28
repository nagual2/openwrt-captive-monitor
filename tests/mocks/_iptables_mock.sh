#!/bin/sh
set -eu

. "$(dirname "$0")/_lib.sh"

iptables_mock_state_base() {
    mock_init
    tool="$1"
    base="$STATE_ROOT"
    if [ -z "$base" ]; then
        base="$MOCK_ROOT"
    fi
    dir="$base/$tool"
    mkdir -p "$dir"
    printf '%s\n' "$dir"
}

iptables_mock_table_dir() {
    tool="$1"
    table="$2"
    base=$(iptables_mock_state_base "$tool")
    dir="$base/$table"
    mkdir -p "$dir"
    printf '%s\n' "$dir"
}

iptables_mock_chain_file() {
    tool="$1"
    table="$2"
    chain="$3"
    dir=$(iptables_mock_table_dir "$tool" "$table")
    printf '%s/%s.rules\n' "$dir" "$chain"
}

iptables_mock_debug_enabled() {
    case "${MOCK_IPTABLES_DEBUG:-0}" in
        1 | true | TRUE | yes | YES | on | ON)
            return 0
            ;;
    esac
    return 1
}

iptables_mock_debug_log() {
    tool="$1"
    shift
    if ! iptables_mock_debug_enabled; then
        return 0
    fi
    base=$(iptables_mock_state_base "$tool")
    log_file="$base/debug.log"
    printf '%s\n' "$*" >> "$log_file"
}

iptables_mock_debug_snapshot() {
    tool="$1"
    table="$2"
    chain="$3"
    label="$4"
    if ! iptables_mock_debug_enabled; then
        return 0
    fi
    base=$(iptables_mock_state_base "$tool")
    log_file="$base/debug.log"
    file=$(iptables_mock_chain_file "$tool" "$table" "$chain")
    {
        printf '%s table=%s chain=%s\n' "$label" "$table" "$chain"
        if [ -f "$file" ] && [ -s "$file" ]; then
            while IFS= read -r line || [ -n "$line" ]; do
                printf '    %s\n' "$line"
            done < "$file"
        else
            if [ -f "$file" ]; then
                printf '    (empty)\n'
            else
                printf '    (missing)\n'
            fi
        fi
    } >> "$log_file"
}

iptables_mock_is_builtin() {
    table="$1"
    chain="$2"
    case "$table:$chain" in
        filter:INPUT | filter:FORWARD | filter:OUTPUT | \
            nat:PREROUTING | nat:INPUT | nat:OUTPUT | nat:POSTROUTING | \
            mangle:PREROUTING | mangle:INPUT | mangle:FORWARD | mangle:OUTPUT | mangle:POSTROUTING | \
            raw:PREROUTING | raw:OUTPUT | \
            security:INPUT | security:FORWARD | security:OUTPUT)
            return 0
            ;;
    esac
    return 1
}

iptables_mock_chain_exists() {
    tool="$1"
    table="$2"
    chain="$3"
    file=$(iptables_mock_chain_file "$tool" "$table" "$chain")
    if [ -f "$file" ]; then
        return 0
    fi
    if iptables_mock_is_builtin "$table" "$chain"; then
        return 0
    fi
    return 1
}

iptables_mock_require_chain() {
    tool="$1"
    table="$2"
    chain="$3"
    file=$(iptables_mock_chain_file "$tool" "$table" "$chain")
    if [ -f "$file" ]; then
        return 0
    fi
    if iptables_mock_is_builtin "$table" "$chain"; then
        : > "$file"
        return 0
    fi
    return 1
}

iptables_mock_new_chain() {
    tool="$1"
    table="$2"
    chain="$3"
    if [ -z "$chain" ]; then
        return 1
    fi
    if iptables_mock_is_builtin "$table" "$chain"; then
        return 1
    fi
    file=$(iptables_mock_chain_file "$tool" "$table" "$chain")
    if [ -f "$file" ]; then
        return 1
    fi
    : > "$file"
    return 0
}

iptables_mock_flush_chain() {
    tool="$1"
    table="$2"
    chain="$3"
    if [ -z "$chain" ]; then
        return 0
    fi
    if ! iptables_mock_require_chain "$tool" "$table" "$chain"; then
        return 1
    fi
    file=$(iptables_mock_chain_file "$tool" "$table" "$chain")
    : > "$file"
    return 0
}

iptables_mock_delete_chain() {
    tool="$1"
    table="$2"
    chain="$3"
    if [ -z "$chain" ]; then
        return 1
    fi
    if iptables_mock_is_builtin "$table" "$chain"; then
        return 1
    fi
    file=$(iptables_mock_chain_file "$tool" "$table" "$chain")
    if [ ! -f "$file" ]; then
        return 1
    fi
    if [ -s "$file" ]; then
        return 1
    fi
    rm -f "$file"
    return 0
}

iptables_mock_list_chain() {
    tool="$1"
    table="$2"
    chain="$3"
    if [ -z "$chain" ]; then
        return 0
    fi
    if ! iptables_mock_require_chain "$tool" "$table" "$chain"; then
        return 1
    fi
    return 0
}

iptables_mock_append_rule() {
    tool="$1"
    table="$2"
    chain="$3"
    rule="$4"
    if [ -z "$chain" ] || [ -z "$rule" ]; then
        iptables_mock_debug_log "$tool" "APPEND invalid-spec table=$table chain=$chain rule=$rule"
        return 1
    fi
    if ! iptables_mock_require_chain "$tool" "$table" "$chain"; then
        iptables_mock_debug_log "$tool" "APPEND missing-chain table=$table chain=$chain rule=$rule"
        return 1
    fi
    file=$(iptables_mock_chain_file "$tool" "$table" "$chain")
    printf '%s\n' "$rule" >> "$file"
    iptables_mock_debug_log "$tool" "APPEND table=$table chain=$chain rule=$rule"
    iptables_mock_debug_snapshot "$tool" "$table" "$chain" "STATE AFTER APPEND"
    return 0
}

iptables_mock_insert_rule() {
    tool="$1"
    table="$2"
    chain="$3"
    index="$4"
    rule="$5"
    if [ -z "$chain" ] || [ -z "$rule" ]; then
        iptables_mock_debug_log "$tool" "INSERT invalid-spec table=$table chain=$chain index=$index rule=$rule"
        return 1
    fi
    if ! iptables_mock_require_chain "$tool" "$table" "$chain"; then
        iptables_mock_debug_log "$tool" "INSERT missing-chain table=$table chain=$chain index=$index rule=$rule"
        return 1
    fi
    file=$(iptables_mock_chain_file "$tool" "$table" "$chain")
    case "$index" in
        '' | *[!0-9]* | 0)
            index=1
            ;;
    esac
    tmp="${file}.tmp.\$\$"
    : > "$tmp"
    inserted=0
    position=1
    if [ -f "$file" ]; then
        while IFS= read -r line || [ -n "$line" ]; do
            if [ "$inserted" -eq 0 ] && [ "$position" -eq "$index" ]; then
                printf '%s\n' "$rule" >> "$tmp"
                inserted=1
            fi
            printf '%s\n' "$line" >> "$tmp"
            position=$((position + 1))
        done < "$file"
    fi
    if [ "$inserted" -eq 0 ]; then
        printf '%s\n' "$rule" >> "$tmp"
    fi
    mv "$tmp" "$file"
    iptables_mock_debug_log "$tool" "INSERT table=$table chain=$chain index=$index rule=$rule"
    iptables_mock_debug_snapshot "$tool" "$table" "$chain" "STATE AFTER INSERT"
    return 0
}

iptables_mock_normalize_rule() {
    rule="$1"
    if [ -z "$rule" ]; then
        printf '\n'
        return 0
    fi
    # shellcheck disable=SC2086
    set -- $rule
    output=""
    while [ "$#" -gt 0 ]; do
        token="$1"
        case "$token" in
            -m)
                if [ "${2:-}" = "comment" ]; then
                    shift
                    shift
                    if [ "$#" -gt 0 ] && [ "$1" = "--comment" ]; then
                        shift
                        if [ "$#" -gt 0 ]; then
                            shift
                        fi
                    fi
                    continue
                fi
                ;;
            --comment)
                shift
                if [ "$#" -gt 0 ]; then
                    shift
                fi
                continue
                ;;
        esac
        output="$output $token"
        shift
    done
    output=${output# }
    printf '%s\n' "$output"
}

iptables_mock_check_rule() {
    tool="$1"
    table="$2"
    chain="$3"
    rule="$4"
    if [ -z "$chain" ] || [ -z "$rule" ]; then
        iptables_mock_debug_log "$tool" "CHECK invalid-spec table=$table chain=$chain rule=$rule"
        return 1
    fi
    if ! iptables_mock_require_chain "$tool" "$table" "$chain"; then
        iptables_mock_debug_log "$tool" "CHECK missing-chain table=$table chain=$chain rule=$rule"
        return 1
    fi
    file=$(iptables_mock_chain_file "$tool" "$table" "$chain")
    target=$(iptables_mock_normalize_rule "$rule")
    iptables_mock_debug_log "$tool" "CHECK table=$table chain=$chain normalized=$target raw=$rule"
    iptables_mock_debug_snapshot "$tool" "$table" "$chain" "STATE BEFORE CHECK"
    if [ ! -f "$file" ]; then
        iptables_mock_debug_log "$tool" "CHECK no-chain-file table=$table chain=$chain"
        return 1
    fi
    while IFS= read -r line || [ -n "$line" ]; do
        current=$(iptables_mock_normalize_rule "$line")
        if [ "$current" = "$target" ]; then
            iptables_mock_debug_log "$tool" "CHECK hit table=$table chain=$chain rule=$current"
            return 0
        fi
    done < "$file"
    iptables_mock_debug_log "$tool" "CHECK miss table=$table chain=$chain normalized=$target"
    return 1
}

iptables_mock_delete_rule() {
    tool="$1"
    table="$2"
    chain="$3"
    index="$4"
    rule="$5"
    if [ -z "$chain" ]; then
        iptables_mock_debug_log "$tool" "DELETE invalid-chain table=$table chain=$chain index=$index rule=$rule"
        return 1
    fi
    if ! iptables_mock_require_chain "$tool" "$table" "$chain"; then
        iptables_mock_debug_log "$tool" "DELETE missing-chain table=$table chain=$chain index=$index rule=$rule"
        return 1
    fi
    file=$(iptables_mock_chain_file "$tool" "$table" "$chain")
    if [ ! -f "$file" ]; then
        iptables_mock_debug_log "$tool" "DELETE no-chain-file table=$table chain=$chain index=$index rule=$rule"
        return 1
    fi
    iptables_mock_debug_log "$tool" "DELETE table=$table chain=$chain index=$index rule=$rule"
    iptables_mock_debug_snapshot "$tool" "$table" "$chain" "STATE BEFORE DELETE"
    tmp="${file}.tmp.\$\$"
    : > "$tmp"
    removed=0
    if [ -n "$index" ] && [ -z "${index%%[0-9]*}" ] && [ "$index" -ne 0 ]; then
        position=1
        while IFS= read -r line || [ -n "$line" ]; do
            if [ "$removed" -eq 0 ] && [ "$position" -eq "$index" ]; then
                iptables_mock_debug_log "$tool" "DELETE matched-index table=$table chain=$chain position=$position rule=$line"
                removed=1
            else
                printf '%s\n' "$line" >> "$tmp"
            fi
            position=$((position + 1))
        done < "$file"
    else
        if [ -z "$rule" ]; then
            rm -f "$tmp"
            iptables_mock_debug_log "$tool" "DELETE missing-spec table=$table chain=$chain"
            return 1
        fi
        target=$(iptables_mock_normalize_rule "$rule")
        iptables_mock_debug_log "$tool" "DELETE normalized target=$target"
        while IFS= read -r line || [ -n "$line" ]; do
            current=$(iptables_mock_normalize_rule "$line")
            if [ "$removed" -eq 0 ] && [ "$current" = "$target" ]; then
                iptables_mock_debug_log "$tool" "DELETE matched-rule table=$table chain=$chain rule=$current"
                removed=1
                continue
            fi
            printf '%s\n' "$line" >> "$tmp"
        done < "$file"
    fi
    if [ "$removed" -eq 0 ]; then
        rm -f "$tmp"
        iptables_mock_debug_log "$tool" "DELETE miss table=$table chain=$chain index=$index rule=$rule"
        return 1
    fi
    mv "$tmp" "$file"
    iptables_mock_debug_snapshot "$tool" "$table" "$chain" "STATE AFTER DELETE"
    iptables_mock_debug_log "$tool" "DELETE success table=$table chain=$chain index=$index"
    return 0
}

iptables_mock_run() {
    tool="$1"
    shift
    mock_log "$tool" "$@"
    table="filter"
    action=""
    chain=""
    index=""
    rule_args=""

    while [ "$#" -gt 0 ]; do
        arg="$1"
        case "$arg" in
            -t)
                shift
                if [ "$#" -gt 0 ]; then
                    table="$1"
                    shift
                fi
                ;;
            -A | -I | -C | -D)
                action="$arg"
                shift
                if [ "$#" -gt 0 ]; then
                    chain="$1"
                    shift
                fi
                if [ "$action" = "-I" ] || [ "$action" = "-D" ]; then
                    if [ "$#" -gt 0 ]; then
                        case "$1" in
                            '' | -* | *[!0-9]*) ;;
                            *)
                                index="$1"
                                shift
                                ;;
                        esac
                    fi
                fi
                rule_args="$*"
                break
                ;;
            -N | -F | -X | -L)
                action="$arg"
                shift
                if [ "$#" -gt 0 ]; then
                    case "$1" in
                        -*)
                            chain=""
                            ;;
                        *)
                            chain="$1"
                            shift
                            ;;
                    esac
                fi
                break
                ;;
            *)
                shift
                ;;
        esac
    done

    table=$(printf '%s' "$table" | tr '[:upper:]' '[:lower:]')

    case "$action" in
        -N)
            iptables_mock_new_chain "$tool" "$table" "$chain"
            return $?
            ;;
        -F)
            iptables_mock_flush_chain "$tool" "$table" "$chain"
            return $?
            ;;
        -X)
            iptables_mock_delete_chain "$tool" "$table" "$chain"
            return $?
            ;;
        -L)
            iptables_mock_list_chain "$tool" "$table" "$chain"
            return $?
            ;;
        -A)
            iptables_mock_append_rule "$tool" "$table" "$chain" "$rule_args"
            return $?
            ;;
        -I)
            iptables_mock_insert_rule "$tool" "$table" "$chain" "$index" "$rule_args"
            return $?
            ;;
        -C)
            iptables_mock_check_rule "$tool" "$table" "$chain" "$rule_args"
            return $?
            ;;
        -D)
            iptables_mock_delete_rule "$tool" "$table" "$chain" "$index" "$rule_args"
            return $?
            ;;
    esac

    return 0
}
