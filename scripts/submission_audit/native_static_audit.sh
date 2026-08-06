#!/usr/bin/env bash
set -euo pipefail

repo_root=/mnt/f/projects/hccl-agent
build_dir=/tmp/hccl-g3a-native-audit

for tool in cmake ctest cc nm readelf sha256sum git; do
    command -v "${tool}" >/dev/null
done

cmake -S "${repo_root}/hcccl" -B "${build_dir}" \
    -DHCCL_BACKEND=CPU_SIM -DCMAKE_BUILD_TYPE=Release \
    >/tmp/hccl-g3a-cmake-configure.log
cmake --build "${build_dir}" --parallel 2 \
    >/tmp/hccl-g3a-cmake-build.log

ctest_output=$(ctest --test-dir "${build_dir}" --output-on-failure)
if ! printf '%s\n' "${ctest_output}" | grep -q '100% tests passed'; then
    printf '%s\n' "${ctest_output}" >&2
    exit 1
fi
ctest_passed=$(printf '%s\n' "${ctest_output}" | sed -n 's/.*0 tests failed out of \([0-9][0-9]*\).*/\1/p' | tail -n 1)

artifact="${build_dir}/libhccl_plugin.so"
test -f "${artifact}"
exports=$(nm -D --defined-only "${artifact}" | awk '{print $3}' | sort | paste -sd, -)
needed=$(readelf -d "${artifact}" | sed -n 's/.*Shared library: \[\([^]]*\)\].*/\1/p' | sort | paste -sd, -)

official_state() {
    name=$1
    path=$2
    branch=$(git -c "safe.directory=${path}" -C "${path}" branch --show-current)
    commit=$(git -c "safe.directory=${path}" -C "${path}" rev-parse HEAD)
    status=$(git -c "safe.directory=${path}" -C "${path}" status --short --untracked-files=no)
    clean=false
    if test -z "${status}"; then
        clean=true
    fi
    printf '%s_BRANCH=%s\n' "${name}" "${branch}"
    printf '%s_COMMIT=%s\n' "${name}" "${commit}"
    printf '%s_TRACKED_CLEAN=%s\n' "${name}" "${clean}"
}

printf 'STATUS=PASS\n'
printf 'CPU_SIM_ARTIFACT=%s\n' "${artifact}"
printf 'CPU_SIM_SHA256=%s\n' "$(sha256sum "${artifact}" | awk '{print $1}')"
printf 'CPU_SIM_EXPORTS=%s\n' "${exports}"
printf 'CPU_SIM_NEEDED=%s\n' "${needed}"
printf 'CPU_SIM_CTEST_PASSED=%s\n' "${ctest_passed}"
official_state HCOMM /home/workspace/hcomm
official_state HCCL /home/workspace/hccl
