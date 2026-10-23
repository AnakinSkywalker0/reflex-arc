#!/usr/bin/env bash
# Start the active simulation from any working directory.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
prototype_dir="$project_dir/prototype10b"
python_bin="$prototype_dir/.venv/bin/python"
ollama_bin="$prototype_dir/.venv/ollama/bin/ollama"

if [[ ! -x "$python_bin" ]]; then
    echo "Python environment missing. Follow prototype10b/README.md." >&2
    exit 1
fi

# Replays and --help work without a model server.
needs_server=true
for arg in "$@"; do
    case "$arg" in
        --replay|--help|-h) needs_server=false ;;
    esac
done

server_ready() {
    "$python_bin" -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:11434/api/version", timeout=1).close()' >/dev/null 2>&1
}

if "$needs_server" && ! server_ready; then
    if [[ ! -x "$ollama_bin" ]]; then
        ollama_bin="$(command -v ollama || true)"
    fi
    if [[ -z "$ollama_bin" ]]; then
        echo "Ollama is missing. Follow prototype10b/README.md." >&2
        exit 1
    fi
    mkdir -p "$prototype_dir/runs"
    nohup "$ollama_bin" serve >"$prototype_dir/runs/ollama-server.log" 2>&1 </dev/null &
    for ((attempt = 0; attempt < 50; attempt++)); do
        if server_ready; then break; fi
        sleep 0.2
    done
    if ! server_ready; then
        echo "Ollama did not start. See prototype10b/runs/ollama-server.log." >&2
        exit 1
    fi
fi

cd -- "$prototype_dir"
exec "$python_bin" game/main.py "$@"
