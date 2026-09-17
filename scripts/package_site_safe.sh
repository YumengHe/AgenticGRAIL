#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
task_stage_root="$task_root/output/site-stage"
mkdir -p "$task_stage_root"
export TASK_STAGE_ROOT="$(cd "$task_stage_root" && pwd -P)"
export TMPDIR="$TASK_STAGE_ROOT"
# The official helper cleans its mktemp directory. Verify every cleanup target
# remains inside the named project staging folder, in this same shell.
rm() {
  for candidate in "$@"; do
    [[ "$candidate" == -* ]] && continue
    resolved="$(realpath -- "$candidate")"
    case "$resolved" in "$TASK_STAGE_ROOT"/*) ;; *) echo 'Refusing cleanup outside project staging directory' >&2; return 1;; esac
  done
  command rm "$@"
}
export -f rm
export PATH="/c/Users/envora/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH"
bash /c/Users/envora/.codex/plugins/cache/openai-bundled/sites/0.1.57/scripts/package-site.sh "$task_root/web" "$task_root/output/${1:-site.tar.gz}"
