/**
 * @file    test_reducescatter.c
 * @brief   Unit tests for CPU_SIM ReduceScatter data correctness.
 */

#include "hccl_algorithms.h"
#include "hccl_comm.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

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
    int32_t ids[16];
    hcclComm_t comm = NULL;
    for (int32_t i = 0; i < n; i++) {
        ids[i] = i;
    }
    if (hcclCommInit(&comm, n, ids) != HCCL_SUCCESS) {
        return NULL;
    }
    return comm;
}

static void fill_input(float* send, int32_t n, size_t count)
{
    for (int32_t src = 0; src < n; src++) {
        for (int32_t dst = 0; dst < n; dst++) {
            for (size_t elem = 0; elem < count; elem++) {
                size_t idx =
                    ((size_t)src * (size_t)n + (size_t)dst) * count + elem;
                send[idx] = (float)(src * 1000 + dst * 100 + (int32_t)elem + 1);
            }
        }
    }
}

static int check_reference(const float* recv, const float* send,
                           int32_t n, size_t count)
{
    for (int32_t dst = 0; dst < n; dst++) {
        for (size_t elem = 0; elem < count; elem++) {
            float expected = 0.0f;
            size_t out_idx = (size_t)dst * count + elem;
            for (int32_t src = 0; src < n; src++) {
                size_t in_idx =
                    ((size_t)src * (size_t)n + (size_t)dst) * count + elem;
                expected += send[in_idx];
            }
            if (fabsf(recv[out_idx] - expected) > EPS) {
                return 0;
            }
        }
    }
    return 1;
}

static int run_case(
    const char* name,
    hcclResult_t (*fn)(const void*, void*, size_t, hcclDataType_t,
                       hcclRedOp_t, hcclComm_t),
    int32_t n,
    size_t count
)
{
    size_t input_elems = (size_t)n * (size_t)n * count;
    size_t output_elems = (size_t)n * count;
    float* send = (float*) malloc(input_elems * sizeof(float));
    float* recv = (float*) malloc(output_elems * sizeof(float));
    hcclComm_t comm = make_comm(n);
    hcclResult_t rc;

    if (send == NULL || recv == NULL || comm == NULL) {
        free(send);
        free(recv);
        if (comm != NULL) hcclCommDestroy(comm);
        FAIL("allocation or comm init failed");
        return 0;
    }

    fill_input(send, n, count);
    for (size_t i = 0; i < output_elems; i++) {
        recv[i] = -999.0f;
    }

    rc = fn(send, recv, count, HCCL_FP32, HCCL_SUM, comm);
    if (rc != HCCL_SUCCESS) {
        free(send);
        free(recv);
        hcclCommDestroy(comm);
        FAIL("expected HCCL_SUCCESS");
        return 0;
    }
    if (!check_reference(recv, send, n, count)) {
        free(send);
        free(recv);
        hcclCommDestroy(comm);
        FAIL("output does not match reference");
        return 0;
    }

    free(send);
    free(recv);
    hcclCommDestroy(comm);
    (void)name;
    return 1;
}

static void test_mesh_case(const char* label, int32_t n, size_t count)
{
    TEST(label);
    if (run_case(label, mesh_reducescatter, n, count)) {
        PASS();
    }
}

static void test_wrapper_case(void)
{
    TEST("hcclReduceScatter wrapper uses Mesh CPU_SIM path");
    if (run_case("wrapper", hcclReduceScatter, 4, 3)) {
        PASS();
    }
}

static void test_invalid_args(void)
{
    TEST("ReduceScatter invalid args and unsupported modes");

    hcclComm_t comm = make_comm(4);
    float send[16];
    float recv[4];
    float sentinel = -55.0f;

    if (comm == NULL) {
        FAIL("comm init failed");
        return;
    }
    for (int i = 0; i < 16; i++) send[i] = (float)(i + 1);
    for (int i = 0; i < 4; i++) recv[i] = sentinel;

    if (mesh_reducescatter(NULL, recv, 1, HCCL_FP32, HCCL_SUM, comm)
        != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("NULL send should be invalid");
        return;
    }
    if (mesh_reducescatter(send, NULL, 1, HCCL_FP32, HCCL_SUM, comm)
        != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("NULL recv should be invalid");
        return;
    }
    if (mesh_reducescatter(send, recv, 0, HCCL_FP32, HCCL_SUM, comm)
        != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("zero count should be invalid");
        return;
    }
    if (mesh_reducescatter(send, recv, 1, HCCL_FP16, HCCL_SUM, comm)
        != HCCL_ERR_NOT_SUPPORTED) {
        hcclCommDestroy(comm);
        FAIL("FP16 should be unsupported");
        return;
    }
    if (mesh_reducescatter(send, recv, 1, HCCL_BF16, HCCL_SUM, comm)
        != HCCL_ERR_NOT_SUPPORTED) {
        hcclCommDestroy(comm);
        FAIL("BF16 should be unsupported");
        return;
    }
    if (mesh_reducescatter(send, recv, 1, HCCL_FP32, HCCL_PROD, comm)
        != HCCL_ERR_NOT_SUPPORTED) {
        hcclCommDestroy(comm);
        FAIL("PROD should be unsupported in C2");
        return;
    }
    if (mesh_reducescatter(send, send, 1, HCCL_FP32, HCCL_SUM, comm)
        != HCCL_ERR_NOT_SUPPORTED) {
        hcclCommDestroy(comm);
        FAIL("in-place layout should be unsupported");
        return;
    }
    if (mesh_reducescatter(send, recv, 1, HCCL_FP32, HCCL_SUM, NULL)
        != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("NULL comm should be invalid");
        return;
    }
    for (int i = 0; i < 4; i++) {
        if (fabsf(recv[i] - sentinel) > EPS) {
            hcclCommDestroy(comm);
            FAIL("failure path modified recv");
            return;
        }
    }

    hcclCommDestroy(comm);
    PASS();
}

static void test_legacy_two_rank_scalar_case(void)
{
    TEST("2-rank scalar legacy wrapper remains NOT_SUPPORTED");

    hcclComm_t comm = make_comm(2);
    float send[4] = {1.0f, 2.0f, 3.0f, 4.0f};
    float recv = -88.0f;

    if (comm == NULL) {
        FAIL("comm init failed");
        return;
    }

    if (hcclReduceScatter(send, &recv, 1, HCCL_FP32, HCCL_SUM, comm)
        == HCCL_ERR_NOT_SUPPORTED &&
        fabsf(recv - (-88.0f)) <= EPS) {
        hcclCommDestroy(comm);
        PASS();
        return;
    }

    hcclCommDestroy(comm);
    FAIL("expected NOT_SUPPORTED and preserved recv");
}

int main(void)
{
    printf("\n");
    printf("============================================\n");
    printf(" test_reducescatter - CPU_SIM ReduceScatter\n");
    printf("============================================\n\n");

    test_mesh_case("Mesh 1 rank count 1", 1, 1);
    test_mesh_case("Mesh 4 ranks count 1", 4, 1);
    test_mesh_case("Mesh 8 ranks count 1", 8, 1);
    test_mesh_case("Mesh 16 ranks count 1", 16, 1);
    test_mesh_case("Mesh 4 ranks count 2", 4, 2);
    test_mesh_case("Mesh 8 ranks count 3", 8, 3);
    test_mesh_case("Mesh 16 ranks count 2", 16, 2);
    test_wrapper_case();
    test_invalid_args();
    test_legacy_two_rank_scalar_case();

    printf("\n");
    printf("============================================\n");
    printf(" Results: %d run, %d passed, %d failed\n",
           tests_run, tests_pass, tests_fail);
    printf("============================================\n\n");

    return tests_fail > 0 ? 1 : 0;
}
