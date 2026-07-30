#!/usr/bin/env bash
set -euo pipefail

BUILD_DIR="${1:-/tmp/hccl-agent-linux-review}"

rm -rf "$BUILD_DIR"

echo "Linux CPU_SIM validation"
echo "BUILD_DIR=$BUILD_DIR"
python3 --version
cmake --version
cc --version

cmake -S hcccl -B "$BUILD_DIR" \
  -DCMAKE_BUILD_TYPE=Release \
  -DHCCL_BACKEND=CPU_SIM

cmake --build "$BUILD_DIR" -j"$(nproc)"

ctest --test-dir "$BUILD_DIR" --output-on-failure

PLUGIN_PATH="$(find "$BUILD_DIR" -type f -name 'libhccl_plugin.so' -print -quit)"
if [[ -z "$PLUGIN_PATH" ]]; then
  echo "libhccl_plugin.so not found" >&2
  exit 1
fi

export HCCL_PLUGIN_PATH="$PLUGIN_PATH"
unset DEEPSEEK_API_KEY OPENAI_API_KEY ANTHROPIC_API_KEY || true

python3 -m unittest \
  tests.test_reduce_ops \
  tests.test_reducescatter \
  tests.test_allgather \
  tests.test_dtype_emulation \
  tests.test_randomized_collective_correctness \
  tests.test_hccl_api \
  tests.test_execution_engine \
  -q

python3 -m unittest discover tests -q

echo "LINUX_CPU_SIM_VALIDATION_OK"
echo "HCCL_PLUGIN_PATH=$HCCL_PLUGIN_PATH"
