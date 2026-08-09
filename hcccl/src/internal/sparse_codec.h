#ifndef HCCL_INTERNAL_SPARSE_CODEC_H
#define HCCL_INTERNAL_SPARSE_CODEC_H

#include <stddef.h>
#include <stdint.h>

#if defined(__GNUC__) || defined(__clang__)
#define HCCL_INTERNAL_VISIBILITY __attribute__((visibility("hidden")))
#else
#define HCCL_INTERNAL_VISIBILITY
#endif

#define HCCL_SPARSE_METADATA_BYTES ((size_t)64)

typedef struct {
    size_t logical_element_count;
    size_t nonzero_count;
    size_t element_size;
    size_t index_width;
    unsigned char* indices;
    unsigned char* values;
    size_t logical_bytes;
    size_t index_bytes;
    size_t value_bytes;
    size_t metadata_bytes;
    size_t wire_bytes;
    double compression_ratio;
    uint64_t reconstruction_hash;
} hcclSparsePayload;

typedef struct {
    int eligible;
    const char* fallback_reason;
    double sparsity_ratio;
    size_t detect_cost_equivalent_bytes;
    size_t encode_cost_equivalent_bytes;
    size_t decode_cost_equivalent_bytes;
    size_t estimated_sparse_total_cost;
    size_t estimated_dense_total_cost;
} hcclSparseDecision;

typedef struct {
    uint64_t prepare_calls;
    uint64_t sparse_selected;
    uint64_t dense_fallback;
    size_t last_logical_bytes;
    size_t last_wire_bytes;
    size_t last_nonzero_count;
    size_t last_index_width;
    char last_fallback_reason[32];
} hcclSparseRuntimeStats;

typedef struct {
    const void* dense_input;
    hcclSparsePayload payload;
    hcclSparseDecision decision;
    int sparse_selected;
} hcclSparsePreparedInput;

HCCL_INTERNAL_VISIBILITY size_t hccl_sparse_index_width(size_t logical_elements);
HCCL_INTERNAL_VISIBILITY uint64_t hccl_sparse_hash64(const void* data, size_t length);
HCCL_INTERNAL_VISIBILITY int hccl_sparse_encode(
    const void* input, size_t element_count, size_t element_size,
    hcclSparsePayload* payload);
HCCL_INTERNAL_VISIBILITY int hccl_sparse_decode(
    const hcclSparsePayload* payload, void* output,
    size_t output_elements, size_t element_size);
HCCL_INTERNAL_VISIBILITY int hccl_sparse_decide(
    const hcclSparsePayload* payload, size_t memory_limit_bytes,
    hcclSparseDecision* decision);
HCCL_INTERNAL_VISIBILITY void hccl_sparse_payload_destroy(hcclSparsePayload* payload);
HCCL_INTERNAL_VISIBILITY int hccl_sparse_prepared_init(
    const void* input, size_t element_count, size_t element_size,
    size_t memory_limit_bytes, hcclSparsePreparedInput* prepared);
HCCL_INTERNAL_VISIBILITY int hccl_sparse_prepared_copy_element(
    const hcclSparsePreparedInput* prepared, size_t element_index,
    void* output_element);
HCCL_INTERNAL_VISIBILITY void hccl_sparse_prepared_destroy(
    hcclSparsePreparedInput* prepared);
HCCL_INTERNAL_VISIBILITY void hccl_sparse_runtime_reset(void);
HCCL_INTERNAL_VISIBILITY hcclSparseRuntimeStats hccl_sparse_runtime_stats(void);

#endif
