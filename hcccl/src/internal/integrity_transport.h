#ifndef HCCL_INTERNAL_INTEGRITY_TRANSPORT_H
#define HCCL_INTERNAL_INTEGRITY_TRANSPORT_H

#include "hccl_comm.h"

#include <stddef.h>
#include <stdint.h>

#if defined(__GNUC__) || defined(__clang__)
#define HCCL_INTEGRITY_INTERNAL __attribute__((visibility("hidden")))
#else
#define HCCL_INTEGRITY_INTERNAL
#endif

typedef enum {
    HCCL_FAULT_NONE = 0,
    HCCL_FAULT_BIT_FLIP,
    HCCL_FAULT_BYTE_FLIP,
    HCCL_FAULT_CRC_TAMPER,
    HCCL_FAULT_LOGICAL_TIMEOUT,
    HCCL_FAULT_TRANSIENT_TRANSFER,
    HCCL_FAULT_DUPLICATE_SEQUENCE,
    HCCL_FAULT_MISSING_CHUNK,
    HCCL_FAULT_REORDERED_SEQUENCE,
    HCCL_FAULT_INVALID_INPUT,
    HCCL_FAULT_NO_ALTERNATE_PATH
} hcclIntegrityFault;

typedef enum {
    HCCL_FAILURE_NONE = 0,
    HCCL_FAILURE_RETRYABLE,
    HCCL_FAILURE_NON_RETRYABLE,
    HCCL_FAILURE_TERMINAL
} hcclFailureClassification;

typedef enum {
    HCCL_REASON_NONE = 0,
    HCCL_REASON_CRC_MISMATCH,
    HCCL_REASON_LOGICAL_TIMEOUT,
    HCCL_REASON_TRANSIENT_TRANSFER_FAILURE,
    HCCL_REASON_INVALID_ARGUMENT,
    HCCL_REASON_RETRY_EXHAUSTED,
    HCCL_REASON_NO_ALTERNATE_PATH,
    HCCL_REASON_UNRECOVERABLE_INTEGRITY_FAILURE,
    HCCL_REASON_DUPLICATE_SEQUENCE,
    HCCL_REASON_MISSING_CHUNK,
    HCCL_REASON_REORDERED_SEQUENCE
} hcclFailureReason;

typedef struct {
    uint64_t transfer_id;
    uint64_t sequence_id;
    uint64_t chunk_id;
    uint32_t attempt;
    size_t payload_length;
    uint32_t crc32;
} hcclIntegrityMetadata;

typedef struct {
    uint32_t max_retries;
    uint64_t logical_timeout_ticks;
    uint64_t retry_backoff_ticks;
    hcclIntegrityFault fault;
    uint32_t fault_until_attempt;
    size_t corruption_offset;
    uint64_t expected_sequence_id;
    uint64_t observed_sequence_id;
} hcclIntegrityConfig;

typedef struct {
    hcclResult_t result_code;
    hcclFailureClassification classification;
    hcclFailureReason failure_reason;
    hcclIntegrityMetadata metadata;
    uint32_t attempt_count;
    size_t retransmitted_bytes;
    uint64_t start_tick;
    uint64_t deadline_tick;
    uint64_t completion_tick;
    int timed_out;
    int corruption_detected;
    int sequence_valid;
    int recovered;
} hcclIntegrityResult;

typedef struct {
    uint64_t transfers;
    uint64_t chunks_verified;
    uint64_t retry_attempts;
    uint64_t crc_mismatches;
    uint64_t logical_timeouts;
    uint64_t sequence_errors;
    size_t retransmitted_bytes;
    hcclResult_t last_result;
    hcclFailureReason last_reason;
} hcclIntegrityRuntimeStats;

HCCL_INTEGRITY_INTERNAL uint32_t hccl_crc32(const void* data, size_t length);
HCCL_INTEGRITY_INTERNAL hcclIntegrityConfig hccl_integrity_default_config(void);
HCCL_INTEGRITY_INTERNAL hcclResult_t hccl_integrity_execute(
    const void* source, void* destination, size_t length,
    const hcclIntegrityMetadata* identity,
    const hcclIntegrityConfig* config,
    hcclIntegrityResult* result);
HCCL_INTEGRITY_INTERNAL hcclResult_t hccl_integrity_verify_chunked(
    const void* source, size_t length, size_t chunk_bytes,
    uint64_t transfer_id, hcclIntegrityResult* last_result);
HCCL_INTEGRITY_INTERNAL void hccl_integrity_test_configure(
    const hcclIntegrityConfig* config);
HCCL_INTEGRITY_INTERNAL void hccl_integrity_test_clear(void);
HCCL_INTEGRITY_INTERNAL void hccl_integrity_runtime_reset(void);
HCCL_INTEGRITY_INTERNAL hcclIntegrityRuntimeStats hccl_integrity_runtime_stats(void);
HCCL_INTEGRITY_INTERNAL const char* hccl_failure_classification_name(
    hcclFailureClassification classification);
HCCL_INTEGRITY_INTERNAL const char* hccl_failure_reason_name(
    hcclFailureReason reason);

#endif
