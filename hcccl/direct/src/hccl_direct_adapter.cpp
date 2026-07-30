#include "hccl_direct_adapter.h"

#include <cstdint>
#include <new>
#include <type_traits>

#include <acl/acl_rt.h>
#include <hccl/hccl.h>
#include <hccl/hccl_comm.h>

namespace {

using ExpectedAllReduce = HcclResult (*)(void *, void *, uint64_t, HcclDataType,
                                         HcclReduceOp, HcclComm, aclrtStream);
using ExpectedAllGather = HcclResult (*)(void *, void *, uint64_t, HcclDataType,
                                         HcclComm, aclrtStream);
using ExpectedReduceScatter = HcclResult (*)(void *, void *, uint64_t, HcclDataType,
                                              HcclReduceOp, HcclComm, aclrtStream);
using ExpectedCommInit = HcclResult (*)(const char *, uint32_t, HcclComm *);
using ExpectedCommDestroy = HcclResult (*)(HcclComm);
using ExpectedAclInit = aclError (*)(const char *);
using ExpectedAclFinalize = aclError (*)();
using ExpectedSetDevice = aclError (*)(int32_t);
using ExpectedCreateContext = aclError (*)(aclrtContext *, int32_t);
using ExpectedDestroyContext = aclError (*)(aclrtContext);
using ExpectedCreateStream = aclError (*)(aclrtStream *);
using ExpectedDestroyStream = aclError (*)(aclrtStream);
using ExpectedSynchronizeStream = aclError (*)(aclrtStream);
using ExpectedMalloc = aclError (*)(void **, size_t, aclrtMemMallocPolicy);
using ExpectedFree = aclError (*)(void *);
using ExpectedMemcpy = aclError (*)(void *, size_t, const void *, size_t, aclrtMemcpyKind);

static_assert(std::is_same<decltype(&HcclAllReduce), ExpectedAllReduce>::value,
              "CANN HcclAllReduce signature drifted");
static_assert(std::is_same<decltype(&HcclAllGather), ExpectedAllGather>::value,
              "CANN HcclAllGather signature drifted");
static_assert(std::is_same<decltype(&HcclReduceScatter), ExpectedReduceScatter>::value,
              "CANN HcclReduceScatter signature drifted");
static_assert(std::is_same<decltype(&HcclCommInitClusterInfo), ExpectedCommInit>::value,
              "CANN HcclCommInitClusterInfo signature drifted");
static_assert(std::is_same<decltype(&HcclCommDestroy), ExpectedCommDestroy>::value,
              "CANN HcclCommDestroy signature drifted");
static_assert(std::is_same<decltype(&aclInit), ExpectedAclInit>::value,
              "CANN aclInit signature drifted");
static_assert(std::is_same<decltype(&aclFinalize), ExpectedAclFinalize>::value,
              "CANN aclFinalize signature drifted");
static_assert(std::is_same<decltype(&aclrtSetDevice), ExpectedSetDevice>::value,
              "CANN aclrtSetDevice signature drifted");
static_assert(std::is_same<decltype(&aclrtCreateContext), ExpectedCreateContext>::value,
              "CANN aclrtCreateContext signature drifted");
static_assert(std::is_same<decltype(&aclrtDestroyContext), ExpectedDestroyContext>::value,
              "CANN aclrtDestroyContext signature drifted");
static_assert(std::is_same<decltype(&aclrtCreateStream), ExpectedCreateStream>::value,
              "CANN aclrtCreateStream signature drifted");
static_assert(std::is_same<decltype(&aclrtDestroyStream), ExpectedDestroyStream>::value,
              "CANN aclrtDestroyStream signature drifted");
static_assert(std::is_same<decltype(&aclrtSynchronizeStream), ExpectedSynchronizeStream>::value,
              "CANN aclrtSynchronizeStream signature drifted");
static_assert(std::is_same<decltype(&aclrtMalloc), ExpectedMalloc>::value,
              "CANN aclrtMalloc signature drifted");
static_assert(std::is_same<decltype(&aclrtFree), ExpectedFree>::value,
              "CANN aclrtFree signature drifted");
static_assert(std::is_same<decltype(&aclrtMemcpy), ExpectedMemcpy>::value,
              "CANN aclrtMemcpy signature drifted");

class DirectSession final {
public:
    DirectSession() noexcept = default;
    ~DirectSession() noexcept { release_owned_handles(); }

    DirectSession(const DirectSession &) = delete;
    DirectSession &operator=(const DirectSession &) = delete;

    hccl_direct_session_state_t state() const noexcept { return state_; }

private:
    void release_owned_handles() noexcept {
        // G2-F-2 skeleton only: no ACL/HCCL function is called here. Future
        // G2-F-4 must replace this with reverse-order, return-code-preserving cleanup.
        recv_buffer_ = nullptr;
        send_buffer_ = nullptr;
        comm_ = nullptr;
        stream_ = nullptr;
        context_ = nullptr;
        runtime_lease_ = false;
        state_ = HCCL_DIRECT_SESSION_RELEASED;
    }

    bool runtime_lease_ = false;
    aclrtContext context_ = nullptr;
    aclrtStream stream_ = nullptr;
    HcclComm comm_ = nullptr;
    void *send_buffer_ = nullptr;
    void *recv_buffer_ = nullptr;
    hccl_direct_session_state_t state_ = HCCL_DIRECT_SESSION_NEW;
};

void set_error(hccl_direct_error_t *error, hccl_direct_status_t status,
               const char *api, const char *message) noexcept {
    if (error != nullptr) {
        error->status = status;
        error->acl_error = 0;
        error->hccl_result = 0;
        error->api = api;
        error->message = message;
    }
}

}  // namespace

struct hccl_direct_session {
    DirectSession impl;
};

extern "C" hccl_direct_status_t hccl_direct_session_create(
    hccl_direct_session_t **session, hccl_direct_error_t *error) {
    try {
        if (session == nullptr) {
            set_error(error, HCCL_DIRECT_STATUS_INVALID_ARGUMENT,
                      "hccl_direct_session_create", "session output must not be null");
            return HCCL_DIRECT_STATUS_INVALID_ARGUMENT;
        }
        *session = nullptr;
        set_error(error, HCCL_DIRECT_STATUS_BUILD_ONLY, "hccl_direct_session_create",
                  "G2-F-2 is compile-only and does not acquire runtime resources");
        return HCCL_DIRECT_STATUS_BUILD_ONLY;
    } catch (const std::bad_alloc &) {
        set_error(error, HCCL_DIRECT_STATUS_INTERNAL_ERROR, "hccl_direct_session_create",
                  "host allocation failure");
        return HCCL_DIRECT_STATUS_INTERNAL_ERROR;
    } catch (...) {
        set_error(error, HCCL_DIRECT_STATUS_INTERNAL_ERROR, "hccl_direct_session_create",
                  "C++ exception contained at C ABI boundary");
        return HCCL_DIRECT_STATUS_INTERNAL_ERROR;
    }
}

extern "C" hccl_direct_status_t hccl_direct_session_destroy(
    hccl_direct_session_t *session, hccl_direct_error_t *error) {
    try {
        delete session;
        set_error(error, HCCL_DIRECT_STATUS_SUCCESS, "hccl_direct_session_destroy", "host state released");
        return HCCL_DIRECT_STATUS_SUCCESS;
    } catch (...) {
        set_error(error, HCCL_DIRECT_STATUS_INTERNAL_ERROR, "hccl_direct_session_destroy",
                  "C++ exception contained at C ABI boundary");
        return HCCL_DIRECT_STATUS_INTERNAL_ERROR;
    }
}

extern "C" hccl_direct_session_state_t hccl_direct_session_state(
    const hccl_direct_session_t *session) {
    try {
        return session == nullptr ? HCCL_DIRECT_SESSION_RELEASED : session->impl.state();
    } catch (...) {
        return HCCL_DIRECT_SESSION_RELEASED;
    }
}

extern "C" const char *hccl_direct_status_string(hccl_direct_status_t status) {
    switch (status) {
        case HCCL_DIRECT_STATUS_SUCCESS:
            return "success";
        case HCCL_DIRECT_STATUS_INVALID_ARGUMENT:
            return "invalid_argument";
        case HCCL_DIRECT_STATUS_INVALID_STATE:
            return "invalid_state";
        case HCCL_DIRECT_STATUS_BUILD_ONLY:
            return "build_only";
        case HCCL_DIRECT_STATUS_INTERNAL_ERROR:
            return "internal_error";
        default:
            return "unknown_status";
    }
}
