/**
 * @file    test_api_wrappers.c
 * @brief   Unit tests for standard HCCL wrapper symbols.
 */

#include "hccl_comm.h"
#include <math.h>
#include <stdio.h>

static int tests_run = 0;
static int tests_pass = 0;
static int tests_fail = 0;

#define TEST(name) do {                                    \
    tests_run++;                                           \
    printf("  %-52s ", name);                              \
} while (0)

#define PASS() do {                                        \
    printf("PASS\n");                                     \
    tests_pass++;                                          \
} while (0)

#define FAIL(msg) do {                                     \
    printf("FAIL - %s\n", msg);                            \
    tests_fail++;                                          \
} while (0)

#define EPS 0.0001f

static hcclComm_t make_comm(int32_t n)
{
    int32_t ids[8];
    hcclComm_t comm = NULL;
    for (int32_t i = 0; i < n; i++) {
        ids[i] = i;
    }
    if (hcclCommInit(&comm, n, ids) != HCCL_SUCCESS) {
        return NULL;
    }
    return comm;
}

static void test_allreduce_wrapper_uses_cpu_path(void)
{
    TEST("hcclAllReduce wrapper computes 4-rank SUM");

    hcclComm_t comm = make_comm(4);
    float inputs[] = {1.0f, 2.0f, 3.0f, 4.0f};
    float results[4] = {0};

    if (comm == NULL) {
        FAIL("comm init failed");
        return;
    }

    for (int32_t rank = 0; rank < 4; rank++) {
        hcclSetRank(comm, rank);
        float recv = -999.0f;
        hcclAllReduce(&inputs[rank], &recv, 1, HCCL_FP32, HCCL_SUM, comm);
    }

    for (int32_t rank = 0; rank < 4; rank++) {
        hcclSetRank(comm, rank);
        float recv = -999.0f;
        hcclResult_t rc = hcclAllReduce(
            &inputs[rank], &recv, 1, HCCL_FP32, HCCL_SUM, comm
        );
        if (rc != HCCL_SUCCESS) {
            hcclCommDestroy(comm);
            FAIL("hcclAllReduce did not return success");
            return;
        }
        results[rank] = recv;
    }

    for (int32_t rank = 0; rank < 4; rank++) {
        if (fabsf(results[rank] - 10.0f) > EPS) {
            hcclCommDestroy(comm);
            FAIL("expected all ranks to receive 10.0");
            return;
        }
    }

    hcclCommDestroy(comm);
    PASS();
}

static void test_allreduce_invalid_args(void)
{
    TEST("hcclAllReduce invalid args and unsupported types");

    hcclComm_t comm = make_comm(1);
    float send = 1.0f;
    float recv = -123.0f;

    if (comm == NULL) {
        FAIL("comm init failed");
        return;
    }

    if (hcclAllReduce(NULL, &recv, 1, HCCL_FP32, HCCL_SUM, comm)
        != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("NULL send_buf should be invalid");
        return;
    }
    if (hcclAllReduce(&send, NULL, 1, HCCL_FP32, HCCL_SUM, comm)
        != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("NULL recv_buf should be invalid");
        return;
    }
    if (hcclAllReduce(&send, &recv, 0, HCCL_FP32, HCCL_SUM, comm)
        != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("zero count should be invalid");
        return;
    }
    if (hcclAllReduce(&send, &recv, 1, HCCL_FP16, HCCL_SUM, comm)
        != HCCL_ERR_NOT_SUPPORTED) {
        hcclCommDestroy(comm);
        FAIL("FP16 should be unsupported");
        return;
    }
    if (hcclAllReduce(&send, &recv, 1, HCCL_FP32, HCCL_PROD, comm)
        != HCCL_ERR_NOT_SUPPORTED) {
        hcclCommDestroy(comm);
        FAIL("PROD should be unsupported");
        return;
    }
    if (hcclAllReduce(&send, &recv, 1, HCCL_FP32, HCCL_SUM, NULL)
        != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("NULL comm should be invalid");
        return;
    }

    hcclCommDestroy(comm);
    PASS();
}

static void test_allgather_not_supported(void)
{
    TEST("hcclAllGather returns NOT_SUPPORTED and preserves recv");

    hcclComm_t comm = make_comm(2);
    float send = 1.0f;
    float recv = -77.0f;
    hcclResult_t rc;

    if (comm == NULL) {
        FAIL("comm init failed");
        return;
    }

    rc = hcclAllGather(&send, &recv, 1, HCCL_FP32, comm);
    if (rc != HCCL_ERR_NOT_SUPPORTED) {
        hcclCommDestroy(comm);
        FAIL("expected NOT_SUPPORTED");
        return;
    }
    if (fabsf(recv - (-77.0f)) > EPS) {
        hcclCommDestroy(comm);
        FAIL("recv buffer was modified");
        return;
    }
    if (hcclAllGather(NULL, &recv, 1, HCCL_FP32, comm)
        != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("NULL send_buf should be invalid");
        return;
    }
    if (hcclAllGather(&send, &recv, 0, HCCL_FP32, comm)
        != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("zero count should be invalid");
        return;
    }

    hcclCommDestroy(comm);
    PASS();
}

static void test_reducescatter_not_supported(void)
{
    TEST("hcclReduceScatter returns NOT_SUPPORTED and preserves recv");

    hcclComm_t comm = make_comm(2);
    float send[2] = {1.0f, 2.0f};
    float recv = -88.0f;
    hcclResult_t rc;

    if (comm == NULL) {
        FAIL("comm init failed");
        return;
    }

    rc = hcclReduceScatter(send, &recv, 1, HCCL_FP32, HCCL_SUM, comm);
    if (rc != HCCL_ERR_NOT_SUPPORTED) {
        hcclCommDestroy(comm);
        FAIL("expected NOT_SUPPORTED");
        return;
    }
    if (fabsf(recv - (-88.0f)) > EPS) {
        hcclCommDestroy(comm);
        FAIL("recv buffer was modified");
        return;
    }
    if (hcclReduceScatter(send, &recv, 1, HCCL_FP32, HCCL_PROD, comm)
        != HCCL_ERR_NOT_SUPPORTED) {
        hcclCommDestroy(comm);
        FAIL("PROD should be unsupported");
        return;
    }
    if (hcclReduceScatter(send, &recv, 0, HCCL_FP32, HCCL_SUM, comm)
        != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("zero count should be invalid");
        return;
    }

    hcclCommDestroy(comm);
    PASS();
}

static void test_broadcast_not_supported(void)
{
    TEST("hcclBroadcast returns NOT_SUPPORTED and preserves recv");

    hcclComm_t comm = make_comm(2);
    float send = 5.0f;
    float recv = -99.0f;
    hcclResult_t rc;

    if (comm == NULL) {
        FAIL("comm init failed");
        return;
    }

    rc = hcclBroadcast(&send, &recv, 1, HCCL_FP32, 0, comm);
    if (rc != HCCL_ERR_NOT_SUPPORTED) {
        hcclCommDestroy(comm);
        FAIL("expected NOT_SUPPORTED");
        return;
    }
    if (fabsf(recv - (-99.0f)) > EPS) {
        hcclCommDestroy(comm);
        FAIL("recv buffer was modified");
        return;
    }
    if (hcclBroadcast(&send, &recv, 1, HCCL_FP32, 3, comm)
        != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("invalid root should be invalid");
        return;
    }
    if (hcclBroadcast(&send, &recv, 0, HCCL_FP32, 0, comm)
        != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("zero count should be invalid");
        return;
    }

    hcclCommDestroy(comm);
    PASS();
}

int main(void)
{
    printf("\n");
    printf("============================================\n");
    printf(" test_api_wrappers - standard C wrappers\n");
    printf("============================================\n\n");

    test_allreduce_wrapper_uses_cpu_path();
    test_allreduce_invalid_args();
    test_allgather_not_supported();
    test_reducescatter_not_supported();
    test_broadcast_not_supported();

    printf("\n");
    printf("============================================\n");
    printf(" Results: %d run, %d passed, %d failed\n",
           tests_run, tests_pass, tests_fail);
    printf("============================================\n\n");

    return tests_fail > 0 ? 1 : 0;
}
