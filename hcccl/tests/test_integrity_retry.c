#include "hccl_algorithms.h"
#include "hccl_comm.h"
#include "internal/integrity_transport.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>


static int tests_run;
static int tests_failed;

#define CHECK(name, condition) do { \
    tests_run++; \
    if (condition) { printf("  PASS %s\n", name); } \
    else { printf("  FAIL %s\n", name); tests_failed++; } \
} while (0)


static hcclIntegrityMetadata identity(void)
{
    hcclIntegrityMetadata value;
    memset(&value, 0, sizeof(value));
    value.transfer_id = 7;
    value.sequence_id = 2;
    value.chunk_id = 2;
    return value;
}


static hcclIntegrityResult run_fault(
    hcclIntegrityFault fault, uint32_t max_retries,
    uint32_t fault_until_attempt, hcclResult_t* rc_out)
{
    const unsigned char source[] = "integrity-payload";
    unsigned char destination[sizeof(source)];
    hcclIntegrityConfig config = hccl_integrity_default_config();
    hcclIntegrityMetadata metadata = identity();
    hcclIntegrityResult result;
    config.fault = fault;
    config.max_retries = max_retries;
    config.fault_until_attempt = fault_until_attempt;
    config.corruption_offset = 3;
    *rc_out = hccl_integrity_execute(
        source, destination, sizeof(source), &metadata, &config, &result);
    return result;
}


static void test_crc_vectors(void)
{
    const char vector[] = "123456789";
    unsigned char unaligned[] = {0, 1, 2, 3, 4, 5, 6};
    CHECK("CRC32 known vector", hccl_crc32(vector, 9) == UINT32_C(0xCBF43926));
    CHECK("CRC32 empty", hccl_crc32(NULL, 0) == 0);
    CHECK("CRC32 one byte", hccl_crc32("a", 1) == UINT32_C(0xE8B7BE43));
    CHECK("CRC32 non-aligned deterministic", hccl_crc32(unaligned, sizeof(unaligned)) == hccl_crc32(unaligned, sizeof(unaligned)));
}


static void test_clean_and_recovery(void)
{
    hcclResult_t rc;
    hcclIntegrityResult clean = run_fault(HCCL_FAULT_NONE, 3, 0, &rc);
    CHECK("clean transfer no retry", rc == HCCL_SUCCESS && clean.attempt_count == 1 && clean.retransmitted_bytes == 0 && !clean.recovered);

    {
        hcclIntegrityResult bit = run_fault(HCCL_FAULT_BIT_FLIP, 3, 0, &rc);
        CHECK("bit corruption detected and recovered", rc == HCCL_SUCCESS && bit.attempt_count == 2 && bit.corruption_detected && bit.recovered);
        CHECK("single retry byte accounting", bit.retransmitted_bytes == sizeof("integrity-payload"));
    }
    {
        hcclIntegrityResult byte = run_fault(HCCL_FAULT_BYTE_FLIP, 3, 0, &rc);
        CHECK("byte corruption recovered", rc == HCCL_SUCCESS && byte.attempt_count == 2 && byte.corruption_detected);
    }
    {
        hcclIntegrityResult tamper = run_fault(HCCL_FAULT_CRC_TAMPER, 3, 0, &rc);
        CHECK("CRC tamper recovered", rc == HCCL_SUCCESS && tamper.attempt_count == 2 && tamper.corruption_detected);
    }
}


static void test_exhaustion_and_timeout(void)
{
    hcclResult_t rc;
    hcclIntegrityResult exhausted = run_fault(HCCL_FAULT_BIT_FLIP, 3, 3, &rc);
    CHECK("repeated corruption retry exhausted", rc == HCCL_ERR_CRC_MISMATCH && exhausted.classification == HCCL_FAILURE_TERMINAL && exhausted.failure_reason == HCCL_REASON_RETRY_EXHAUSTED);
    CHECK("attempt bound", exhausted.attempt_count == 4);
    CHECK("exhausted retransmitted bytes", exhausted.retransmitted_bytes == 3 * sizeof("integrity-payload"));

    {
        hcclIntegrityResult recovered = run_fault(HCCL_FAULT_LOGICAL_TIMEOUT, 2, 0, &rc);
        CHECK("logical timeout recovered", rc == HCCL_SUCCESS && recovered.attempt_count == 2 && recovered.timed_out && recovered.recovered);
    }
    {
        hcclIntegrityResult terminal = run_fault(HCCL_FAULT_LOGICAL_TIMEOUT, 2, 2, &rc);
        CHECK("logical timeout terminal", rc == HCCL_ERR_TIMEOUT && terminal.failure_reason == HCCL_REASON_RETRY_EXHAUSTED && terminal.attempt_count == 3);
    }
}


static void test_failure_classification(void)
{
    hcclResult_t rc;
    hcclIntegrityResult invalid = run_fault(HCCL_FAULT_INVALID_INPUT, 3, 3, &rc);
    CHECK("invalid input non-retryable", rc == HCCL_ERR_INVALID_ARG && invalid.classification == HCCL_FAILURE_NON_RETRYABLE && invalid.attempt_count == 0);
    {
        hcclIntegrityResult no_path = run_fault(HCCL_FAULT_NO_ALTERNATE_PATH, 3, 3, &rc);
        CHECK("no-path terminal without blind retry", rc == HCCL_ERR_TOPOLOGY && no_path.classification == HCCL_FAILURE_TERMINAL && no_path.attempt_count == 0);
    }
    {
        hcclIntegrityResult transient = run_fault(HCCL_FAULT_TRANSIENT_TRANSFER, 2, 0, &rc);
        CHECK("transient transfer retryable and recovered", rc == HCCL_SUCCESS && transient.attempt_count == 2 && transient.recovered);
    }
}


static void test_sequence_errors(void)
{
    const hcclIntegrityFault faults[] = {
        HCCL_FAULT_DUPLICATE_SEQUENCE,
        HCCL_FAULT_MISSING_CHUNK,
        HCCL_FAULT_REORDERED_SEQUENCE
    };
    size_t index;
    for (index = 0; index < sizeof(faults) / sizeof(faults[0]); index++) {
        hcclResult_t rc;
        hcclIntegrityResult result = run_fault(faults[index], 3, 0, &rc);
        CHECK("sequence error terminal", rc == HCCL_ERR_COMM_FAILURE && result.classification == HCCL_FAILURE_TERMINAL && !result.sequence_valid && result.attempt_count == 1);
    }
}


static void test_chunked_large_payload(void)
{
    const size_t length = 2U * 1024U * 1024U + 17U;
    unsigned char* payload = (unsigned char*)malloc(length);
    hcclIntegrityResult result;
    hcclResult_t rc;
    if (payload == NULL) {
        CHECK("large chunk allocation", 0);
        return;
    }
    memset(payload, 0x5A, length);
    hccl_integrity_runtime_reset();
    rc = hccl_integrity_verify_chunked(payload, length, 1024U * 1024U, 9, &result);
    CHECK("logical large chunked integrity", rc == HCCL_SUCCESS && hccl_integrity_runtime_stats().chunks_verified == 3);
    free(payload);
}


static hcclComm_t make_comm(int32_t ranks)
{
    int32_t ids[8];
    hcclComm_t comm = NULL;
    int32_t rank;
    for (rank = 0; rank < ranks; rank++) ids[rank] = rank;
    return hcclCommInit(&comm, ranks, ids) == HCCL_SUCCESS ? comm : NULL;
}


static void test_sparse_collective_crc_retry_crosscheck(void)
{
    float send[256] = {0};
    float recv[1024] = {0};
    hcclComm_t comm = make_comm(4);
    hcclIntegrityConfig config = hccl_integrity_default_config();
    hcclIntegrityRuntimeStats stats;
    int rank;
    int correct = comm != NULL;
    for (rank = 0; rank < 4; rank++) send[(size_t)rank * 64U + (size_t)rank] = (float)(rank + 1);
    config.fault = HCCL_FAULT_BIT_FLIP;
    config.fault_until_attempt = 0;
    hccl_integrity_runtime_reset();
    hccl_integrity_test_configure(&config);
    if (correct) correct = hcclAllGather(send, recv, 64, HCCL_FP32, comm) == HCCL_SUCCESS;
    hccl_integrity_test_clear();
    for (rank = 0; rank < 4 && correct; rank++) {
        correct = memcmp(recv + (size_t)rank * 256U, send, sizeof(send)) == 0;
    }
    stats = hccl_integrity_runtime_stats();
    CHECK("sparse payload CRC retry integration", correct && stats.retry_attempts >= 1 && stats.crc_mismatches >= 1);
    if (comm != NULL) hcclCommDestroy(comm);
}


int main(void)
{
    test_crc_vectors();
    test_clean_and_recovery();
    test_exhaustion_and_timeout();
    test_failure_classification();
    test_sequence_errors();
    test_chunked_large_payload();
    test_sparse_collective_crc_retry_crosscheck();
    printf("integrity/retry tests: %d run, %d failed\n", tests_run, tests_failed);
    return tests_failed == 0 ? 0 : 1;
}
