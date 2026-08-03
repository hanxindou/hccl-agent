#ifndef HCCL_DIRECT_ADAPTER_H
#define HCCL_DIRECT_ADAPTER_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct hccl_direct_session hccl_direct_session_t;

/* Project-local ABI values; none aliases a CPU_SIM or official HCCL result. */
typedef enum hccl_direct_status {
    HCCL_DIRECT_STATUS_SUCCESS = 0,
    HCCL_DIRECT_STATUS_INVALID_ARGUMENT = 1,
    HCCL_DIRECT_STATUS_INVALID_STATE = 2,
    HCCL_DIRECT_STATUS_BUILD_ONLY = 3,
    HCCL_DIRECT_STATUS_INTERNAL_ERROR = 4,
    HCCL_DIRECT_STATUS_NO_DEVICE_EXPECTED = 5,
    HCCL_DIRECT_STATUS_HARDWARE_BLOCKED = 6,
    HCCL_DIRECT_STATUS_CONFIGURATION_ERROR = 7,
    HCCL_DIRECT_STATUS_OVERFLOW = 8,
    HCCL_DIRECT_STATUS_OWNERSHIP_VIOLATION = 9,
    HCCL_DIRECT_STATUS_INJECTED_FAILURE = 10
} hccl_direct_status_t;

typedef enum hccl_direct_session_state {
    HCCL_DIRECT_SESSION_CREATED = 0,
    HCCL_DIRECT_SESSION_CONFIGURED = 1,
    HCCL_DIRECT_SESSION_PREFLIGHT_CHECKED = 2,
    HCCL_DIRECT_SESSION_NO_DEVICE_EXPECTED = 3,
    HCCL_DIRECT_SESSION_RUNTIME_READY = 4,
    HCCL_DIRECT_SESSION_DEVICE_READY = 5,
    HCCL_DIRECT_SESSION_CONTEXT_READY = 6,
    HCCL_DIRECT_SESSION_STREAM_READY = 7,
    HCCL_DIRECT_SESSION_COMM_READY = 8,
    HCCL_DIRECT_SESSION_BUFFERS_READY = 9,
    HCCL_DIRECT_SESSION_COLLECTIVE_SUBMITTED = 10,
    HCCL_DIRECT_SESSION_SYNCHRONIZED = 11,
    HCCL_DIRECT_SESSION_COMPLETED = 12,
    HCCL_DIRECT_SESSION_CLEANING = 13,
    HCCL_DIRECT_SESSION_DESTROYED = 14,
    HCCL_DIRECT_SESSION_FAILED = 15
} hccl_direct_session_state_t;

typedef enum hccl_direct_rank_mode {
    HCCL_DIRECT_RANK_TABLE = 0,
    HCCL_DIRECT_ROOT_INFO = 1
} hccl_direct_rank_mode_t;

typedef enum hccl_direct_primitive {
    HCCL_DIRECT_ALL_REDUCE = 0,
    HCCL_DIRECT_ALL_GATHER = 1,
    HCCL_DIRECT_REDUCE_SCATTER = 2
} hccl_direct_primitive_t;

typedef enum hccl_direct_dtype {
    HCCL_DIRECT_DTYPE_FP16 = 0,
    HCCL_DIRECT_DTYPE_FP32 = 1,
    HCCL_DIRECT_DTYPE_FP64 = 2,
    HCCL_DIRECT_DTYPE_BF16 = 3
} hccl_direct_dtype_t;

typedef enum hccl_direct_reduce_op {
    HCCL_DIRECT_REDUCE_NONE = 0,
    HCCL_DIRECT_REDUCE_SUM = 1,
    HCCL_DIRECT_REDUCE_PROD = 2,
    HCCL_DIRECT_REDUCE_MAX = 3,
    HCCL_DIRECT_REDUCE_MIN = 4
} hccl_direct_reduce_op_t;

typedef enum hccl_direct_failure_point {
    HCCL_DIRECT_FAILURE_NONE = 0,
    HCCL_DIRECT_FAILURE_RUNTIME_LEASE = 1,
    HCCL_DIRECT_FAILURE_DEVICE_BIND = 2,
    HCCL_DIRECT_FAILURE_CONTEXT_CREATE = 3,
    HCCL_DIRECT_FAILURE_STREAM_CREATE = 4,
    HCCL_DIRECT_FAILURE_COMM_CREATE = 5,
    HCCL_DIRECT_FAILURE_SEND_BUFFER = 6,
    HCCL_DIRECT_FAILURE_RECV_BUFFER = 7,
    HCCL_DIRECT_FAILURE_COLLECTIVE_SUBMIT = 8,
    HCCL_DIRECT_FAILURE_SYNCHRONIZE = 9,
    HCCL_DIRECT_FAILURE_CLEANUP_RECV_BUFFER = 10,
    HCCL_DIRECT_FAILURE_CLEANUP_SEND_BUFFER = 11,
    HCCL_DIRECT_FAILURE_CLEANUP_COMM = 12,
    HCCL_DIRECT_FAILURE_CLEANUP_STREAM = 13,
    HCCL_DIRECT_FAILURE_CLEANUP_CONTEXT = 14,
    HCCL_DIRECT_FAILURE_CLEANUP_DEVICE = 15,
    HCCL_DIRECT_FAILURE_CLEANUP_RUNTIME_LEASE = 16
} hccl_direct_failure_point_t;

typedef enum hccl_direct_cleanup_action {
    HCCL_DIRECT_CLEANUP_RECV_BUFFER = 0,
    HCCL_DIRECT_CLEANUP_SEND_BUFFER = 1,
    HCCL_DIRECT_CLEANUP_COMM = 2,
    HCCL_DIRECT_CLEANUP_STREAM = 3,
    HCCL_DIRECT_CLEANUP_CONTEXT = 4,
    HCCL_DIRECT_CLEANUP_DEVICE = 5,
    HCCL_DIRECT_CLEANUP_RUNTIME_LEASE = 6
} hccl_direct_cleanup_action_t;

typedef struct hccl_direct_error {
    hccl_direct_status_t status;
    int32_t acl_error;
    int32_t hccl_result;
    const char *api;
    const char *message;
} hccl_direct_error_t;

typedef struct hccl_direct_session_config {
    hccl_direct_rank_mode_t rank_mode;
    uint32_t rank_id;
    uint32_t rank_size;
    int32_t device_id;
    const char *rank_table_path;
    uint32_t root_rank;
    uint32_t model_only_test;
} hccl_direct_session_config_t;

typedef struct hccl_direct_capacity {
    uint64_t input_elements_per_rank;
    uint64_t output_elements_per_rank;
    size_t input_bytes_per_rank;
    size_t output_bytes_per_rank;
    size_t dtype_size;
} hccl_direct_capacity_t;

hccl_direct_status_t hccl_direct_session_create(hccl_direct_session_t **session, hccl_direct_error_t *error);
hccl_direct_status_t hccl_direct_session_configure(hccl_direct_session_t *session, const hccl_direct_session_config_t *config, hccl_direct_error_t *error);
hccl_direct_status_t hccl_direct_session_preflight(hccl_direct_session_t *session, int32_t device_present, hccl_direct_error_t *error);
hccl_direct_status_t hccl_direct_session_request_execution(hccl_direct_session_t *session, int32_t explicit_real_device_request, hccl_direct_error_t *error);
hccl_direct_status_t hccl_direct_session_model_acquire_lease(hccl_direct_session_t *session, hccl_direct_error_t *error);
hccl_direct_status_t hccl_direct_session_model_cleanup(hccl_direct_session_t *session, hccl_direct_failure_point_t failure, hccl_direct_error_t *error);
hccl_direct_status_t hccl_direct_session_run_model(hccl_direct_session_t *session, hccl_direct_failure_point_t failure, hccl_direct_error_t *error);
hccl_direct_status_t hccl_direct_session_destroy(hccl_direct_session_t *session, hccl_direct_error_t *error);
hccl_direct_status_t hccl_direct_session_verify_owner(const hccl_direct_session_t *session, int32_t device_id, hccl_direct_error_t *error);
hccl_direct_session_state_t hccl_direct_session_state(const hccl_direct_session_t *session);
hccl_direct_status_t hccl_direct_session_first_error(const hccl_direct_session_t *session, hccl_direct_error_t *error);
size_t hccl_direct_session_cleanup_count(const hccl_direct_session_t *session);
hccl_direct_cleanup_action_t hccl_direct_session_cleanup_action(const hccl_direct_session_t *session, size_t index);
size_t hccl_direct_session_cleanup_error_count(const hccl_direct_session_t *session);
uint32_t hccl_direct_runtime_lease_count(void);
hccl_direct_status_t hccl_direct_calculate_capacity(hccl_direct_primitive_t primitive, uint64_t count, uint32_t rank_size, hccl_direct_dtype_t dtype, hccl_direct_reduce_op_t reduce_op, hccl_direct_capacity_t *capacity, hccl_direct_error_t *error);
const char *hccl_direct_status_string(hccl_direct_status_t status);
const char *hccl_direct_session_state_string(hccl_direct_session_state_t state);

#ifdef __cplusplus
}
#endif

#endif /* HCCL_DIRECT_ADAPTER_H */
