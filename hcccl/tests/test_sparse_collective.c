#include "hccl_algorithms.h"
#include "hccl_comm.h"
#include "internal/sparse_codec.h"

#include <math.h>
#include <stdint.h>
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


static hcclComm_t make_comm(int32_t ranks)
{
    int32_t ids[16];
    hcclComm_t comm = NULL;
    int32_t rank;
    for (rank = 0; rank < ranks; rank++) ids[rank] = rank;
    if (hcclCommInit(&comm, ranks, ids) != HCCL_SUCCESS) return NULL;
    return comm;
}


static void test_codec_roundtrip_and_decision(void)
{
    float values[128] = {0};
    float decoded[128];
    hcclSparsePayload payload;
    hcclSparseDecision decision;
    values[1] = 1.0f;
    values[64] = -2.0f;
    values[127] = 3.5f;
    CHECK("sparse encode", hccl_sparse_encode(values, 128, sizeof(float), &payload) == 0);
    CHECK("stable ordered index count", payload.nonzero_count == 3 && payload.index_width == 2);
    CHECK("sparse eligible by total modeled cost", hccl_sparse_decide(&payload, 1024 * 1024, &decision) == 0 && decision.eligible);
    CHECK("lossless reconstruction", hccl_sparse_decode(&payload, decoded, 128, sizeof(float)) == 0 && memcmp(values, decoded, sizeof(values)) == 0);
    CHECK("wire accounting", payload.wire_bytes == payload.index_bytes + payload.value_bytes + payload.metadata_bytes && payload.wire_bytes < payload.logical_bytes);
    hccl_sparse_payload_destroy(&payload);
}


static void test_dense_fallback(void)
{
    float values[64];
    hcclSparsePayload payload;
    hcclSparseDecision decision;
    size_t index;
    for (index = 0; index < 64; index++) values[index] = (float)(index + 1);
    CHECK("dense encode", hccl_sparse_encode(values, 64, sizeof(float), &payload) == 0);
    CHECK("dense fallback low sparsity", hccl_sparse_decide(&payload, 1024 * 1024, &decision) == 0 && !decision.eligible && strcmp(decision.fallback_reason, "LOW_SPARSITY") == 0);
    hccl_sparse_payload_destroy(&payload);
}


static void test_invalid_indices(void)
{
    float values[8] = {0.0f, 1.0f, 0.0f, 2.0f, 0.0f, 3.0f, 0.0f, 0.0f};
    float decoded[8];
    hcclSparsePayload payload;
    CHECK("invalid-index fixture encode", hccl_sparse_encode(values, 8, sizeof(float), &payload) == 0);
    if (payload.nonzero_count >= 2) {
        memcpy(payload.indices + payload.index_width, payload.indices, payload.index_width);
        CHECK("duplicate index rejected", hccl_sparse_decode(&payload, decoded, 8, sizeof(float)) != 0);
    } else {
        CHECK("duplicate index rejected", 0);
    }
    hccl_sparse_payload_destroy(&payload);
}


static void test_index_width_rule(void)
{
    CHECK("uint16 index boundary", hccl_sparse_index_width(65535) == 2);
    CHECK("uint32 index boundary", hccl_sparse_index_width(65536) == 4);
}


static void test_empty_and_16bit_codec(void)
{
    unsigned char empty_output = 0xA5;
    uint16_t values[64] = {0};
    uint16_t decoded[64] = {0};
    hcclSparsePayload payload;
    CHECK("empty sparse payload encode", hccl_sparse_encode(NULL, 0, sizeof(float), &payload) == 0 && payload.nonzero_count == 0);
    CHECK("empty sparse payload decode", hccl_sparse_decode(&payload, &empty_output, 0, sizeof(float)) == 0);
    hccl_sparse_payload_destroy(&payload);

    values[1] = 0x3C00U;
    values[17] = 0xBF80U;
    values[63] = 0x4000U;
    CHECK("FP16/BF16-width sparse encode", hccl_sparse_encode(values, 64, sizeof(uint16_t), &payload) == 0 && payload.nonzero_count == 3);
    CHECK("FP16/BF16-width lossless decode", hccl_sparse_decode(&payload, decoded, 64, sizeof(uint16_t)) == 0 && memcmp(values, decoded, sizeof(values)) == 0);
    hccl_sparse_payload_destroy(&payload);
}


static void test_allreduce_sparse_path(void)
{
    const int32_t ranks = 4;
    const size_t count = 128;
    float send[4][128] = {{0}};
    float recv[4][128] = {{0}};
    hcclComm_t comm = make_comm(ranks);
    hcclSparseRuntimeStats stats;
    int32_t rank;
    int correct = comm != NULL;
    for (rank = 0; rank < ranks; rank++) {
        send[rank][(size_t)rank * 7U] = (float)(rank + 1);
    }
    hccl_sparse_runtime_reset();
    for (rank = 0; rank < ranks && correct; rank++) {
        correct = hcclSetRank(comm, rank) == HCCL_SUCCESS &&
            hcclAllReduce(send[rank], recv[rank], count, HCCL_FP32, HCCL_SUM, comm) == HCCL_SUCCESS;
    }
    for (rank = 0; rank < ranks && correct; rank++) {
        correct = fabsf(recv[ranks - 1][(size_t)rank * 7U] - (float)(rank + 1)) < 1e-6f;
    }
    stats = hccl_sparse_runtime_stats();
    CHECK("sparse AllReduce correctness", correct);
    CHECK("sparse AllReduce transform selected", stats.prepare_calls == 4 && stats.sparse_selected == 4 && stats.dense_fallback == 0);
    if (comm != NULL) hcclCommDestroy(comm);
}


static void test_allgather_sparse_path(void)
{
    const int32_t ranks = 4;
    const size_t count = 64;
    float send[256] = {0};
    float recv[1024];
    hcclComm_t comm = make_comm(ranks);
    hcclSparseRuntimeStats stats;
    int correct = comm != NULL;
    int32_t rank;
    for (rank = 0; rank < ranks; rank++) send[(size_t)rank * count + (size_t)rank] = (float)(rank + 1);
    hccl_sparse_runtime_reset();
    if (correct) correct = hcclAllGather(send, recv, count, HCCL_FP32, comm) == HCCL_SUCCESS;
    for (rank = 0; rank < ranks && correct; rank++) {
        correct = memcmp(recv + (size_t)rank * ranks * count, send, sizeof(send)) == 0;
    }
    stats = hccl_sparse_runtime_stats();
    CHECK("sparse AllGather correctness", correct);
    CHECK("sparse AllGather transform selected", stats.prepare_calls == 1 && stats.sparse_selected == 1);
    if (comm != NULL) hcclCommDestroy(comm);
}


static void test_reducescatter_sparse_path(void)
{
    const int32_t ranks = 4;
    const size_t recv_count = 32;
    float send[512] = {0};
    float recv[128] = {0};
    hcclComm_t comm = make_comm(ranks);
    hcclSparseRuntimeStats stats;
    int correct = comm != NULL;
    int32_t src;
    for (src = 0; src < ranks; src++) {
        size_t index = ((size_t)src * ranks + (size_t)src) * recv_count + (size_t)src;
        send[index] = (float)(src + 1);
    }
    hccl_sparse_runtime_reset();
    if (correct) correct = hcclReduceScatter(send, recv, recv_count, HCCL_FP32, HCCL_SUM, comm) == HCCL_SUCCESS;
    for (src = 0; src < ranks && correct; src++) {
        correct = fabsf(recv[(size_t)src * recv_count + (size_t)src] - (float)(src + 1)) < 1e-6f;
    }
    stats = hccl_sparse_runtime_stats();
    CHECK("sparse ReduceScatter correctness", correct);
    CHECK("sparse ReduceScatter transform selected", stats.prepare_calls == 1 && stats.sparse_selected == 1);
    if (comm != NULL) hcclCommDestroy(comm);
}


int main(void)
{
    test_codec_roundtrip_and_decision();
    test_dense_fallback();
    test_invalid_indices();
    test_index_width_rule();
    test_empty_and_16bit_codec();
    test_allreduce_sparse_path();
    test_allgather_sparse_path();
    test_reducescatter_sparse_path();
    printf("sparse collective tests: %d run, %d failed\n", tests_run, tests_failed);
    return tests_failed == 0 ? 0 : 1;
}
