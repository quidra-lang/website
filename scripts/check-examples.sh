#!/usr/bin/env bash
# Verifies the example programs shown on the Quidra website against the real compiler.
#
# For every examples/*.qui:
#   - `quidra check FILE` must pass
#   - `quidra fmt FILE --check` must pass (canonical formatting)
#   - for run:true examples, `quidra run FILE [-- args]` stdout must equal FILE.out
#     (skipped when SKIP_RUN=1, because `quidra run` needs Clang)
# For every examples/invalid/*.qui:
#   - it must be listed in manifest.json under "invalid" with matching file names
#   - `quidra check FILE` must exit non-zero
#   - its combined stdout+stderr must equal FILE.diag
#   - when FILE.json exists, `quidra check FILE --json` stdout must equal it
#
# Usage: scripts/check-examples.sh          (from anywhere)
#        QUIDRA=/path/to/quidra SKIP_RUN=1 scripts/check-examples.sh
set -euo pipefail

QUIDRA="${QUIDRA:-quidra}"
SKIP_RUN="${SKIP_RUN:-0}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
examples_dir="$(cd "$script_dir/../examples" && pwd)"
manifest="$examples_dir/manifest.json"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

pass_count=0
fail_count=0
skip_count=0

pass() { echo "PASS  $1"; pass_count=$((pass_count + 1)); }
fail() { echo "FAIL  $1"; fail_count=$((fail_count + 1)); }
skip() { echo "SKIP  $1"; skip_count=$((skip_count + 1)); }

# manifest_field ID KEY -> prints the string value of KEY for the example with that id
manifest_field() {
    node -e '
        const [file, id, key] = process.argv.slice(1);
        const m = JSON.parse(require("fs").readFileSync(file, "utf8"));
        const entry = m.examples.find((e) => e.id === id);
        if (!entry) { process.exit(3); }
        const value = entry[key];
        if (Array.isArray(value)) { console.log(value.join("\n")); }
        else if (value !== undefined) { console.log(String(value)); }
    ' "$manifest" "$1" "$2"
}

# manifest_invalid_field ID KEY -> prints KEY for the invalid example with that id
manifest_invalid_field() {
    node -e '
        const [file, id, key] = process.argv.slice(1);
        const m = JSON.parse(require("fs").readFileSync(file, "utf8"));
        const entry = m.invalid.find((e) => e.id === id);
        if (!entry) { process.exit(3); }
        if (entry[key] !== undefined) { console.log(String(entry[key])); }
    ' "$manifest" "$1" "$2"
}

[ -f "$manifest" ] || { echo "missing $manifest" >&2; exit 1; }
command -v "$QUIDRA" >/dev/null 2>&1 || { echo "compiler not found: $QUIDRA" >&2; exit 1; }
echo "compiler: $("$QUIDRA" --version)"
echo

# --- valid examples -----------------------------------------------------------
cd "$examples_dir"
for source in *.qui; do
    name="$(basename "$source" .qui)"

    if "$QUIDRA" check "$source" >"$tmp_dir/check.txt" 2>&1; then
        pass "$source check"
    else
        fail "$source check"
        cat "$tmp_dir/check.txt"
    fi

    if "$QUIDRA" fmt "$source" --check >"$tmp_dir/fmt.txt" 2>&1; then
        pass "$source fmt --check"
    else
        fail "$source fmt --check"
        cat "$tmp_dir/fmt.txt"
    fi

    if ! manifest_field "$name" id >/dev/null; then
        fail "$source listed in manifest.json"
        continue
    fi
    run_flag="$(manifest_field "$name" run)"
    if [ "$run_flag" != "true" ]; then
        continue
    fi
    expected="$(manifest_field "$name" output)"
    if [ "$SKIP_RUN" = "1" ]; then
        skip "$source run (SKIP_RUN=1)"
        continue
    fi
    if [ ! -f "$expected" ]; then
        fail "$source run (missing $expected)"
        continue
    fi

    args=()
    while IFS= read -r line; do
        [ -n "$line" ] && args+=("$line")
    done < <(manifest_field "$name" args)

    run_status=0
    if [ "${#args[@]}" -gt 0 ]; then
        "$QUIDRA" run "$source" -- "${args[@]}" >"$tmp_dir/run.out" 2>"$tmp_dir/run.err" || run_status=$?
    else
        "$QUIDRA" run "$source" >"$tmp_dir/run.out" 2>"$tmp_dir/run.err" || run_status=$?
    fi
    if [ "$run_status" -eq 0 ] && diff -u "$expected" "$tmp_dir/run.out" >"$tmp_dir/run.diff"; then
        pass "$source run == $expected"
    else
        fail "$source run == $expected (exit $run_status)"
        cat "$tmp_dir/run.err"
        cat "$tmp_dir/run.diff" 2>/dev/null || true
    fi
done

# --- intentionally invalid examples ------------------------------------------
cd "$examples_dir/invalid"
for source in *.qui; do
    name="$(basename "$source" .qui)"
    expected="$name.diag"

    if ! manifest_invalid_field "$name" id >/dev/null; then
        fail "invalid/$source listed in manifest.json"
        continue
    fi
    if [ "$(manifest_invalid_field "$name" file)" != "$source" ] || [ "$(manifest_invalid_field "$name" diagnostic)" != "$expected" ]; then
        fail "invalid/$source manifest file names match"
        continue
    fi

    check_status=0
    "$QUIDRA" check "$source" >"$tmp_dir/diag.txt" 2>&1 || check_status=$?
    if [ "$check_status" -eq 0 ]; then
        fail "invalid/$source check unexpectedly passed"
        continue
    fi
    if [ ! -f "$expected" ]; then
        fail "invalid/$source diagnostic (missing $expected)"
        continue
    fi
    if diff -u "$expected" "$tmp_dir/diag.txt" >"$tmp_dir/diag.diff"; then
        pass "invalid/$source diagnostic == $expected"
    else
        fail "invalid/$source diagnostic == $expected"
        cat "$tmp_dir/diag.diff"
    fi

    if [ -f "$name.json" ]; then
        "$QUIDRA" check "$source" --json >"$tmp_dir/diag.json" 2>/dev/null || true
        if diff -u "$name.json" "$tmp_dir/diag.json" >"$tmp_dir/json.diff"; then
            pass "invalid/$source --json == $name.json"
        else
            fail "invalid/$source --json == $name.json"
            cat "$tmp_dir/json.diff"
        fi
    fi
done

echo
echo "summary: $pass_count passed, $fail_count failed, $skip_count skipped"
if [ "$fail_count" -ne 0 ]; then
    exit 1
fi
