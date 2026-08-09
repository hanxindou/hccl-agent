// G3-B3-E compile/link-only production source path.
//
// THIS SOURCE IS NOT EXECUTED IN HOST-ONLY ACCEPTANCE.  It intentionally
// contains actual official ACL/HCCL call expressions so the frozen 9.1.0
// headers and DSOs can be compile/link audited.  The target has no executable
// entry point, is default-OFF, is not registered with CTest, and is protected
// by an explicit runtime authorization token.

#include <cstddef>
#include <cstdint>

#include <acl/acl_rt.h>
#include <hccl/hccl.h>
#include <hccl/hccl_comm.h>

namespace {

constexpr std::uint64_t kRuntimeAuthorizationToken = UINT64_C(0x47334233454E5055);

enum class Primitive : std::uint32_t {
    kAllReduce = 0,
    kAllGather = 1,
    kReduceScatter = 2,
};

enum class SourceStatus : std::int32_t {
    kSuccess = 0,
    kExecutionGuardActive = 1,
    kInvalidArgument = 2,
    kAclFailure = 3,
    kHcclFailure = 4,
};

struct RuntimeRequest {
    std::uint64_t execution_authorization_token;
    const char *rank_table_path;
    std::uint32_t rank;
    std::int32_t device_id;
    Primitive primitive;
    std::uint64_t count;
    HcclDataType data_type;
    HcclReduceOp reduce_op;
    const void *host_send;
    void *host_recv;
    std::size_t send_bytes;
    std::size_t recv_bytes;
};

struct RuntimeResult {
    SourceStatus status;
    const char *first_failed_api;
    std::int32_t first_acl_error;
    std::int32_t first_hccl_error;
    std::uint32_t cleanup_error_count;
};

void initialize_result(RuntimeResult *result) noexcept {
    result->status = SourceStatus::kSuccess;
    result->first_failed_api = nullptr;
    result->first_acl_error = ACL_SUCCESS;
    result->first_hccl_error = HCCL_SUCCESS;
    result->cleanup_error_count = 0;
}
bool record_acl(RuntimeResult *result, const char *api, aclError error,
                bool cleanup = false) noexcept {
    if (error == ACL_SUCCESS) return true;
    if (cleanup) ++result->cleanup_error_count;
    if (result->first_failed_api == nullptr) {
        result->status = SourceStatus::kAclFailure;
        result->first_failed_api = api;
        result->first_acl_error = error;
    }
    return false;
}

bool record_hccl(RuntimeResult *result, const char *api, HcclResult error,
                 bool cleanup = false) noexcept {
    if (error == HCCL_SUCCESS) return true;
    if (cleanup) ++result->cleanup_error_count;
    if (result->first_failed_api == nullptr) {
        result->status = SourceStatus::kHcclFailure;
        result->first_failed_api = api;
        result->first_hccl_error = error;
    }
    return false;
}

bool valid_request(const RuntimeRequest *request) noexcept {
    return request != nullptr && request->rank_table_path != nullptr &&
           request->host_send != nullptr && request->host_recv != nullptr &&
           request->count > 0 && request->send_bytes > 0 &&
           request->recv_bytes > 0;
}

}  // namespace

#if defined(__GNUC__)
#define HCCL_DIRECT_RUNTIME_SOURCE_HIDDEN __attribute__((visibility("hidden"), used))
#else
#define HCCL_DIRECT_RUNTIME_SOURCE_HIDDEN
#endif

extern "C" HCCL_DIRECT_RUNTIME_SOURCE_HIDDEN std::int32_t
hccl_direct_runtime_source_compile_link_only(const RuntimeRequest *request,
                                             RuntimeResult *result) noexcept {
    if (result == nullptr) return static_cast<std::int32_t>(SourceStatus::kInvalidArgument);
    initialize_result(result);
    if (!valid_request(request)) {
        result->status = SourceStatus::kInvalidArgument;
        result->first_failed_api = "request_validation";
        return static_cast<std::int32_t>(result->status);
    }
    if (request->execution_authorization_token != kRuntimeAuthorizationToken) {
        result->status = SourceStatus::kExecutionGuardActive;
        result->first_failed_api = "runtime_execution_guard";
        return static_cast<std::int32_t>(result->status);
    }

    bool runtime_initialized = false;
    bool device_set = false;
    bool context_created = false;
    bool stream_created = false;
    bool send_allocated = false;
    bool recv_allocated = false;
    bool comm_created = false;
    aclrtContext context = nullptr;
    aclrtStream stream = nullptr;
    void *device_send = nullptr;
    void *device_recv = nullptr;
    HcclComm comm = nullptr;

    do {
        aclError acl_error = aclInit(nullptr);
        if (!record_acl(result, "aclInit", acl_error)) break;
        runtime_initialized = true;

        acl_error = aclrtSetDevice(request->device_id);
        if (!record_acl(result, "aclrtSetDevice", acl_error)) break;
        device_set = true;

        acl_error = aclrtCreateContext(&context, request->device_id);
        if (!record_acl(result, "aclrtCreateContext", acl_error)) break;
        context_created = true;

        acl_error = aclrtCreateStream(&stream);
        if (!record_acl(result, "aclrtCreateStream", acl_error)) break;
        stream_created = true;

        acl_error = aclrtMalloc(&device_send, request->send_bytes,
                                ACL_MEM_MALLOC_HUGE_FIRST);
        if (!record_acl(result, "aclrtMalloc(send)", acl_error)) break;
        send_allocated = true;

        acl_error = aclrtMalloc(&device_recv, request->recv_bytes,
                                ACL_MEM_MALLOC_HUGE_FIRST);
        if (!record_acl(result, "aclrtMalloc(recv)", acl_error)) break;
        recv_allocated = true;

        acl_error = aclrtMemcpy(device_send, request->send_bytes,
                                request->host_send, request->send_bytes,
                                ACL_MEMCPY_HOST_TO_DEVICE);
        if (!record_acl(result, "aclrtMemcpy(host_to_device)", acl_error)) break;

        HcclResult hccl_error = HcclCommInitClusterInfo(
            request->rank_table_path, request->rank, &comm);
        if (!record_hccl(result, "HcclCommInitClusterInfo", hccl_error)) break;
        comm_created = true;

        switch (request->primitive) {
            case Primitive::kAllReduce:
                hccl_error = HcclAllReduce(
                    device_send, device_recv, request->count,
                    request->data_type, request->reduce_op, comm, stream);
                if (!record_hccl(result, "HcclAllReduce", hccl_error)) break;
                break;
            case Primitive::kAllGather:
                hccl_error = HcclAllGather(
                    device_send, device_recv, request->count,
                    request->data_type, comm, stream);
                if (!record_hccl(result, "HcclAllGather", hccl_error)) break;
                break;
            case Primitive::kReduceScatter:
                hccl_error = HcclReduceScatter(
                    device_send, device_recv, request->count,
                    request->data_type, request->reduce_op, comm, stream);
                if (!record_hccl(result, "HcclReduceScatter", hccl_error)) break;
                break;
            default:
                result->status = SourceStatus::kInvalidArgument;
                result->first_failed_api = "primitive_validation";
                break;
        }
        if (result->first_failed_api != nullptr) break;

        acl_error = aclrtSynchronizeStream(stream);
        if (!record_acl(result, "aclrtSynchronizeStream", acl_error)) break;

        acl_error = aclrtMemcpy(request->host_recv, request->recv_bytes,
                                device_recv, request->recv_bytes,
                                ACL_MEMCPY_DEVICE_TO_HOST);
        if (!record_acl(result, "aclrtMemcpy(device_to_host)", acl_error)) break;
    } while (false);

    // Official cleanup is attempted exactly once per acquired resource and in
    // reverse lifecycle order.  Cleanup errors never replace the first error.
    if (comm_created) {
        record_hccl(result, "HcclCommDestroy", HcclCommDestroy(comm), true);
        comm_created = false;
    }
    if (recv_allocated) {
        record_acl(result, "aclrtFree(recv)", aclrtFree(device_recv), true);
        recv_allocated = false;
    }
    if (send_allocated) {
        record_acl(result, "aclrtFree(send)", aclrtFree(device_send), true);
        send_allocated = false;
    }
    if (stream_created) {
        record_acl(result, "aclrtDestroyStream", aclrtDestroyStream(stream), true);
        stream_created = false;
    }
    if (context_created) {
        record_acl(result, "aclrtDestroyContext", aclrtDestroyContext(context), true);
        context_created = false;
    }
    if (device_set) {
        record_acl(result, "aclrtResetDevice", aclrtResetDevice(request->device_id), true);
        device_set = false;
    }
    if (runtime_initialized) {
        record_acl(result, "aclFinalize", aclFinalize(), true);
        runtime_initialized = false;
    }
    return static_cast<std::int32_t>(result->status);
}
