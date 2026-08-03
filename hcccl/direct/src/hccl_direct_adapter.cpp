#include "hccl_direct_adapter.h"

#include <array>
#include <cstdint>
#include <limits>
#include <new>
#include <thread>
#include <type_traits>

// These includes and assertions freeze ABI signatures.  This translation unit
// intentionally contains no call expression to an official ACL/HCCL function.
#include <acl/acl_rt.h>
#include <hccl/hccl.h>
#include <hccl/hccl_comm.h>

namespace {

using ExpectedAllReduce = HcclResult (*)(void *, void *, uint64_t, HcclDataType, HcclReduceOp, HcclComm, aclrtStream);
using ExpectedAllGather = HcclResult (*)(void *, void *, uint64_t, HcclDataType, HcclComm, aclrtStream);
using ExpectedReduceScatter = HcclResult (*)(void *, void *, uint64_t, HcclDataType, HcclReduceOp, HcclComm, aclrtStream);
using ExpectedAclInit = aclError (*)(const char *);
using ExpectedCommInit = HcclResult (*)(const char *, uint32_t, HcclComm *);
using ExpectedSetDevice = aclError (*)(int32_t);
using ExpectedCreateContext = aclError (*)(aclrtContext *, int32_t);
using ExpectedCreateStream = aclError (*)(aclrtStream *);
using ExpectedMalloc = aclError (*)(void **, size_t, aclrtMemMallocPolicy);
static_assert(std::is_same<decltype(&HcclAllReduce), ExpectedAllReduce>::value, "HcclAllReduce signature drifted");
static_assert(std::is_same<decltype(&HcclAllGather), ExpectedAllGather>::value, "HcclAllGather signature drifted");
static_assert(std::is_same<decltype(&HcclReduceScatter), ExpectedReduceScatter>::value, "HcclReduceScatter signature drifted");
static_assert(std::is_same<decltype(&aclInit), ExpectedAclInit>::value, "aclInit signature drifted");
static_assert(std::is_same<decltype(&aclrtSetDevice), ExpectedSetDevice>::value, "aclrtSetDevice signature drifted");
static_assert(std::is_same<decltype(&aclrtCreateContext), ExpectedCreateContext>::value, "aclrtCreateContext signature drifted");
static_assert(std::is_same<decltype(&aclrtCreateStream), ExpectedCreateStream>::value, "aclrtCreateStream signature drifted");
static_assert(std::is_same<decltype(&aclrtMalloc), ExpectedMalloc>::value, "aclrtMalloc signature drifted");
static_assert(std::is_same<decltype(&HcclCommInitClusterInfo), ExpectedCommInit>::value, "HcclCommInitClusterInfo signature drifted");

constexpr size_t kAdapterMaxBytes = static_cast<size_t>(1) << 40;
uint32_t g_runtime_leases = 0;
std::array<const hccl_direct_session_t *, 64> g_retired_sessions{};

bool retired(const hccl_direct_session_t *session) noexcept {
    for (const auto *entry : g_retired_sessions) if (entry == session) return true;
    return false;
}

void remember_retired(const hccl_direct_session_t *session) noexcept {
    for (auto &entry : g_retired_sessions) if (entry == nullptr) { entry = session; return; }
    g_retired_sessions[0] = session;
}

void forget_retired(const hccl_direct_session_t *session) noexcept {
    for (auto &entry : g_retired_sessions) if (entry == session) entry = nullptr;
}

void set_error(hccl_direct_error_t *error, hccl_direct_status_t status, const char *api, const char *message) noexcept {
    if (error != nullptr) *error = {status, 0, 0, api, message};
}

bool multiply(size_t left, size_t right, size_t *out) noexcept {
    if (left != 0 && right > std::numeric_limits<size_t>::max() / left) return false;
    *out = left * right;
    return *out <= kAdapterMaxBytes;
}

size_t dtype_size(hccl_direct_dtype_t dtype) noexcept {
    switch (dtype) {
        case HCCL_DIRECT_DTYPE_FP16: case HCCL_DIRECT_DTYPE_BF16: return 2;
        case HCCL_DIRECT_DTYPE_FP32: return 4;
        case HCCL_DIRECT_DTYPE_FP64: return 8;
        default: return 0;
    }
}

class DirectSession final {
public:
    DirectSession() noexcept : owner_thread_(std::this_thread::get_id()) {}
    ~DirectSession() noexcept { if (runtime_lease_) --g_runtime_leases; }
    DirectSession(const DirectSession &) = delete;
    DirectSession &operator=(const DirectSession &) = delete;

    hccl_direct_status_t configure(const hccl_direct_session_config_t &config, hccl_direct_error_t *error) noexcept {
        if (!owner(error, "configure") || state_ != HCCL_DIRECT_SESSION_CREATED) return invalid_state(error, "configure");
        if (config.rank_size <= 1 || config.rank_id >= config.rank_size || config.device_id < 0 ||
            (config.rank_mode != HCCL_DIRECT_RANK_TABLE && config.rank_mode != HCCL_DIRECT_ROOT_INFO) ||
            (config.rank_mode == HCCL_DIRECT_RANK_TABLE && (config.rank_table_path == nullptr || config.rank_table_path[0] == '\0')) ||
            (config.rank_mode == HCCL_DIRECT_RANK_TABLE && config.root_rank != 0) ||
            (config.rank_mode == HCCL_DIRECT_ROOT_INFO && (config.rank_table_path != nullptr || config.root_rank >= config.rank_size))) {
            set_error(error, HCCL_DIRECT_STATUS_CONFIGURATION_ERROR, "configure", "invalid mutually-exclusive rank configuration");
            return HCCL_DIRECT_STATUS_CONFIGURATION_ERROR;
        }
        config_ = config; configured_ = true; state_ = HCCL_DIRECT_SESSION_CONFIGURED;
        set_error(error, HCCL_DIRECT_STATUS_SUCCESS, "configure", "configuration accepted without reading launcher data");
        return HCCL_DIRECT_STATUS_SUCCESS;
    }

    hccl_direct_status_t preflight(int32_t device_present, hccl_direct_error_t *error) noexcept {
        if (!owner(error, "preflight") || state_ != HCCL_DIRECT_SESSION_CONFIGURED) return invalid_state(error, "preflight");
        state_ = HCCL_DIRECT_SESSION_PREFLIGHT_CHECKED;
        if (device_present == 0) {
            state_ = HCCL_DIRECT_SESSION_NO_DEVICE_EXPECTED;
            set_error(error, HCCL_DIRECT_STATUS_NO_DEVICE_EXPECTED, "preflight", "no device: runtime boundary remains closed");
            return HCCL_DIRECT_STATUS_NO_DEVICE_EXPECTED;
        }
        set_error(error, HCCL_DIRECT_STATUS_HARDWARE_BLOCKED, "preflight", "G2-F-4 never enters a real runtime");
        return HCCL_DIRECT_STATUS_HARDWARE_BLOCKED;
    }

    hccl_direct_status_t execution(int32_t explicit_request, hccl_direct_error_t *error) noexcept {
        if (!owner(error, "request_execution")) return HCCL_DIRECT_STATUS_OWNERSHIP_VIOLATION;
        const auto status = explicit_request ? HCCL_DIRECT_STATUS_HARDWARE_BLOCKED : HCCL_DIRECT_STATUS_NO_DEVICE_EXPECTED;
        set_error(error, status, "request_execution", "guard rejected request before ACL/HCCL runtime boundary");
        return status;
    }

    hccl_direct_status_t acquire_model_lease(hccl_direct_error_t *error) noexcept {
        if (!owner(error, "model_acquire_lease") || state_ != HCCL_DIRECT_SESSION_NO_DEVICE_EXPECTED || config_.model_only_test == 0) return invalid_state(error, "model_acquire_lease");
        runtime_lease_ = true; ++g_runtime_leases; state_ = HCCL_DIRECT_SESSION_RUNTIME_READY;
        set_error(error, HCCL_DIRECT_STATUS_SUCCESS, "model_acquire_lease", "logical runtime lease acquired without aclInit");
        return HCCL_DIRECT_STATUS_SUCCESS;
    }

    hccl_direct_status_t model_cleanup(hccl_direct_failure_point_t failure, hccl_direct_error_t *error) noexcept {
        if (!owner(error, "model_cleanup") || state_ != HCCL_DIRECT_SESSION_RUNTIME_READY) return invalid_state(error, "model_cleanup");
        cleanup(failure); state_ = HCCL_DIRECT_SESSION_COMPLETED;
        set_error(error, HCCL_DIRECT_STATUS_SUCCESS, "model_cleanup", "logical lease released without aclFinalize");
        return HCCL_DIRECT_STATUS_SUCCESS;
    }

    hccl_direct_status_t run_model(hccl_direct_failure_point_t failure, hccl_direct_error_t *error) noexcept {
        if (!owner(error, "run_model") || state_ != HCCL_DIRECT_SESSION_NO_DEVICE_EXPECTED || config_.model_only_test == 0) return invalid_state(error, "run_model");
        reset_trace();
        const std::array<hccl_direct_session_state_t, 9> steps = {{
            HCCL_DIRECT_SESSION_RUNTIME_READY, HCCL_DIRECT_SESSION_DEVICE_READY, HCCL_DIRECT_SESSION_CONTEXT_READY,
            HCCL_DIRECT_SESSION_STREAM_READY, HCCL_DIRECT_SESSION_COMM_READY, HCCL_DIRECT_SESSION_BUFFERS_READY,
            HCCL_DIRECT_SESSION_BUFFERS_READY, HCCL_DIRECT_SESSION_COLLECTIVE_SUBMITTED, HCCL_DIRECT_SESSION_SYNCHRONIZED}};
        const std::array<hccl_direct_failure_point_t, 9> points = {{
            HCCL_DIRECT_FAILURE_RUNTIME_LEASE, HCCL_DIRECT_FAILURE_DEVICE_BIND, HCCL_DIRECT_FAILURE_CONTEXT_CREATE,
            HCCL_DIRECT_FAILURE_STREAM_CREATE, HCCL_DIRECT_FAILURE_COMM_CREATE, HCCL_DIRECT_FAILURE_SEND_BUFFER,
            HCCL_DIRECT_FAILURE_RECV_BUFFER, HCCL_DIRECT_FAILURE_COLLECTIVE_SUBMIT, HCCL_DIRECT_FAILURE_SYNCHRONIZE}};
        for (size_t i = 0; i < steps.size(); ++i) {
            if (failure == points[i]) return fail(error, points[i]);
            state_ = steps[i];
            if (i == 0) { runtime_lease_ = true; ++g_runtime_leases; }
            if (i == 1) owns_[5] = true;
            if (i == 2) owns_[4] = true;
            if (i == 3) owns_[3] = true;
            if (i == 4) owns_[2] = true;
            if (i == 5) owns_[1] = true;
            if (i == 6) owns_[0] = true;
        }
        state_ = HCCL_DIRECT_SESSION_COMPLETED;
        cleanup(failure);
        state_ = HCCL_DIRECT_SESSION_COMPLETED;
        set_error(error, HCCL_DIRECT_STATUS_SUCCESS, "run_model", "deterministic lifecycle model completed without runtime calls");
        return HCCL_DIRECT_STATUS_SUCCESS;
    }

    hccl_direct_status_t destroy(hccl_direct_error_t *error) noexcept {
        if (!owner(error, "destroy")) return HCCL_DIRECT_STATUS_OWNERSHIP_VIOLATION;
        if (state_ == HCCL_DIRECT_SESSION_DESTROYED) return invalid_state(error, "destroy");
        if (runtime_lease_ || owns_any()) cleanup(HCCL_DIRECT_FAILURE_NONE);
        state_ = HCCL_DIRECT_SESSION_DESTROYED;
        set_error(error, HCCL_DIRECT_STATUS_SUCCESS, "destroy", "host-only state destroyed");
        return HCCL_DIRECT_STATUS_SUCCESS;
    }

    hccl_direct_status_t verify_owner(int32_t device_id, hccl_direct_error_t *error) const noexcept {
        if (!owner(error, "verify_owner") || !configured_ || device_id != config_.device_id) {
            set_error(error, HCCL_DIRECT_STATUS_OWNERSHIP_VIOLATION, "verify_owner", "session thread or device owner mismatch");
            return HCCL_DIRECT_STATUS_OWNERSHIP_VIOLATION;
        }
        set_error(error, HCCL_DIRECT_STATUS_SUCCESS, "verify_owner", "owner verified"); return HCCL_DIRECT_STATUS_SUCCESS;
    }
    hccl_direct_session_state_t state() const noexcept { return state_; }
    const hccl_direct_error_t &first_error() const noexcept { return first_error_; }
    size_t cleanup_count() const noexcept { return cleanup_count_; }
    hccl_direct_cleanup_action_t cleanup_action(size_t i) const noexcept { return i < cleanup_count_ ? cleanup_[i] : HCCL_DIRECT_CLEANUP_RUNTIME_LEASE; }
    size_t cleanup_error_count() const noexcept { return cleanup_errors_; }

private:
    bool owner(hccl_direct_error_t *error, const char *api) const noexcept {
        if (owner_thread_ == std::this_thread::get_id()) return true;
        set_error(error, HCCL_DIRECT_STATUS_OWNERSHIP_VIOLATION, api, "session used from a non-owner thread"); return false;
    }
    hccl_direct_status_t invalid_state(hccl_direct_error_t *error, const char *api) const noexcept {
        set_error(error, HCCL_DIRECT_STATUS_INVALID_STATE, api, "invalid lifecycle state transition"); return HCCL_DIRECT_STATUS_INVALID_STATE;
    }
    void reset_trace() noexcept { cleanup_count_ = 0; cleanup_errors_ = 0; first_error_ = {HCCL_DIRECT_STATUS_SUCCESS, 0, 0, "", ""}; }
    bool owns_any() const noexcept { for (bool owned : owns_) if (owned) return true; return runtime_lease_; }
    hccl_direct_status_t fail(hccl_direct_error_t *error, hccl_direct_failure_point_t point) noexcept {
        first_error_ = {HCCL_DIRECT_STATUS_INJECTED_FAILURE, 0, 0, "model", "injected lifecycle acquisition failure"};
        cleanup(point); state_ = HCCL_DIRECT_SESSION_FAILED; set_error(error, first_error_.status, first_error_.api, first_error_.message); return HCCL_DIRECT_STATUS_INJECTED_FAILURE;
    }
    void cleanup(hccl_direct_failure_point_t failure) noexcept {
        state_ = HCCL_DIRECT_SESSION_CLEANING;
        const std::array<hccl_direct_cleanup_action_t, 7> actions = {{HCCL_DIRECT_CLEANUP_RECV_BUFFER, HCCL_DIRECT_CLEANUP_SEND_BUFFER, HCCL_DIRECT_CLEANUP_COMM, HCCL_DIRECT_CLEANUP_STREAM, HCCL_DIRECT_CLEANUP_CONTEXT, HCCL_DIRECT_CLEANUP_DEVICE, HCCL_DIRECT_CLEANUP_RUNTIME_LEASE}};
        const std::array<hccl_direct_failure_point_t, 7> failures = {{HCCL_DIRECT_FAILURE_CLEANUP_RECV_BUFFER, HCCL_DIRECT_FAILURE_CLEANUP_SEND_BUFFER, HCCL_DIRECT_FAILURE_CLEANUP_COMM, HCCL_DIRECT_FAILURE_CLEANUP_STREAM, HCCL_DIRECT_FAILURE_CLEANUP_CONTEXT, HCCL_DIRECT_FAILURE_CLEANUP_DEVICE, HCCL_DIRECT_FAILURE_CLEANUP_RUNTIME_LEASE}};
        for (size_t i = 0; i < actions.size(); ++i) {
            if (i < 6 && !owns_[i]) continue;
            if (i == 6 && !runtime_lease_) continue;
            cleanup_[cleanup_count_++] = actions[i];
            if (failure == failures[i]) ++cleanup_errors_;
            if (i < 6) owns_[i] = false; else { runtime_lease_ = false; --g_runtime_leases; }
        }
    }
    std::thread::id owner_thread_;
    hccl_direct_session_state_t state_ = HCCL_DIRECT_SESSION_CREATED;
    hccl_direct_session_config_t config_{};
    bool configured_ = false;
    bool runtime_lease_ = false;
    std::array<bool, 6> owns_{};
    std::array<hccl_direct_cleanup_action_t, 7> cleanup_{};
    size_t cleanup_count_ = 0;
    size_t cleanup_errors_ = 0;
    hccl_direct_error_t first_error_{HCCL_DIRECT_STATUS_SUCCESS, 0, 0, "", ""};
};

}  // namespace

struct hccl_direct_session { DirectSession impl; };

extern "C" hccl_direct_status_t hccl_direct_session_create(hccl_direct_session_t **session, hccl_direct_error_t *error) { try { if (!session) { set_error(error, HCCL_DIRECT_STATUS_INVALID_ARGUMENT, "create", "null session output"); return HCCL_DIRECT_STATUS_INVALID_ARGUMENT; } *session = new hccl_direct_session; forget_retired(*session); set_error(error, HCCL_DIRECT_STATUS_SUCCESS, "create", "host-only session created"); return HCCL_DIRECT_STATUS_SUCCESS; } catch (...) { set_error(error, HCCL_DIRECT_STATUS_INTERNAL_ERROR, "create", "exception contained at C ABI boundary"); return HCCL_DIRECT_STATUS_INTERNAL_ERROR; } }
extern "C" hccl_direct_status_t hccl_direct_session_configure(hccl_direct_session_t *s, const hccl_direct_session_config_t *c, hccl_direct_error_t *e) { return (!s || !c) ? (set_error(e, HCCL_DIRECT_STATUS_INVALID_ARGUMENT, "configure", "null argument"), HCCL_DIRECT_STATUS_INVALID_ARGUMENT) : retired(s) ? (set_error(e, HCCL_DIRECT_STATUS_INVALID_STATE, "configure", "destroyed session"), HCCL_DIRECT_STATUS_INVALID_STATE) : s->impl.configure(*c, e); }
extern "C" hccl_direct_status_t hccl_direct_session_preflight(hccl_direct_session_t *s, int32_t present, hccl_direct_error_t *e) { return (!s || retired(s)) ? HCCL_DIRECT_STATUS_INVALID_STATE : s->impl.preflight(present, e); }
extern "C" hccl_direct_status_t hccl_direct_session_request_execution(hccl_direct_session_t *s, int32_t real, hccl_direct_error_t *e) { return (!s || retired(s)) ? (set_error(e, HCCL_DIRECT_STATUS_INVALID_STATE, "request_execution", "destroyed session"), HCCL_DIRECT_STATUS_INVALID_STATE) : s->impl.execution(real, e); }
extern "C" hccl_direct_status_t hccl_direct_session_model_acquire_lease(hccl_direct_session_t *s, hccl_direct_error_t *e) { return (!s || retired(s)) ? HCCL_DIRECT_STATUS_INVALID_STATE : s->impl.acquire_model_lease(e); }
extern "C" hccl_direct_status_t hccl_direct_session_model_cleanup(hccl_direct_session_t *s, hccl_direct_failure_point_t f, hccl_direct_error_t *e) { return (!s || retired(s)) ? HCCL_DIRECT_STATUS_INVALID_STATE : s->impl.model_cleanup(f, e); }
extern "C" hccl_direct_status_t hccl_direct_session_run_model(hccl_direct_session_t *s, hccl_direct_failure_point_t f, hccl_direct_error_t *e) { return (!s || retired(s)) ? HCCL_DIRECT_STATUS_INVALID_STATE : s->impl.run_model(f, e); }
extern "C" hccl_direct_status_t hccl_direct_session_destroy(hccl_direct_session_t *s, hccl_direct_error_t *e) { if (!s) { set_error(e, HCCL_DIRECT_STATUS_INVALID_ARGUMENT, "destroy", "null session"); return HCCL_DIRECT_STATUS_INVALID_ARGUMENT; } if (retired(s)) { set_error(e, HCCL_DIRECT_STATUS_INVALID_STATE, "destroy", "double destroy rejected"); return HCCL_DIRECT_STATUS_INVALID_STATE; } const auto status = s->impl.destroy(e); if (status == HCCL_DIRECT_STATUS_SUCCESS) { remember_retired(s); delete s; } return status; }
extern "C" hccl_direct_status_t hccl_direct_session_verify_owner(const hccl_direct_session_t *s, int32_t d, hccl_direct_error_t *e) { return (!s || retired(s)) ? HCCL_DIRECT_STATUS_INVALID_STATE : s->impl.verify_owner(d, e); }
extern "C" hccl_direct_session_state_t hccl_direct_session_state(const hccl_direct_session_t *s) { return !s || retired(s) ? HCCL_DIRECT_SESSION_DESTROYED : s->impl.state(); }
extern "C" hccl_direct_status_t hccl_direct_session_first_error(const hccl_direct_session_t *s, hccl_direct_error_t *e) { if (!s || !e) return HCCL_DIRECT_STATUS_INVALID_ARGUMENT; *e = s->impl.first_error(); return e->status; }
extern "C" size_t hccl_direct_session_cleanup_count(const hccl_direct_session_t *s) { return s ? s->impl.cleanup_count() : 0; }
extern "C" hccl_direct_cleanup_action_t hccl_direct_session_cleanup_action(const hccl_direct_session_t *s, size_t i) { return s ? s->impl.cleanup_action(i) : HCCL_DIRECT_CLEANUP_RUNTIME_LEASE; }
extern "C" size_t hccl_direct_session_cleanup_error_count(const hccl_direct_session_t *s) { return s ? s->impl.cleanup_error_count() : 0; }
extern "C" uint32_t hccl_direct_runtime_lease_count(void) { return g_runtime_leases; }

extern "C" hccl_direct_status_t hccl_direct_calculate_capacity(hccl_direct_primitive_t p, uint64_t count, uint32_t ranks, hccl_direct_dtype_t dtype, hccl_direct_reduce_op_t op, hccl_direct_capacity_t *out, hccl_direct_error_t *error) {
    if (!out || ranks <= 1 || count > std::numeric_limits<size_t>::max() || dtype_size(dtype) == 0 || (p == HCCL_DIRECT_ALL_GATHER ? op != HCCL_DIRECT_REDUCE_NONE : op == HCCL_DIRECT_REDUCE_NONE)) { set_error(error, HCCL_DIRECT_STATUS_INVALID_ARGUMENT, "calculate_capacity", "invalid primitive, dtype, op, rank count, or output"); return HCCL_DIRECT_STATUS_INVALID_ARGUMENT; }
    size_t in_elements = static_cast<size_t>(count), out_elements = in_elements, bytes = 0;
    if (p == HCCL_DIRECT_ALL_GATHER) { if (!multiply(in_elements, ranks, &out_elements)) { set_error(error, HCCL_DIRECT_STATUS_OVERFLOW, "calculate_capacity", "allgather output element overflow"); return HCCL_DIRECT_STATUS_OVERFLOW; } }
    else if (p == HCCL_DIRECT_REDUCE_SCATTER) { if (!multiply(in_elements, ranks, &in_elements)) { set_error(error, HCCL_DIRECT_STATUS_OVERFLOW, "calculate_capacity", "reducescatter input element overflow"); return HCCL_DIRECT_STATUS_OVERFLOW; } }
    else if (p != HCCL_DIRECT_ALL_REDUCE) { set_error(error, HCCL_DIRECT_STATUS_INVALID_ARGUMENT, "calculate_capacity", "unknown primitive"); return HCCL_DIRECT_STATUS_INVALID_ARGUMENT; }
    if (!multiply(in_elements, dtype_size(dtype), &bytes)) { set_error(error, HCCL_DIRECT_STATUS_OVERFLOW, "calculate_capacity", "input byte overflow"); return HCCL_DIRECT_STATUS_OVERFLOW; } out->input_bytes_per_rank = bytes;
    if (!multiply(out_elements, dtype_size(dtype), &bytes)) { set_error(error, HCCL_DIRECT_STATUS_OVERFLOW, "calculate_capacity", "output byte overflow"); return HCCL_DIRECT_STATUS_OVERFLOW; }
    *out = {static_cast<uint64_t>(in_elements), static_cast<uint64_t>(out_elements), out->input_bytes_per_rank, bytes, dtype_size(dtype)}; set_error(error, HCCL_DIRECT_STATUS_SUCCESS, "calculate_capacity", "capacity contract computed"); return HCCL_DIRECT_STATUS_SUCCESS;
}

extern "C" const char *hccl_direct_status_string(hccl_direct_status_t s) { switch (s) { case HCCL_DIRECT_STATUS_SUCCESS: return "success"; case HCCL_DIRECT_STATUS_INVALID_ARGUMENT: return "invalid_argument"; case HCCL_DIRECT_STATUS_INVALID_STATE: return "invalid_state"; case HCCL_DIRECT_STATUS_BUILD_ONLY: return "build_only"; case HCCL_DIRECT_STATUS_NO_DEVICE_EXPECTED: return "no_device_expected"; case HCCL_DIRECT_STATUS_HARDWARE_BLOCKED: return "hardware_blocked"; case HCCL_DIRECT_STATUS_CONFIGURATION_ERROR: return "configuration_error"; case HCCL_DIRECT_STATUS_OVERFLOW: return "overflow"; case HCCL_DIRECT_STATUS_OWNERSHIP_VIOLATION: return "ownership_violation"; case HCCL_DIRECT_STATUS_INJECTED_FAILURE: return "injected_failure"; default: return "internal_error"; } }
extern "C" const char *hccl_direct_session_state_string(hccl_direct_session_state_t s) { static const char *names[] = {"created", "configured", "preflight_checked", "no_device_expected", "runtime_ready", "device_ready", "context_ready", "stream_ready", "comm_ready", "buffers_ready", "collective_submitted", "synchronized", "completed", "cleaning", "destroyed", "failed"}; return s <= HCCL_DIRECT_SESSION_FAILED ? names[s] : "unknown_state"; }
