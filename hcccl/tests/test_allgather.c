/**
 * @file    test_allgather.c
 * @brief   Unit tests for CPU_SIM AllGather data correctness.
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
    for (int32_t rank = 0; rank < n; rank++) {
        for (size_t elem = 0; elem < count; elem++) {
            send[(size_t)rank * count + elem] =
                (float)(rank * 100 + (int32_t)elem + 1);
        }
    }
}

static int check_reference(const float* recv, const float* send,
                           int32_t n, size_t count)
{
    for (int32_t dst = 0; dst < n; dst++) {
        for (int32_t src = 0; src < n; src++) {
            for (size_t elem = 0; elem < count; elem++) {
                size_t out_idx =
                    ((size_t)dst * (size_t)n + (size_t)src) * count + elem;
                size_t in_idx = (size_t)src * count + elem;
                if (fabsf(recv[out_idx] - send[in_idx]) > EPS) {
                    return 0;
                }
            }
        }
    }
    return 1;
}

static int run_algorithm_case(
    const char* name,
    hcclResult_t (*fn)(const void*, void*, size_t, hcclDataType_t, hcclComm_t),
    int32_t n,
    size_t count
)
{
    size_t input_elems = (size_t)n * count;
    size_t output_elems = (size_t)n * input_elems;
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

    rc = fn(send, recv, count, HCCL_FP32, comm);
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

static void test_ring_case(const char* label, int32_t n, size_t count)
{
    TEST(label);
    if (run_algorithm_case(label, ring_allgather, n, count)) {
        PASS();
    }
}

static void test_butterfly_case(const char* label, int32_t n, size_t count)
{
    TEST(label);
    if (run_algorithm_case(label, butterfly_allgather, n, count)) {
        PASS();
    }
}

static void test_wrapper_case(void)
{
    TEST("hcclAllGather wrapper uses Ring CPU_SIM path");
    if (run_algorithm_case("wrapper", hcclAllGather, 4, 3)) {
        PASS();
    }
}

static void test_ring_and_butterfly_match(void)
{
    TEST("Ring and Butterfly match reference for 8 ranks count 3");

    int32_t n = 8;
    size_t count = 3;
    size_t input_elems = (size_t)n * count;
    size_t output_elems = (size_t)n * input_elems;
    float* send = (float*) malloc(input_elems * sizeof(float));
    float* ring_recv = (float*) malloc(output_elems * sizeof(float));
    float* butterfly_recv = (float*) malloc(output_elems * sizeof(float));
    hcclComm_t comm = make_comm(n);

    if (send == NULL || ring_recv == NULL || butterfly_recv == NULL || comm == NULL) {
        free(send);
        free(ring_recv);
        free(butterfly_recv);
        if (comm != NULL) hcclCommDestroy(comm);
        FAIL("allocation or comm init failed");
        return;
    }

    fill_input(send, n, count);
    if (ring_allgather(send, ring_recv, count, HCCL_FP32, comm) != HCCL_SUCCESS ||
        butterfly_allgather(send, butterfly_recv, count, HCCL_FP32, comm) != HCCL_SUCCESS) {
        free(send);
        free(ring_recv);
        free(butterfly_recv);
        hcclCommDestroy(comm);
        FAIL("algorithm returned error");
        return;
    }

    for (size_t i = 0; i < output_elems; i++) {
        if (fabsf(ring_recv[i] - butterfly_recv[i]) > EPS) {
            free(send);
            free(ring_recv);
            free(butterfly_recv);
            hcclCommDestroy(comm);
            FAIL("outputs differ");
            return;
        }
    }

    free(send);
    free(ring_recv);
    free(butterfly_recv);
    hcclCommDestroy(comm);
    PASS();
}

static void test_invalid_args(void)
{
    TEST("AllGather invalid args and unsupported dtype");

    hcclComm_t comm = make_comm(4);
    float send[4] = {1.0f, 2.0f, 3.0f, 4.0f};
    float recv[16];
    float sentinel = -55.0f;

    if (comm == NULL) {
        FAIL("comm init failed");
        return;
    }

    for (int i = 0; i < 16; i++) recv[i] = sentinel;

    if (ring_allgather(NULL, recv, 1, HCCL_FP32, comm) != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("NULL send should be invalid");
        return;
    }
    if (ring_allgather(send, NULL, 1, HCCL_FP32, comm) != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("NULL recv should be invalid");
        return;
    }
    if (ring_allgather(send, recv, 0, HCCL_FP32, comm) != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("zero count should be invalid");
        return;
    }
    if (ring_allgather(send, recv, 1, HCCL_INT8, comm) != HCCL_ERR_NOT_SUPPORTED) {
        hcclCommDestroy(comm);
        FAIL("INT8 should be unsupported");
        return;
    }
    if (ring_allgather(send, send, 1, HCCL_FP32, comm) != HCCL_ERR_NOT_SUPPORTED) {
        hcclCommDestroy(comm);
        FAIL("in-place layout should be unsupported");
        return;
    }
    if (ring_allgather(send, recv, 1, HCCL_FP32, NULL) != HCCL_ERR_INVALID_ARG) {
        hcclCommDestroy(comm);
        FAIL("NULL comm should be invalid");
        return;
    }
    for (int i = 0; i < 16; i++) {
        if (fabsf(recv[i] - sentinel) > EPS) {
            hcclCommDestroy(comm);
            FAIL("failure path modified recv");
            return;
        }
    }

    hcclCommDestroy(comm);
    PASS();
}

static void test_butterfly_rejects_non_power_of_two(void)
{
    TEST("Butterfly rejects non-power-of-two rank count");

    hcclComm_t comm = make_comm(3);
    float send[3] = {1.0f, 2.0f, 3.0f};
    float recv[9];

    if (comm == NULL) {
        FAIL("comm init failed");
        return;
    }
    for (int i = 0; i < 9; i++) recv[i] = -44.0f;

    if (butterfly_allgather(send, recv, 1, HCCL_FP32, comm)
        == HCCL_ERR_NOT_SUPPORTED &&
        fabsf(recv[0] - (-44.0f)) <= EPS) {
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
    printf(" test_allgather - CPU_SIM AllGather\n");
    printf("============================================\n\n");

    test_ring_case("Ring 1 rank count 1", 1, 1);
    test_ring_case("Ring 2 ranks count 1", 2, 1);
    test_ring_case("Ring 4 ranks count 1", 4, 1);
    test_ring_case("Ring 8 ranks count 1", 8, 1);
    test_ring_case("Ring 16 ranks count 1", 16, 1);
    test_ring_case("Ring 4 ranks count 2", 4, 2);
    test_ring_case("Ring 8 ranks count 3", 8, 3);

    test_butterfly_case("Butterfly 1 rank count 1", 1, 1);
    test_butterfly_case("Butterfly 2 ranks count 1", 2, 1);
    test_butterfly_case("Butterfly 4 ranks count 1", 4, 1);
    test_butterfly_case("Butterfly 8 ranks count 1", 8, 1);
    test_butterfly_case("Butterfly 16 ranks count 1", 16, 1);
    test_butterfly_case("Butterfly 4 ranks count 2", 4, 2);
    test_butterfly_case("Butterfly 8 ranks count 3", 8, 3);

    test_wrapper_case();
    test_ring_and_butterfly_match();
    test_invalid_args();
    test_butterfly_rejects_non_power_of_two();

    printf("\n");
    printf("============================================\n");
    printf(" Results: %d run, %d passed, %d failed\n",
           tests_run, tests_pass, tests_fail);
    printf("============================================\n\n");

    return tests_fail > 0 ? 1 : 0;
}
