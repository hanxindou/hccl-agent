#include "integrity_transport.h"

#include <stdlib.h>
#include <string.h>


static hcclIntegrityConfig g_test_config;
static int g_test_configured;
static hcclIntegrityRuntimeStats g_runtime_stats;


uint32_t hccl_crc32(const void* data, size_t length)
{
    const unsigned char* bytes = (const unsigned char*)data;
    uint32_t crc = UINT32_C(0xFFFFFFFF);
    size_t index;
    int bit;
    if (data == NULL && length != 0) return 0;
    for (index = 0; index < length; index++) {
        crc ^= bytes[index];
        for (bit = 0; bit < 8; bit++) {
            crc = (crc >> 1) ^ (UINT32_C(0xEDB88320) & (uint32_t)-(int32_t)(crc & 1U));
        }
    }
    return crc ^ UINT32_C(0xFFFFFFFF);
}


hcclIntegrityConfig hccl_integrity_default_config(void)
{
    hcclIntegrityConfig config;
    memset(&config, 0, sizeof(config));
    config.max_retries = 3;
    config.logical_timeout_ticks = 8;
    config.retry_backoff_ticks = 1;
    config.fault = HCCL_FAULT_NONE;
    config.fault_until_attempt = 0;
    config.expected_sequence_id = 0;
    config.observed_sequence_id = 0;
    return config;
}


static int fault_applies(const hcclIntegrityConfig* config, uint32_t attempt)
{
    return config->fault != HCCL_FAULT_NONE && attempt <= config->fault_until_attempt;
}


static void set_failure(
    hcclIntegrityResult* result,
    hcclResult_t code,
    hcclFailureClassification classification,
    hcclFailureReason reason)
{
    result->result_code = code;
    result->classification = classification;
    result->failure_reason = reason;
}


static void record_runtime(const hcclIntegrityResult* result)
{
    g_runtime_stats.transfers++;
    g_runtime_stats.chunks_verified += result->result_code == HCCL_SUCCESS;
    g_runtime_stats.retry_attempts += result->attempt_count > 0 ? result->attempt_count - 1 : 0;
    g_runtime_stats.crc_mismatches += result->corruption_detected;
    g_runtime_stats.logical_timeouts += result->timed_out;
    g_runtime_stats.sequence_errors += !result->sequence_valid;
    g_runtime_stats.retransmitted_bytes += result->retransmitted_bytes;
    g_runtime_stats.last_result = result->result_code;
    g_runtime_stats.last_reason = result->failure_reason;
}


hcclResult_t hccl_integrity_execute(
    const void* source, void* destination, size_t length,
    const hcclIntegrityMetadata* identity,
    const hcclIntegrityConfig* config,
    hcclIntegrityResult* result)
{
    uint32_t attempt;
    int ever_corruption_detected = 0;
    int ever_timed_out = 0;
    if (result == NULL) return HCCL_ERR_INVALID_ARG;
    memset(result, 0, sizeof(*result));
    result->result_code = HCCL_ERR_INVALID_ARG;
    result->classification = HCCL_FAILURE_NON_RETRYABLE;
    result->failure_reason = HCCL_REASON_INVALID_ARGUMENT;
    result->sequence_valid = 1;
    if ((source == NULL && length != 0) || (destination == NULL && length != 0) ||
        identity == NULL || config == NULL || config->logical_timeout_ticks == 0) {
        record_runtime(result);
        return result->result_code;
    }
    result->metadata = *identity;
    result->metadata.payload_length = length;
    result->metadata.crc32 = hccl_crc32(source, length);

    if (config->fault == HCCL_FAULT_INVALID_INPUT) {
        set_failure(result, HCCL_ERR_INVALID_ARG, HCCL_FAILURE_NON_RETRYABLE, HCCL_REASON_INVALID_ARGUMENT);
        record_runtime(result);
        return result->result_code;
    }
    if (config->fault == HCCL_FAULT_NO_ALTERNATE_PATH) {
        set_failure(result, HCCL_ERR_TOPOLOGY, HCCL_FAILURE_TERMINAL, HCCL_REASON_NO_ALTERNATE_PATH);
        record_runtime(result);
        return result->result_code;
    }

    for (attempt = 0; attempt <= config->max_retries; attempt++) {
        uint32_t expected_crc = result->metadata.crc32;
        uint32_t observed_crc;
        int applies = fault_applies(config, attempt);
        result->metadata.attempt = attempt;
        result->attempt_count = attempt + 1;
        result->start_tick = (uint64_t)attempt * (1U + config->retry_backoff_ticks);
        result->deadline_tick = result->start_tick + config->logical_timeout_ticks;
        result->completion_tick = result->start_tick + 1;
        result->timed_out = 0;
        result->corruption_detected = 0;
        result->sequence_valid = 1;
        if (length != 0) memcpy(destination, source, length);

        if (applies && config->fault == HCCL_FAULT_BIT_FLIP && length != 0) {
            ((unsigned char*)destination)[config->corruption_offset % length] ^= 0x01U;
        } else if (applies && config->fault == HCCL_FAULT_BYTE_FLIP && length != 0) {
            ((unsigned char*)destination)[config->corruption_offset % length] ^= 0xFFU;
        } else if (applies && config->fault == HCCL_FAULT_CRC_TAMPER) {
            expected_crc ^= UINT32_C(0x00000001);
        } else if (applies && config->fault == HCCL_FAULT_LOGICAL_TIMEOUT) {
            result->completion_tick = result->deadline_tick + 1;
        } else if (applies && config->fault == HCCL_FAULT_TRANSIENT_TRANSFER) {
            set_failure(result, HCCL_ERR_COMM_FAILURE, HCCL_FAILURE_RETRYABLE, HCCL_REASON_TRANSIENT_TRANSFER_FAILURE);
        } else if (applies && config->fault == HCCL_FAULT_DUPLICATE_SEQUENCE) {
            result->sequence_valid = 0;
            set_failure(result, HCCL_ERR_COMM_FAILURE, HCCL_FAILURE_TERMINAL, HCCL_REASON_DUPLICATE_SEQUENCE);
        } else if (applies && config->fault == HCCL_FAULT_MISSING_CHUNK) {
            result->sequence_valid = 0;
            set_failure(result, HCCL_ERR_COMM_FAILURE, HCCL_FAILURE_TERMINAL, HCCL_REASON_MISSING_CHUNK);
        } else if (applies && config->fault == HCCL_FAULT_REORDERED_SEQUENCE) {
            result->sequence_valid = 0;
            set_failure(result, HCCL_ERR_COMM_FAILURE, HCCL_FAILURE_TERMINAL, HCCL_REASON_REORDERED_SEQUENCE);
        }

        if (result->classification == HCCL_FAILURE_TERMINAL) break;
        if (applies && config->fault == HCCL_FAULT_TRANSIENT_TRANSFER) {
            /* Classification already populated above. */
        } else if (result->completion_tick > result->deadline_tick) {
            result->timed_out = 1;
            ever_timed_out = 1;
            set_failure(result, HCCL_ERR_TIMEOUT, HCCL_FAILURE_RETRYABLE, HCCL_REASON_LOGICAL_TIMEOUT);
        } else {
            observed_crc = hccl_crc32(destination, length);
            if (observed_crc != expected_crc) {
                result->corruption_detected = 1;
                ever_corruption_detected = 1;
                set_failure(result, HCCL_ERR_CRC_MISMATCH, HCCL_FAILURE_RETRYABLE, HCCL_REASON_CRC_MISMATCH);
            } else {
                set_failure(result, HCCL_SUCCESS, HCCL_FAILURE_NONE, HCCL_REASON_NONE);
                result->recovered = attempt > 0;
                result->corruption_detected = ever_corruption_detected;
                result->timed_out = ever_timed_out;
                record_runtime(result);
                return HCCL_SUCCESS;
            }
        }

        if (result->classification != HCCL_FAILURE_RETRYABLE) break;
        if (attempt < config->max_retries) {
            result->retransmitted_bytes += length;
            continue;
        }
        result->classification = HCCL_FAILURE_TERMINAL;
        result->failure_reason = HCCL_REASON_RETRY_EXHAUSTED;
        break;
    }
    result->corruption_detected = ever_corruption_detected;
    result->timed_out = ever_timed_out;
    record_runtime(result);
    return result->result_code;
}


hcclResult_t hccl_integrity_verify_chunked(
    const void* source, size_t length, size_t chunk_bytes,
    uint64_t transfer_id, hcclIntegrityResult* last_result)
{
    const unsigned char* bytes = (const unsigned char*)source;
    hcclIntegrityConfig config = g_test_configured ? g_test_config : hccl_integrity_default_config();
    unsigned char* destination;
    size_t offset = 0;
    uint64_t chunk_id = 0;
    hcclIntegrityResult local_result;
    if ((source == NULL && length != 0) || chunk_bytes == 0) return HCCL_ERR_INVALID_ARG;
    destination = (unsigned char*)malloc(chunk_bytes);
    if (destination == NULL) return HCCL_ERR_INTERNAL;
    do {
        size_t remaining = length - offset;
        size_t current = remaining < chunk_bytes ? remaining : chunk_bytes;
        hcclIntegrityMetadata identity;
        hcclResult_t rc;
        memset(&identity, 0, sizeof(identity));
        identity.transfer_id = transfer_id;
        identity.sequence_id = chunk_id;
        identity.chunk_id = chunk_id;
        config.expected_sequence_id = chunk_id;
        if (config.fault != HCCL_FAULT_DUPLICATE_SEQUENCE &&
            config.fault != HCCL_FAULT_MISSING_CHUNK &&
            config.fault != HCCL_FAULT_REORDERED_SEQUENCE) {
            config.observed_sequence_id = chunk_id;
        }
        rc = hccl_integrity_execute(
            bytes == NULL ? NULL : bytes + offset,
            destination,
            current,
            &identity,
            &config,
            &local_result);
        if (last_result != NULL) *last_result = local_result;
        if (rc != HCCL_SUCCESS) {
            free(destination);
            return rc;
        }
        offset += current;
        chunk_id++;
    } while (offset < length);
    free(destination);
    return HCCL_SUCCESS;
}


void hccl_integrity_test_configure(const hcclIntegrityConfig* config)
{
    if (config == NULL) {
        hccl_integrity_test_clear();
        return;
    }
    g_test_config = *config;
    g_test_configured = 1;
}


void hccl_integrity_test_clear(void)
{
    memset(&g_test_config, 0, sizeof(g_test_config));
    g_test_configured = 0;
}


void hccl_integrity_runtime_reset(void)
{
    memset(&g_runtime_stats, 0, sizeof(g_runtime_stats));
}


hcclIntegrityRuntimeStats hccl_integrity_runtime_stats(void)
{
    return g_runtime_stats;
}


const char* hccl_failure_classification_name(hcclFailureClassification classification)
{
    if (classification == HCCL_FAILURE_RETRYABLE) return "RETRYABLE";
    if (classification == HCCL_FAILURE_NON_RETRYABLE) return "NON_RETRYABLE";
    if (classification == HCCL_FAILURE_TERMINAL) return "TERMINAL";
    return "NONE";
}


const char* hccl_failure_reason_name(hcclFailureReason reason)
{
    switch (reason) {
        case HCCL_REASON_CRC_MISMATCH: return "CRC_MISMATCH";
        case HCCL_REASON_LOGICAL_TIMEOUT: return "LOGICAL_TIMEOUT";
        case HCCL_REASON_TRANSIENT_TRANSFER_FAILURE: return "TRANSIENT_TRANSFER_FAILURE";
        case HCCL_REASON_INVALID_ARGUMENT: return "INVALID_ARGUMENT";
        case HCCL_REASON_RETRY_EXHAUSTED: return "RETRY_EXHAUSTED";
        case HCCL_REASON_NO_ALTERNATE_PATH: return "NO_ALTERNATE_PATH";
        case HCCL_REASON_UNRECOVERABLE_INTEGRITY_FAILURE: return "UNRECOVERABLE_INTEGRITY_FAILURE";
        case HCCL_REASON_DUPLICATE_SEQUENCE: return "DUPLICATE_SEQUENCE";
        case HCCL_REASON_MISSING_CHUNK: return "MISSING_CHUNK";
        case HCCL_REASON_REORDERED_SEQUENCE: return "REORDERED_SEQUENCE";
        default: return "NONE";
    }
}
