#ifndef HCCL_DIRECT_ADAPTER_H
#define HCCL_DIRECT_ADAPTER_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/** Opaque direct-adapter session; it is intentionally unrelated to CPU_SIM handles. */
typedef struct hccl_direct_session hccl_direct_session_t;

/** Stable C-ABI status values for a future direct HCCL adapter. */
typedef enum hccl_direct_status {
    HCCL_DIRECT_STATUS_SUCCESS = 0,
    HCCL_DIRECT_STATUS_INVALID_ARGUMENT = 1,
    HCCL_DIRECT_STATUS_INVALID_STATE = 2,
    HCCL_DIRECT_STATUS_BUILD_ONLY = 3,
    HCCL_DIRECT_STATUS_INTERNAL_ERROR = 4
} hccl_direct_status_t;

/** Lifecycle states exposed without exposing any ACL or HCCL implementation type. */
typedef enum hccl_direct_session_state {
    HCCL_DIRECT_SESSION_NEW = 0,
    HCCL_DIRECT_SESSION_RELEASED = 1
} hccl_direct_session_state_t;

/** Error details preserve future official result codes without importing their ABI into Python. */
typedef struct hccl_direct_error {
    hccl_direct_status_t status;
    int32_t acl_error;
    int32_t hccl_result;
    const char *api;
    const char *message;
} hccl_direct_error_t;

/**
 * Build-only declaration of a future session constructor.
 *
 * G2-F-2 deliberately returns HCCL_DIRECT_STATUS_BUILD_ONLY and never touches
 * ACL, a device, a stream, a communicator, or an official shared library.
 */
hccl_direct_status_t hccl_direct_session_create(
    hccl_direct_session_t **session,
    hccl_direct_error_t *error
);

/** Release only adapter-owned host state; it never performs ACL/HCCL cleanup in G2-F-2. */
hccl_direct_status_t hccl_direct_session_destroy(
    hccl_direct_session_t *session,
    hccl_direct_error_t *error
);

/** Return the adapter state without invoking an official API. */
hccl_direct_session_state_t hccl_direct_session_state(const hccl_direct_session_t *session);

/** Return a stable local status string. */
const char *hccl_direct_status_string(hccl_direct_status_t status);

#ifdef __cplusplus
}
#endif

#endif /* HCCL_DIRECT_ADAPTER_H */
