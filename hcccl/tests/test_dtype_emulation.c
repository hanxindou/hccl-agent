/**
 * @file    test_dtype_emulation.c
 * @brief   FP16/BF16 CPU software emulation tests.
 */

#include "hccl_algorithms.h"
#include "hccl_comm.h"
#include <stdio.h>
#include <stdint.h>

static int tests_run = 0;
static int tests_pass = 0;
static int tests_fail = 0;

#define TEST(name) do { tests_run++; printf("  %-52s ", name); } while (0)
#define PASS() do { printf("PASS\n"); tests_pass++; } while (0)
#define FAIL(msg) do { printf("FAIL - %s\n", msg); tests_fail++; } while (0)

static hcclComm_t make_comm(int32_t n)
{
    int32_t ids[16];
    hcclComm_t comm = NULL;
    for (int32_t i = 0; i < n; i++) ids[i] = i;
    if (hcclCommInit(&comm, n, ids) != HCCL_SUCCESS) return NULL;
    return comm;
}

static int is_nan16(uint16_t value)
{
    return (value & 0x7C00U) == 0x7C00U && (value & 0x03FFU) != 0;
}

static int run_allreduce_u16(
    hcclDataType_t dtype,
    hcclRedOp_t op,
    const uint16_t* inputs,
    uint16_t expected,
    int expect_nan
)
{
    hcclComm_t comm = make_comm(4);
    uint16_t recv = 0;

    if (comm == NULL) {
        FAIL("comm init failed");
        return 0;
    }

    for (int32_t rank = 0; rank < 4; rank++) {
        hcclSetRank(comm, rank);
        hcclAllReduce(&inputs[rank], &recv, 1, dtype, op, comm);
    }
    for (int32_t rank = 0; rank < 4; rank++) {
        hcclResult_t rc;
        hcclSetRank(comm, rank);
        recv = 0;
        rc = hcclAllReduce(&inputs[rank], &recv, 1, dtype, op, comm);
        if (rc != HCCL_SUCCESS) {
            hcclCommDestroy(comm);
            FAIL("expected HCCL_SUCCESS");
            return 0;
        }
        if (expect_nan) {
            if (!is_nan16(recv)) {
                hcclCommDestroy(comm);
                FAIL("expected FP16 NaN");
                return 0;
            }
        } else if (recv != expected) {
            hcclCommDestroy(comm);
            FAIL("unexpected encoded result");
            return 0;
        }
    }

    hcclCommDestroy(comm);
    return 1;
}

static void test_fp16_allreduce_ops(void)
{
    TEST("FP16 AllReduce SUM/MAX/MIN and NaN");

    uint16_t values[4] = {0x3E00U, 0xC000U, 0x0000U, 0x4400U};
    uint16_t nan_values[4] = {0x7E00U, 0x3C00U, 0x4000U, 0x4200U};

    if (!run_allreduce_u16(HCCL_FP16, HCCL_SUM, values, 0x4300U, 0)) return;
    if (!run_allreduce_u16(HCCL_FP16, HCCL_MAX, values, 0x4400U, 0)) return;
    if (!run_allreduce_u16(HCCL_FP16, HCCL_MIN, values, 0xC000U, 0)) return;
    if (!run_allreduce_u16(HCCL_FP16, HCCL_SUM, nan_values, 0, 1)) return;

    PASS();
}

static void test_bf16_allreduce_ops(void)
{
    TEST("BF16 AllReduce SUM/MAX/MIN");

    uint16_t values[4] = {0x3FC0U, 0xC000U, 0x0000U, 0x4080U};

    if (!run_allreduce_u16(HCCL_BF16, HCCL_SUM, values, 0x4060U, 0)) return;
    if (!run_allreduce_u16(HCCL_BF16, HCCL_MAX, values, 0x4080U, 0)) return;
    if (!run_allreduce_u16(HCCL_BF16, HCCL_MIN, values, 0xC000U, 0)) return;

    PASS();
}

static void test_fp16_allgather_preserves_encoded_values(void)
{
    TEST("FP16 AllGather preserves encoded values");

    hcclComm_t comm = make_comm(4);
    uint16_t send[8] = {
        0x3C00U, 0x4000U,
        0x4200U, 0x4400U,
        0xC000U, 0x0000U,
        0x3800U, 0x7C00U
    };
    uint16_t recv[32] = {0};

    if (comm == NULL) {
        FAIL("comm init failed");
        return;
    }
    if (hcclAllGather(send, recv, 2, HCCL_FP16, comm) != HCCL_SUCCESS) {
        hcclCommDestroy(comm);
        FAIL("expected HCCL_SUCCESS");
        return;
    }
    for (int32_t dst = 0; dst < 4; dst++) {
        for (int32_t src = 0; src < 4; src++) {
            for (int32_t elem = 0; elem < 2; elem++) {
                size_t out_idx = ((size_t)dst * 4U + (size_t)src) * 2U + (size_t)elem;
                size_t in_idx = (size_t)src * 2U + (size_t)elem;
                if (recv[out_idx] != send[in_idx]) {
                    hcclCommDestroy(comm);
                    FAIL("AllGather output mismatch");
                    return;
                }
            }
        }
    }

    hcclCommDestroy(comm);
    PASS();
}

static void test_reducescatter_dtype_sum(void)
{
    TEST("FP16/BF16 ReduceScatter SUM");

    hcclComm_t comm = make_comm(4);
    uint16_t send_fp16[16];
    uint16_t recv_fp16[4] = {0};
    uint16_t send_bf16[16];
    uint16_t recv_bf16[4] = {0};

    if (comm == NULL) {
        FAIL("comm init failed");
        return;
    }
    for (int i = 0; i < 16; i++) {
        send_fp16[i] = 0x3C00U;
        send_bf16[i] = 0x3F80U;
    }

    if (hcclReduceScatter(send_fp16, recv_fp16, 1, HCCL_FP16, HCCL_SUM, comm)
        != HCCL_SUCCESS) {
        hcclCommDestroy(comm);
        FAIL("FP16 ReduceScatter failed");
        return;
    }
    if (hcclReduceScatter(send_bf16, recv_bf16, 1, HCCL_BF16, HCCL_SUM, comm)
        != HCCL_SUCCESS) {
        hcclCommDestroy(comm);
        FAIL("BF16 ReduceScatter failed");
        return;
    }
    for (int i = 0; i < 4; i++) {
        if (recv_fp16[i] != 0x4400U || recv_bf16[i] != 0x4080U) {
            hcclCommDestroy(comm);
            FAIL("ReduceScatter encoded result mismatch");
            return;
        }
    }

    hcclCommDestroy(comm);
    PASS();
}

int main(void)
{
    printf("\n");
    printf("============================================\n");
    printf(" test_dtype_emulation - FP16/BF16 CPU emulation\n");
    printf("============================================\n\n");

    test_fp16_allreduce_ops();
    test_bf16_allreduce_ops();
    test_fp16_allgather_preserves_encoded_values();
    test_reducescatter_dtype_sum();

    printf("\n");
    printf("============================================\n");
    printf(" Results: %d run, %d passed, %d failed\n",
           tests_run, tests_pass, tests_fail);
    printf("============================================\n\n");

    return tests_fail > 0 ? 1 : 0;
}
