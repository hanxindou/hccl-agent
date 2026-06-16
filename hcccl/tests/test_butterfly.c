/**
 * @file    test_butterfly.c
 * @brief   Unit tests for butterfly_allreduce CPU simulation.
 */

#include "hccl_algorithms.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

static int tests_run  = 0;
static int tests_pass = 0;
static int tests_fail = 0;

#define TEST(name)  do { tests_run++; printf("  %-52s ", name); } while (0)
#define PASS()      do { printf("PASS\n"); tests_pass++; } while (0)
#define FAIL(msg)   do { printf("FAIL — %s\n", msg); tests_fail++; } while (0)

#define EPS  0.0001f

/* ------------------------------------------------------------------ */
/*  Helper                                                             */
/* ------------------------------------------------------------------ */

static float run_one(hcclComm_t comm, int32_t rank, float input,
                     float *result_out)
{
    hcclSetRank(comm, rank);
    float recv = -999.0f;
    butterfly_allreduce(&input, &recv, 1, HCCL_FP32, HCCL_SUM, comm);
    if (result_out) *result_out = recv;
    return recv;
}

/* ------------------------------------------------------------------ */
/*  4 ranks [1,2,3,4] → 10                                            */
/* ------------------------------------------------------------------ */

static void test_butterfly_4_ranks(void)
{
    TEST("4 ranks [1,2,3,4] → all get 10");

    int32_t ids[] = {0,1,2,3};
    hcclComm_t comm = NULL;
    hcclCommInit(&comm, 4, ids);

    float inputs[]  = {1,2,3,4};
    float results[4];

    for (int i = 0; i < 4; i++) run_one(comm, i, inputs[i], NULL);
    for (int i = 0; i < 4; i++) results[i] = run_one(comm, i, inputs[i], NULL);

    int ok = 1;
    for (int i = 0; i < 4; i++)
        if (fabsf(results[i] - 10.0f) > EPS) { ok = 0; break; }

    if (ok) PASS(); else FAIL("expected all 10.0");
    hcclCommDestroy(comm);
}

/* ------------------------------------------------------------------ */
/*  8 ranks [1..8] → 36                                               */
/* ------------------------------------------------------------------ */

static void test_butterfly_8_ranks(void)
{
    TEST("8 ranks [1..8] → all get 36");

    int32_t ids[] = {0,1,2,3,4,5,6,7};
    hcclComm_t comm = NULL;
    hcclCommInit(&comm, 8, ids);

    float inputs[8], results[8];
    for (int i = 0; i < 8; i++) inputs[i] = (float)(i+1);

    for (int i = 0; i < 8; i++) run_one(comm, i, inputs[i], NULL);
    for (int i = 0; i < 8; i++) results[i] = run_one(comm, i, inputs[i], NULL);

    int ok = 1;
    for (int i = 0; i < 8; i++)
        if (fabsf(results[i] - 36.0f) > EPS) { ok = 0; break; }

    if (ok) PASS(); else FAIL("expected all 36.0");
    hcclCommDestroy(comm);
}

/* ------------------------------------------------------------------ */
/*  NULL args                                                          */
/* ------------------------------------------------------------------ */

static void test_null_sendbuf(void)
{
    TEST("NULL send_buf → INVALID_ARG");
    int32_t ids[] = {0};  hcclComm_t c = NULL;
    hcclCommInit(&c, 1, ids);  hcclSetRank(c, 0);
    float r;
    hcclResult_t rc = butterfly_allreduce(NULL, &r, 1, HCCL_FP32, HCCL_SUM, c);
    if (rc == HCCL_ERR_INVALID_ARG) PASS(); else FAIL("expected INVALID_ARG");
    hcclCommDestroy(c);
}

static void test_null_recvbuf(void)
{
    TEST("NULL recv_buf → INVALID_ARG");
    int32_t ids[] = {0};  hcclComm_t c = NULL;
    hcclCommInit(&c, 1, ids);  hcclSetRank(c, 0);
    float s = 1;
    if (butterfly_allreduce(&s, NULL, 1, HCCL_FP32, HCCL_SUM, c)
        == HCCL_ERR_INVALID_ARG) PASS(); else FAIL("expected INVALID_ARG");
    hcclCommDestroy(c);
}

/* ------------------------------------------------------------------ */
/*  Unsupported type / op                                              */
/* ------------------------------------------------------------------ */

static void test_fp16_rejected(void)
{
    TEST("FP16 → NOT_SUPPORTED");
    int32_t ids[] = {0};  hcclComm_t c = NULL;
    hcclCommInit(&c, 1, ids);  hcclSetRank(c, 0);
    float s=1, r;
    if (butterfly_allreduce(&s, &r, 1, HCCL_FP16, HCCL_SUM, c)
        == HCCL_ERR_NOT_SUPPORTED) PASS(); else FAIL("expected NOT_SUPPORTED");
    hcclCommDestroy(c);
}

static void test_prod_rejected(void)
{
    TEST("PROD → NOT_SUPPORTED");
    int32_t ids[] = {0};  hcclComm_t c = NULL;
    hcclCommInit(&c, 1, ids);  hcclSetRank(c, 0);
    float s=1, r;
    if (butterfly_allreduce(&s, &r, 1, HCCL_FP32, HCCL_PROD, c)
        == HCCL_ERR_NOT_SUPPORTED) PASS(); else FAIL("expected NOT_SUPPORTED");
    hcclCommDestroy(c);
}

/* ------------------------------------------------------------------ */
/*  Driver                                                             */
/* ------------------------------------------------------------------ */

int main(void)
{
    printf("\n============================================\n");
    printf(" test_butterfly — Butterfly AllReduce\n");
    printf("============================================\n\n");

    test_butterfly_4_ranks();
    test_butterfly_8_ranks();
    test_null_sendbuf();
    test_null_recvbuf();
    test_fp16_rejected();
    test_prod_rejected();

    printf("\n============================================\n");
    printf(" Results: %d run, %d passed, %d failed\n",
           tests_run, tests_pass, tests_fail);
    printf("============================================\n\n");
    return tests_fail > 0 ? 1 : 0;
}
