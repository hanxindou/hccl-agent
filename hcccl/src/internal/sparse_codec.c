#include "sparse_codec.h"

#include <stdlib.h>
#include <string.h>


static hcclSparseRuntimeStats g_runtime_stats;


static int checked_multiply(size_t lhs, size_t rhs, size_t* result)
{
    if (lhs != 0 && rhs > ((size_t)-1) / lhs) return -1;
    *result = lhs * rhs;
    return 0;
}


static int checked_add(size_t lhs, size_t rhs, size_t* result)
{
    if (rhs > ((size_t)-1) - lhs) return -1;
    *result = lhs + rhs;
    return 0;
}


static int element_is_zero(const unsigned char* value, size_t element_size)
{
    if (element_size == 2) {
        uint16_t bits;
        memcpy(&bits, value, sizeof(bits));
        return (bits & 0x7FFFU) == 0;
    }
    if (element_size == 4) {
        uint32_t bits;
        memcpy(&bits, value, sizeof(bits));
        return (bits & 0x7FFFFFFFU) == 0;
    }
    return 0;
}


static void write_index(unsigned char* destination, size_t width, uint64_t value)
{
    size_t byte;
    for (byte = 0; byte < width; byte++) {
        destination[byte] = (unsigned char)((value >> (byte * 8U)) & 0xFFU);
    }
}


static uint64_t read_index(const unsigned char* source, size_t width)
{
    uint64_t value = 0;
    size_t byte;
    for (byte = 0; byte < width; byte++) {
        value |= ((uint64_t)source[byte]) << (byte * 8U);
    }
    return value;
}


size_t hccl_sparse_index_width(size_t logical_elements)
{
    if (logical_elements <= 65535U) return 2;
#if SIZE_MAX > UINT32_MAX
    if (logical_elements <= UINT32_MAX) return 4;
    return 8;
#else
    return 4;
#endif
}


uint64_t hccl_sparse_hash64(const void* data, size_t length)
{
    const unsigned char* bytes = (const unsigned char*)data;
    uint64_t hash = UINT64_C(14695981039346656037);
    size_t index;
    for (index = 0; index < length; index++) {
        hash ^= (uint64_t)bytes[index];
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}


static uint64_t canonical_reconstruction_hash(
    const unsigned char* bytes, size_t element_count, size_t element_size)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    size_t element;
    size_t byte;
    for (element = 0; element < element_count; element++) {
        const unsigned char* value = bytes + element * element_size;
        int zero = element_is_zero(value, element_size);
        for (byte = 0; byte < element_size; byte++) {
            hash ^= zero ? 0U : (uint64_t)value[byte];
            hash *= UINT64_C(1099511628211);
        }
    }
    return hash;
}


int hccl_sparse_encode(
    const void* input, size_t element_count, size_t element_size,
    hcclSparsePayload* payload)
{
    const unsigned char* bytes = (const unsigned char*)input;
    size_t logical_bytes;
    size_t nonzero_count = 0;
    size_t index_bytes;
    size_t value_bytes;
    size_t combined;
    size_t element;

    if (payload == NULL || (element_count != 0 && input == NULL)) return -1;
    if (element_size != 2 && element_size != 4) return -1;
    if (checked_multiply(element_count, element_size, &logical_bytes) != 0) return -1;
    memset(payload, 0, sizeof(*payload));

    for (element = 0; element < element_count; element++) {
        if (!element_is_zero(bytes + element * element_size, element_size)) nonzero_count++;
    }

    payload->logical_element_count = element_count;
    payload->nonzero_count = nonzero_count;
    payload->element_size = element_size;
    payload->index_width = hccl_sparse_index_width(element_count);
    payload->logical_bytes = logical_bytes;
    payload->metadata_bytes = HCCL_SPARSE_METADATA_BYTES;
    if (checked_multiply(nonzero_count, payload->index_width, &index_bytes) != 0 ||
        checked_multiply(nonzero_count, element_size, &value_bytes) != 0 ||
        checked_add(index_bytes, value_bytes, &combined) != 0 ||
        checked_add(combined, payload->metadata_bytes, &payload->wire_bytes) != 0) {
        return -1;
    }
    payload->index_bytes = index_bytes;
    payload->value_bytes = value_bytes;
    payload->compression_ratio = payload->wire_bytes == 0
        ? 0.0 : (double)logical_bytes / (double)payload->wire_bytes;
    payload->reconstruction_hash = canonical_reconstruction_hash(
        bytes, element_count, element_size);

    if (nonzero_count == 0) return 0;
    payload->indices = (unsigned char*)malloc(index_bytes);
    payload->values = (unsigned char*)malloc(value_bytes);
    if (payload->indices == NULL || payload->values == NULL) {
        hccl_sparse_payload_destroy(payload);
        return -1;
    }

    nonzero_count = 0;
    for (element = 0; element < element_count; element++) {
        const unsigned char* value = bytes + element * element_size;
        if (!element_is_zero(value, element_size)) {
            write_index(
                payload->indices + nonzero_count * payload->index_width,
                payload->index_width,
                (uint64_t)element);
            memcpy(payload->values + nonzero_count * element_size, value, element_size);
            nonzero_count++;
        }
    }
    return 0;
}


int hccl_sparse_decode(
    const hcclSparsePayload* payload, void* output,
    size_t output_elements, size_t element_size)
{
    unsigned char* bytes = (unsigned char*)output;
    size_t output_bytes;
    size_t ordinal;
    uint64_t previous = 0;
    int have_previous = 0;
    if (payload == NULL || output == NULL) return -1;
    if (element_size != payload->element_size || output_elements != payload->logical_element_count) return -1;
    if (payload->nonzero_count != 0 && (payload->indices == NULL || payload->values == NULL)) return -1;
    if (checked_multiply(output_elements, element_size, &output_bytes) != 0) return -1;
    memset(output, 0, output_bytes);
    for (ordinal = 0; ordinal < payload->nonzero_count; ordinal++) {
        uint64_t index = read_index(
            payload->indices + ordinal * payload->index_width,
            payload->index_width);
        if (index >= output_elements || (have_previous && index <= previous)) return -1;
        memcpy(
            bytes + (size_t)index * element_size,
            payload->values + ordinal * element_size,
            element_size);
        previous = index;
        have_previous = 1;
    }
    if (hccl_sparse_hash64(output, output_bytes) != payload->reconstruction_hash) return -1;
    return 0;
}


int hccl_sparse_decide(
    const hcclSparsePayload* payload, size_t memory_limit_bytes,
    hcclSparseDecision* decision)
{
    size_t combined;
    if (payload == NULL || decision == NULL) return -1;
    memset(decision, 0, sizeof(*decision));
    decision->sparsity_ratio = payload->logical_element_count == 0
        ? 1.0
        : 1.0 - (double)payload->nonzero_count / (double)payload->logical_element_count;
    decision->detect_cost_equivalent_bytes = (payload->logical_bytes + 99U) / 100U;
    decision->encode_cost_equivalent_bytes = (payload->value_bytes + 99U) / 100U;
    decision->decode_cost_equivalent_bytes = (payload->value_bytes + 99U) / 100U;
    if (checked_add(payload->wire_bytes, decision->detect_cost_equivalent_bytes, &combined) != 0 ||
        checked_add(combined, decision->encode_cost_equivalent_bytes, &combined) != 0 ||
        checked_add(combined, decision->decode_cost_equivalent_bytes, &combined) != 0) {
        return -1;
    }
    decision->estimated_sparse_total_cost = combined;
    decision->estimated_dense_total_cost = payload->logical_bytes;
    decision->eligible = combined < payload->logical_bytes && payload->wire_bytes <= memory_limit_bytes;
    if (!decision->eligible) {
        if (payload->wire_bytes > memory_limit_bytes) {
            decision->fallback_reason = "MEMORY_LIMIT";
        } else if (decision->sparsity_ratio < 0.5) {
            decision->fallback_reason = "LOW_SPARSITY";
        } else {
            decision->fallback_reason = "METADATA_OVERHEAD";
        }
    }
    return 0;
}


void hccl_sparse_payload_destroy(hcclSparsePayload* payload)
{
    if (payload == NULL) return;
    free(payload->indices);
    free(payload->values);
    memset(payload, 0, sizeof(*payload));
}


static void record_decision(const hcclSparsePayload* payload, const hcclSparseDecision* decision)
{
    g_runtime_stats.prepare_calls++;
    if (decision->eligible) {
        g_runtime_stats.sparse_selected++;
        g_runtime_stats.last_fallback_reason[0] = '\0';
    } else {
        g_runtime_stats.dense_fallback++;
        if (decision->fallback_reason != NULL) {
            strncpy(
                g_runtime_stats.last_fallback_reason,
                decision->fallback_reason,
                sizeof(g_runtime_stats.last_fallback_reason) - 1);
            g_runtime_stats.last_fallback_reason[sizeof(g_runtime_stats.last_fallback_reason) - 1] = '\0';
        }
    }
    g_runtime_stats.last_logical_bytes = payload->logical_bytes;
    g_runtime_stats.last_wire_bytes = payload->wire_bytes;
    g_runtime_stats.last_nonzero_count = payload->nonzero_count;
    g_runtime_stats.last_index_width = payload->index_width;
}


int hccl_sparse_prepared_init(
    const void* input, size_t element_count, size_t element_size,
    size_t memory_limit_bytes, hcclSparsePreparedInput* prepared)
{
    if (prepared == NULL) return -1;
    memset(prepared, 0, sizeof(*prepared));
    prepared->dense_input = input;
    if (hccl_sparse_encode(input, element_count, element_size, &prepared->payload) != 0) return -1;
    if (hccl_sparse_decide(&prepared->payload, memory_limit_bytes, &prepared->decision) != 0) {
        hccl_sparse_payload_destroy(&prepared->payload);
        return -1;
    }
    prepared->sparse_selected = prepared->decision.eligible;
    record_decision(&prepared->payload, &prepared->decision);
    return 0;
}


int hccl_sparse_prepared_copy_element(
    const hcclSparsePreparedInput* prepared, size_t element_index,
    void* output_element)
{
    size_t low;
    size_t high;
    if (prepared == NULL || output_element == NULL ||
        element_index >= prepared->payload.logical_element_count) return -1;
    if (!prepared->sparse_selected) {
        memcpy(
            output_element,
            (const unsigned char*)prepared->dense_input + element_index * prepared->payload.element_size,
            prepared->payload.element_size);
        return 0;
    }
    low = 0;
    high = prepared->payload.nonzero_count;
    while (low < high) {
        size_t middle = low + (high - low) / 2;
        uint64_t index = read_index(
            prepared->payload.indices + middle * prepared->payload.index_width,
            prepared->payload.index_width);
        if (index < element_index) low = middle + 1;
        else high = middle;
    }
    if (low < prepared->payload.nonzero_count &&
        read_index(
            prepared->payload.indices + low * prepared->payload.index_width,
            prepared->payload.index_width) == element_index) {
        memcpy(
            output_element,
            prepared->payload.values + low * prepared->payload.element_size,
            prepared->payload.element_size);
    } else {
        memset(output_element, 0, prepared->payload.element_size);
    }
    return 0;
}


void hccl_sparse_prepared_destroy(hcclSparsePreparedInput* prepared)
{
    if (prepared == NULL) return;
    hccl_sparse_payload_destroy(&prepared->payload);
    memset(prepared, 0, sizeof(*prepared));
}


void hccl_sparse_runtime_reset(void)
{
    memset(&g_runtime_stats, 0, sizeof(g_runtime_stats));
}


hcclSparseRuntimeStats hccl_sparse_runtime_stats(void)
{
    return g_runtime_stats;
}
