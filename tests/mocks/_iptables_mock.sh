#!/bin/sh
# Stateful mock implementation for iptables-style CLIs.
# Tracks per-table per-chain rule lists on disk so tests can
# observe realistic rule creation/removal semantics.

iptables_mock_run() {
    tool="$1"
    shift

    mock_log "$tool" "$@"

    if [ -n "${STATE_ROOT:-}" ]; then
        base_dir="${STATE_ROOT}/${tool}_state"
    else
        base_dir="${MOCK_ROOT}/${tool}_state"
    fi
    mkdir -p "$base_dir"

    iptables_mock_handle "$tool" "$base_dir" "$@"
}

iptables_mock_handle() {
    tool="$1"
    base_dir="$2"
    shift 2

    table="filter"

    while [ "$#" -gt 0 ]; do
        case "$1" in
            -t)
                if [ "$#" -lt 2 ]; then
                    return 2
                fi
                table="$2"
                shift 2
                continue
                ;;
            -w | --wait)
                shift
                if [ "$#" -gt 0 ]; then
                    case "$1" in
                        '' | *[!0-9]*) ;;
                        *)
                            shift
                            ;;
                    esac
                fi
                continue
                ;;
            -N)
                shift
                if [ "$#" -lt 1 ]; then
                    return 2
                fi
                iptables_mock_new_chain "$base_dir" "$table" "$1"
                return $?
                ;;
            -F)
                shift
                if [ "$#" -lt 1 ]; then
                    return 2
                fi
                iptables_mock_flush_chain "$base_dir" "$table" "$1"
                return $?
                ;;
            -X)
                shift
                if [ "$#" -lt 1 ]; then
                    return 2
                fi
                iptables_mock_delete_chain "$base_dir" "$table" "$1"
                return $?
                ;;
            -L)
                shift
                if [ "$#" -lt 1 ]; then
                    return 2
                fi
                iptables_mock_list_chain "$base_dir" "$table" "$1"
                return $?
                ;;
            -A)
                shift
                if [ "$#" -lt 1 ]; then
                    return 2
                fi
                chain="$1"
                shift
                iptables_mock_append "$base_dir" "$table" "$chain" "$@"
                return $?
                ;;
            -I)
                shift
                if [ "$#" -lt 1 ]; then
                    return 2
                fi
                chain="$1"
                shift
                index=1
                if [ "$#" -gt 0 ]; then
                    case "$1" in
                        '' | *[!0-9]*) ;;
                        *)
                            index="$1"
                            shift
                            ;;
                    esac
                fi
                iptables_mock_insert "$base_dir" "$table" "$chain" "$index" "$@"
                return $?
                ;;
            -C)
                shift
                if [ "$#" -lt 1 ]; then
                    return 2
                fi
                chain="$1"
                shift
                iptables_mock_check "$base_dir" "$table" "$chain" "$@"
                return $?
                ;;
            -D)
                shift
                if [ "$#" -lt 1 ]; then
                    return 2
                fi
                chain="$1"
                shift
                if [ "$#" -eq 0 ]; then
                    return 2
                fi
                case "$1" in
                    '' | *[!0-9]*)
                        iptables_mock_delete_rule "$base_dir" "$table" "$chain" "$@"
                        ;;
                    *)
                        index="$1"
                        shift
                        iptables_mock_delete_index "$base_dir" "$table" "$chain" "$index"
                        ;;
                esac
                return $?
                ;;
            *)
                shift
                ;;
        esac
    done

    return 2
}

iptables_mock_builtin_chain() {
    builtin_table="$1"
    builtin_chain="$2"

    case "$builtin_table" in
        nat)
            case "$builtin_chain" in
                PREROUTING | INPUT | OUTPUT | POSTROUTING)
                    return 0
                    ;;
            esac
            ;;
        filter)
            case "$builtin_chain" in
                INPUT | FORWARD | OUTPUT)
                    return 0
                    ;;
            esac
            ;;
    esac

    return 1
}

iptables_mock_chain_path() {
    path_base="$1"
    path_table="$2"
    path_chain="$3"
    printf '%s/%s/%s.rules' "$path_base" "$path_table" "$path_chain"
}

iptables_mock_prepare_chain() {
    prep_base="$1"
    prep_table="$2"
    prep_chain="$3"
    prep_path=$(iptables_mock_chain_path "$prep_base" "$prep_table" "$prep_chain")
    prep_dir=${prep_path%/*}
    mkdir -p "$prep_dir"
    if [ ! -f "$prep_path" ]; then
        : > "$prep_path"
    fi
    printf '%s\n' "$prep_path"
}

iptables_mock_chain_exists() {
    exists_base="$1"
    exists_table="$2"
    exists_chain="$3"
    exists_path=$(iptables_mock_chain_path "$exists_base" "$exists_table" "$exists_chain")
    if [ -f "$exists_path" ]; then
        return 0
    fi
    iptables_mock_builtin_chain "$exists_table" "$exists_chain"
    return $?
}

iptables_mock_new_chain() {
    new_base="$1"
    new_table="$2"
    new_chain="$3"

    if iptables_mock_chain_exists "$new_base" "$new_table" "$new_chain"; then
        return 1
    fi

    iptables_mock_prepare_chain "$new_base" "$new_table" "$new_chain" > /dev/null
    return 0
}

iptables_mock_flush_chain() {
    flush_base="$1"
    flush_table="$2"
    flush_chain="$3"

    if ! iptables_mock_chain_exists "$flush_base" "$flush_table" "$flush_chain"; then
        return 1
    fi

    flush_path=$(iptables_mock_prepare_chain "$flush_base" "$flush_table" "$flush_chain")
    : > "$flush_path"
    return 0
}

iptables_mock_delete_chain() {
    del_base="$1"
    del_table="$2"
    del_chain="$3"

    if iptables_mock_builtin_chain "$del_table" "$del_chain"; then
        return 1
    fi

    del_path=$(iptables_mock_chain_path "$del_base" "$del_table" "$del_chain")
    if [ -f "$del_path" ]; then
        rm -f "$del_path"
        return 0
    fi

    return 1
}

iptables_mock_list_chain() {
    list_base="$1"
    list_table="$2"
    list_chain="$3"

    if ! iptables_mock_chain_exists "$list_base" "$list_table" "$list_chain"; then
        printf 'iptables-mock: chain %s not found in table %s\n' "$list_chain" "$list_table" >&2
        return 1
    fi

    list_path=$(iptables_mock_chain_path "$list_base" "$list_table" "$list_chain")
    if [ -f "$list_path" ]; then
        cat "$list_path"
    fi
    return 0
}

iptables_mock_append() {
    app_base="$1"
    app_table="$2"
    app_chain="$3"
    shift 3

    if ! iptables_mock_chain_exists "$app_base" "$app_table" "$app_chain"; then
        return 1
    fi

    app_path=$(iptables_mock_prepare_chain "$app_base" "$app_table" "$app_chain")
    app_rule=$(iptables_mock_normalize_rule "$@")
    printf '%s\n' "$app_rule" >> "$app_path"
    return 0
}

iptables_mock_insert() {
    ins_base="$1"
    ins_table="$2"
    ins_chain="$3"
    ins_index="$4"
    shift 4

    if ! iptables_mock_chain_exists "$ins_base" "$ins_table" "$ins_chain"; then
        return 1
    fi

    ins_path=$(iptables_mock_prepare_chain "$ins_base" "$ins_table" "$ins_chain")
    ins_rule=$(iptables_mock_normalize_rule "$@")
    ins_tmp="${ins_path}.tmp.$$"
    : > "$ins_tmp"
    ins_pos=1
    ins_inserted=0

    if [ -f "$ins_path" ]; then
        while IFS= read -r ins_line || [ -n "$ins_line" ]; do
            if [ "$ins_inserted" -eq 0 ] && [ "$ins_pos" -ge "$ins_index" ]; then
                printf '%s\n' "$ins_rule" >> "$ins_tmp"
                ins_inserted=1
            fi
            printf '%s\n' "$ins_line" >> "$ins_tmp"
            ins_pos=$((ins_pos + 1))
        done < "$ins_path"
    fi

    if [ "$ins_inserted" -eq 0 ]; then
        printf '%s\n' "$ins_rule" >> "$ins_tmp"
    fi

    mv "$ins_tmp" "$ins_path"
    return 0
}

iptables_mock_check() {
    chk_base="$1"
    chk_table="$2"
    chk_chain="$3"
    shift 3

    if ! iptables_mock_chain_exists "$chk_base" "$chk_table" "$chk_chain"; then
        return 1
    fi

    chk_path=$(iptables_mock_chain_path "$chk_base" "$chk_table" "$chk_chain")
    if [ ! -f "$chk_path" ]; then
        return 1
    fi

    chk_rule=$(iptables_mock_normalize_rule "$@")

    while IFS= read -r chk_line || [ -n "$chk_line" ]; do
        if [ "$chk_line" = "$chk_rule" ]; then
            return 0
        fi
    done < "$chk_path"

    return 1
}

iptables_mock_delete_rule() {
    delr_base="$1"
    delr_table="$2"
    delr_chain="$3"
    shift 3

    if ! iptables_mock_chain_exists "$delr_base" "$delr_table" "$delr_chain"; then
        return 1
    fi

    delr_path=$(iptables_mock_chain_path "$delr_base" "$delr_table" "$delr_chain")
    if [ ! -f "$delr_path" ]; then
        return 1
    fi

    delr_rule=$(iptables_mock_normalize_rule "$@")
    delr_tmp="${delr_path}.tmp.$$"
    : > "$delr_tmp"
    delr_removed=0

    while IFS= read -r delr_line || [ -n "$delr_line" ]; do
        if [ "$delr_removed" -eq 0 ] && [ "$delr_line" = "$delr_rule" ]; then
            delr_removed=1
            continue
        fi
        printf '%s\n' "$delr_line" >> "$delr_tmp"
    done < "$delr_path"

    if [ "$delr_removed" -eq 0 ]; then
        rm -f "$delr_tmp"
        return 1
    fi

    mv "$delr_tmp" "$delr_path"
    return 0
}

iptables_mock_delete_index() {
    deli_base="$1"
    deli_table="$2"
    deli_chain="$3"
    deli_index="$4"

    if ! iptables_mock_chain_exists "$deli_base" "$deli_table" "$deli_chain"; then
        return 1
    fi

    deli_path=$(iptables_mock_chain_path "$deli_base" "$deli_table" "$deli_chain")
    if [ ! -f "$deli_path" ]; then
        return 1
    fi

    deli_tmp="${deli_path}.tmp.$$"
    : > "$deli_tmp"
    deli_pos=1
    deli_removed=0

    while IFS= read -r deli_line || [ -n "$deli_line" ]; do
        if [ "$deli_removed" -eq 0 ] && [ "$deli_pos" -eq "$deli_index" ]; then
            deli_removed=1
        else
            printf '%s\n' "$deli_line" >> "$deli_tmp"
        fi
        deli_pos=$((deli_pos + 1))
    done < "$deli_path"

    if [ "$deli_removed" -eq 0 ]; then
        rm -f "$deli_tmp"
        return 1
    fi

    mv "$deli_tmp" "$deli_path"
    return 0
}

iptables_mock_norm_append() {
    append_value="$1"
    if [ -n "$norm_out" ]; then
        norm_out="$norm_out $append_value"
    else
        norm_out="$append_value"
    fi
}

iptables_mock_normalize_rule() {
    norm_out=""

    while [ "$#" -gt 0 ]; do
        norm_token="$1"
        case "$norm_token" in
            -m)
                shift
                if [ "$#" -gt 0 ]; then
                    norm_module="$1"
                    if [ "$norm_module" = "comment" ]; then
                        shift
                        continue
                    fi
                    iptables_mock_norm_append "-m"
                    iptables_mock_norm_append "$norm_module"
                    shift
                    continue
                fi
                iptables_mock_norm_append "-m"
                ;;
            --comment)
                shift
                if [ "$#" -gt 0 ]; then
                    shift
                fi
                ;;
            *)
                iptables_mock_norm_append "$norm_token"
                shift
                ;;
        esac
    done

    printf '%s\n' "$norm_out"
}
