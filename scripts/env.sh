# Source this file from the project root:  source scripts/env.sh [--offline]
# Keeps every cache inside the project and switches off telemetry, so the environment stays closed.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"

export HF_HOME="$PROJECT_ROOT/.hf_cache"            # Hugging Face models
export YOLO_CONFIG_DIR="$PROJECT_ROOT/.yolo_config"  # Ultralytics settings + fonts
export HF_HUB_DISABLE_TELEMETRY=1
export YOLO_OFFLINE=1                                 # Ultralytics: skip online checks where supported

if [ "$1" = "--offline" ]; then
  # Use after models are downloaded: any network access by HF becomes an error.
  export HF_HUB_OFFLINE=1
  export TRANSFORMERS_OFFLINE=1
  echo "[env] offline mode: HF_HUB_OFFLINE=1"
fi

if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$PROJECT_ROOT/.venv/bin/activate"
fi
echo "[env] HF_HOME=$HF_HOME"
echo "[env] YOLO_CONFIG_DIR=$YOLO_CONFIG_DIR"
