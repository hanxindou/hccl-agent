#include "internal/sparse_codec.h"

#include <inttypes.h>
#include <stdio.h>


static uint64_t read_index(const unsigned char* bytes, size_t width)
{
    uint64_t value = 0;
    size_t byte;
    for (byte = 0; byte < width; byte++) value |= ((uint64_t)bytes[byte]) << (byte * 8U);
    return value;
}


int main(void)
{
    float input[8] = {0.0f, 1.0f, 0.0f, -2.0f, 0.0f, 3.5f, -0.0f, 0.0f};
    hcclSparsePayload payload;
    size_t ordinal;
    if (hccl_sparse_encode(input, 8, sizeof(float), &payload) != 0) return 1;
    printf("{\"logical_element_count\":%zu,\"nonzero_count\":%zu,\"index_width\":%zu,\"indices\":[",
           payload.logical_element_count, payload.nonzero_count, payload.index_width);
    for (ordinal = 0; ordinal < payload.nonzero_count; ordinal++) {
        if (ordinal) printf(",");
        printf("%" PRIu64, read_index(payload.indices + ordinal * payload.index_width, payload.index_width));
    }
    printf("],\"values_hex\":\"");
    for (ordinal = 0; ordinal < payload.value_bytes; ordinal++) printf("%02x", payload.values[ordinal]);
    printf("\",\"logical_bytes\":%zu,\"wire_bytes\":%zu,\"index_bytes\":%zu,\"value_bytes\":%zu,\"metadata_bytes\":%zu,\"compression_ratio\":%.12f,\"reconstruction_hash64\":\"%016" PRIx64 "\"}\n",
           payload.logical_bytes, payload.wire_bytes, payload.index_bytes,
           payload.value_bytes, payload.metadata_bytes, payload.compression_ratio,
           payload.reconstruction_hash);
    hccl_sparse_payload_destroy(&payload);
    return 0;
}
