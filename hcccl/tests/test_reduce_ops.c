/**
 * @file    test_reduce_ops.c
 * @brief   FP32 ReduceOp correctness baseline for CPU_SIM collectives.
 */

#include "hccl_algorithms.h"
#include "hccl_comm.h"
#include <math.h>
#include <stdio.h>

static int tests_run = 0;
static int tests_pass = 0;
static int tests_fail = 0;

#define TEST(name) do { tests_run++; printf("  %-52s ", name); } while (0)
#define PASS() do { printf("PASS\n"); tests_pass++; } while (0)
#define FAIL(msg) do { printf("FAIL - %s\n", msg); tests_fail++; } while (0)

#define EPS 0.0001f

typedef hcclResult_t (*allreduce_fn_t)(
    const void*, void*, size_t, hcclDataType_t, hcclRedOp_t, hcclComm_t
);

static hcclComm_t make_comm(int32_t n)
{
    int32_t ids[16];
    hcclComm_t comm = NULL;
    for (int32_t i = 0; i < n; i++) ids[i] = i;
    if (hcclCommInit(&comm, n, ids) != HCCL_SUCCESS) return NULL;
    return comm;
}

static float reduce_reference(const float* values, int32_t n, hcclRedOp_t op)
{
    float result = values[0];
    for (int32_t i = 1; i < n; i++) {
        if (op == HCCL_PROD) result *= values[i];
        else if (op == HCCL_MAX) result = result > values[i] ? result : values[i];
        else if (op == HCCL_MIN) result = result < values[i] ? result : values[i];
        else result += values[i];
    }
    return result;
}

static int check_allreduce(allreduce_fn_t fn, int32_t n, hcclRedOp_t op,
                           const float* inputs, float expected)
{
    hcclComm_t comm = make_comm(n);
    float recv = -999.0f;

    if (comm == NULL) {
        FAIL("comm init failed");
        return 0;
    }

    for (int32_t rank = 0; rank < n; rank++) {
        hcclSetRank(comm, rank);
        fn(&inputs[rank], &recv, 1, HCCL_FP32, op, comm);
    }

    for (int32_t rank = 0; rank < n; rank++) {
        hcclResult_t rc;
        hcclSetRank(comm, rank);
        recv = -999.0f;
        rc = fn(&inputs[rank], &recv, 1, HCCL_FP32, op, comm);
        if (rc != HCCL_SUCCESS) {
            hcclCommDestroy(comm);
            FAIL("expected HCCL_SUCCESS");
            return 0;
        }
        if (isinf(expected)) {
            if (!isinf(recv)) {
                hcclCommDestroy(comm);
                FAIL("expected Inf");
                return 0;
            }
        } else if (fabsf(recv - expected) > EPS) {
            hcclCommDestroy(comm);
            FAIL("unexpected reduced value");
            return 0;
        }
    }

    hcclCommDestroy(comm);
    return 1;
}

static void test_allreduce_ops_for_algorithm(
    const char* name,
    allreduce_fn_t fn
)
{
    TEST(name);

    float values[] = {1.5f, -2.0f, 0.0f, 4.0f};
    hcclRedOp_t ops[] = {HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN};

    for (int i = 0; i < 4; i++) {
        float expected = reduce_reference(values, 4, ops[i]);
        if (!check_allreduce(fn, 4, ops[i], values, expected)) return;
    }

    PASS();
}

static void test_allreduce_overflow_behavior(void)
{
    TEST("AllReduce PROD overflow becomes Inf");

    float values[] = {1.0e20f, 1.0e20f, 2.0f, 1.0f};
    if (check_allreduce(hcclAllReduce, 4, HCCL_PROD, values, INFINITY)) {
        PASS();
    }
}

static void test_reducescatter_reduce_ops(void)
{
    TEST("ReduceScatter FP32 SUM/PROD/MAX/MIN");

    int32_t n = 4;
    size_t count = 2;
    float send[32];
    float recv[8];
    hcclRedOp_t ops[] = {HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN};
    hcclComm_t comm = make_comm(n);

    if (comm == NULL) {
        FAIL("comm init failed");
        return;
    }

    for (int32_t src = 0; src < n; src++) {
        for (int32_t dst = 0; dst < n; dst++) {
            for (size_t elem = 0; elem < count; elem++) {
                size_t idx = ((size_t)src * (size_t)n + (size_t)dst) * count + elem;
                send[idx] = (float)((src - 2) * (dst + 1)) + (float)elem * 0.5f;
                if (src == 1 && dst == 2 && elem == 0) send[idx] = 0.0f;
            }
        }
    }

    for (int op_idx = 0; op_idx < 4; op_idx++) {
        hcclRedOp_t op = ops[op_idx];
        hcclResult_t rc = hcclReduceScatter(send, recv, count, HCCL_FP32, op, comm);
        if (rc != HCCL_SUCCESS) {
            hcclCommDestroy(comm);
            FAIL("expected HCCL_SUCCESS");
            return;
        }

        for (int32_t dst = 0; dst < n; dst++) {
            for (size_t elem = 0; elem < count; elem++) {
                float values[4];
                float expected;
                size_t out_idx = (size_t)dst * count + elem;
                for (int32_t src = 0; src < n; src++) {
                    size_t in_idx =
                        ((size_t)src * (size_t)n + (size_t)dst) * count + elem;
                    values[src] = send[in_idx];
                }
                expected = reduce_reference(values, n, op);
                if (fabsf(recv[out_idx] - expected) > EPS) {
                    hcclCommDestroy(comm);
                    FAIL("ReduceScatter mismatch");
                    return;
                }
            }
        }
    }

    hcclCommDestroy(comm);
    PASS();
}

static void test_unknown_reduce_op(void)
{
    TEST("unknown ReduceOp remains NOT_SUPPORTED");

    hcclComm_t comm = make_comm(4);
    float send = 1.0f;
    float recv = -123.0f;
    hcclResult_t rc;

    if (comm == NULL) {
        FAIL("comm init failed");
        return;
    }

    rc = hcclAllReduce(&send, &recv, 1, HCCL_FP32, (hcclRedOp_t)99, comm);
    if (rc != HCCL_ERR_NOT_SUPPORTED) {
        hcclCommDestroy(comm);
        FAIL("AllReduce should reject unknown ReduceOp");
        return;
    }

    hcclCommDestroy(comm);
    PASS();
}

int main(void)
{
    printf("\n");
    printf("============================================\n");
    printf(" test_reduce_ops - FP32 ReduceOp baseline\n");
    printf("============================================\n\n");

    test_allreduce_ops_for_algorithm("hcclAllReduce SUM/PROD/MAX/MIN", hcclAllReduce);
    test_allreduce_ops_for_algorithm("Ring SUM/PROD/MAX/MIN", ring_allreduce);
    test_allreduce_ops_for_algorithm("Butterfly SUM/PROD/MAX/MIN", butterfly_allreduce);
    test_allreduce_ops_for_algorithm("Mesh SUM/PROD/MAX/MIN", mesh_allreduce);
    test_allreduce_ops_for_algorithm("NHR SUM/PROD/MAX/MIN", nhr_allreduce);
    test_allreduce_ops_for_algorithm("Fat-Tree SUM/PROD/MAX/MIN", fattree_allreduce);
    test_allreduce_overflow_behavior();
    test_reducescatter_reduce_ops();
    test_unknown_reduce_op();

    printf("\n");
    printf("============================================\n");
    printf(" Results: %d run, %d passed, %d failed\n",
           tests_run, tests_pass, tests_fail);
    printf("============================================\n\n");

    return tests_fail > 0 ? 1 : 0;
}
