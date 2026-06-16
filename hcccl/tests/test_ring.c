/**
 * @file    test_ring.c
 * @brief   Unit tests for ring_allreduce CPU simulation.
 *
 * Build & run (from hcccl/):
 *   mkdir -p build && cd build && cmake .. && make
 *   ./test_ring
 */

#include "hccl_algorithms.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

static int tests_run  = 0;
static int tests_pass = 0;
static int tests_fail = 0;

#define TEST(name)  do {                                   \
    tests_run++;                                           \
    printf("  %-52s ", name);                              \
} while (0)

#define PASS()  do {                                       \
    printf("PASS\n");                                      \
    tests_pass++;                                          \
} while (0)

#define FAIL(msg)  do {                                    \
    printf("FAIL — %s\n", msg);                            \
    tests_fail++;                                          \
} while (0)

/* tolerance for float comparison */
#define EPS  0.0001f

/* ------------------------------------------------------------------ */
/*  Helper: create comm, set rank, call allreduce, return result      */
/* ------------------------------------------------------------------ */

static float run_one_rank(hcclComm_t comm, int32_t rank,
                          float input, float* result_out)
{
    hcclSetRank(comm, rank);
    float recv = -999.0f;
    ring_allreduce(&input, &recv, 1, HCCL_FP32, HCCL_SUM, comm);
    if (result_out) *result_out = recv;
    return recv;
}

/* ------------------------------------------------------------------ */
/*  Test 1: 4 ranks, values 1/2/3/4  →  sum = 10                     */
/* ------------------------------------------------------------------ */

static void test_ring_4_ranks(void)
{
    TEST("4 ranks [1,2,3,4] → all get 10");

    int32_t ids[] = {0, 1, 2, 3};
    hcclComm_t comm = NULL;
    hcclCommInit(&comm, 4, ids);

    float inputs[]  = {1.0f, 2.0f, 3.0f, 4.0f};
    float results[4];

    /* Pass 1 — submit all values (last call triggers simulation). */
    for (int i = 0; i < 4; i++) {
        run_one_rank(comm, i, inputs[i], NULL);
    }

    /* Pass 2 — retrieve all results (simulation runs again, all correct). */
    for (int i = 0; i < 4; i++) {
        results[i] = run_one_rank(comm, i, inputs[i], NULL);
    }

    int ok = 1;
    for (int i = 0; i < 4; i++) {
        if (fabsf(results[i] - 10.0f) > EPS) {
            ok = 0;
            break;
        }
    }

    if (ok) { PASS(); } else { FAIL("expected all 10.0"); }

    hcclCommDestroy(comm);
}

/* ------------------------------------------------------------------ */
/*  Test 2: 8 ranks, values 1..8  →  sum = 36                        */
/* ------------------------------------------------------------------ */

static void test_ring_8_ranks(void)
{
    TEST("8 ranks [1..8] → all get 36");

    int32_t ids[] = {0, 1, 2, 3, 4, 5, 6, 7};
    hcclComm_t comm = NULL;
    hcclCommInit(&comm, 8, ids);

    float inputs[8];
    float results[8];
    for (int i = 0; i < 8; i++) inputs[i] = (float)(i + 1);

    for (int i = 0; i < 8; i++) {
        run_one_rank(comm, i, inputs[i], NULL);
    }
    for (int i = 0; i < 8; i++) {
        results[i] = run_one_rank(comm, i, inputs[i], NULL);
    }

    int ok = 1;
    for (int i = 0; i < 8; i++) {
        if (fabsf(results[i] - 36.0f) > EPS) { ok = 0; break; }
    }

    if (ok) { PASS(); } else { FAIL("expected all 36.0"); }

    hcclCommDestroy(comm);
}

/* ------------------------------------------------------------------ */
/*  Test 3: unsupported data type → HCCL_ERR_NOT_SUPPORTED            */
/* ------------------------------------------------------------------ */

static void test_rejects_unsupported_dtype(void)
{
    TEST("FP16 data type → HCCL_ERR_NOT_SUPPORTED");

    int32_t ids[] = {0, 1};
    hcclComm_t comm = NULL;
    hcclCommInit(&comm, 2, ids);
    hcclSetRank(comm, 0);

    float send = 1.0f, recv = 0.0f;
    hcclResult_t rc = ring_allreduce(&send, &recv, 1,
                                     HCCL_FP16, HCCL_SUM, comm);

    if (rc == HCCL_ERR_NOT_SUPPORTED) { PASS(); }
    else { FAIL("expected HCCL_ERR_NOT_SUPPORTED"); }

    hcclCommDestroy(comm);
}

/* ------------------------------------------------------------------ */
/*  Test 4: unsupported ReduceOp → HCCL_ERR_NOT_SUPPORTED             */
/* ------------------------------------------------------------------ */

static void test_rejects_unsupported_op(void)
{
    TEST("PROD ReduceOp → HCCL_ERR_NOT_SUPPORTED");

    int32_t ids[] = {0, 1};
    hcclComm_t comm = NULL;
    hcclCommInit(&comm, 2, ids);
    hcclSetRank(comm, 0);

    float send = 1.0f, recv = 0.0f;
    hcclResult_t rc = ring_allreduce(&send, &recv, 1,
                                     HCCL_FP32, HCCL_PROD, comm);

    if (rc == HCCL_ERR_NOT_SUPPORTED) { PASS(); }
    else { FAIL("expected HCCL_ERR_NOT_SUPPORTED"); }

    hcclCommDestroy(comm);
}

/* ------------------------------------------------------------------ */
/*  Test 5: NULL args                                                  */
/* ------------------------------------------------------------------ */

static void test_rejects_null_sendbuf(void)
{
    TEST("NULL send_buf → HCCL_ERR_INVALID_ARG");

    int32_t ids[] = {0};
    hcclComm_t comm = NULL;
    hcclCommInit(&comm, 1, ids);
    hcclSetRank(comm, 0);

    float recv = 0.0f;
    hcclResult_t rc = ring_allreduce(NULL, &recv, 1,
                                     HCCL_FP32, HCCL_SUM, comm);

    if (rc == HCCL_ERR_INVALID_ARG) { PASS(); }
    else { FAIL("expected HCCL_ERR_INVALID_ARG"); }

    hcclCommDestroy(comm);
}

static void test_rejects_null_recvbuf(void)
{
    TEST("NULL recv_buf → HCCL_ERR_INVALID_ARG");

    int32_t ids[] = {0};
    hcclComm_t comm = NULL;
    hcclCommInit(&comm, 1, ids);
    hcclSetRank(comm, 0);

    float send = 1.0f;
    hcclResult_t rc = ring_allreduce(&send, NULL, 1,
                                     HCCL_FP32, HCCL_SUM, comm);

    if (rc == HCCL_ERR_INVALID_ARG) { PASS(); }
    else { FAIL("expected HCCL_ERR_INVALID_ARG"); }

    hcclCommDestroy(comm);
}

/* ------------------------------------------------------------------ */
/*  Driver                                                            */
/* ------------------------------------------------------------------ */

int main(void)
{
    printf("\n");
    printf("============================================\n");
    printf(" test_ring — Ring AllReduce CPU simulation\n");
    printf("============================================\n\n");

    test_ring_4_ranks();
    test_ring_8_ranks();
    test_rejects_unsupported_dtype();
    test_rejects_unsupported_op();
    test_rejects_null_sendbuf();
    test_rejects_null_recvbuf();

    printf("\n");
    printf("============================================\n");
    printf(" Results: %d run, %d passed, %d failed\n",
           tests_run, tests_pass, tests_fail);
    printf("============================================\n\n");

    return tests_fail > 0 ? 1 : 0;
}
