#include "schedule_ir.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char* data;
    size_t length;
    size_t capacity;
} string_builder;

typedef struct {
    uint32_t state[8];
    uint64_t bit_count;
    unsigned char block[64];
    size_t block_length;
} sha256_ctx;

static const uint32_t sha256_k[64] = {
    0x428a2f98U,0x71374491U,0xb5c0fbcfU,0xe9b5dba5U,0x3956c25bU,0x59f111f1U,0x923f82a4U,0xab1c5ed5U,
    0xd807aa98U,0x12835b01U,0x243185beU,0x550c7dc3U,0x72be5d74U,0x80deb1feU,0x9bdc06a7U,0xc19bf174U,
    0xe49b69c1U,0xefbe4786U,0x0fc19dc6U,0x240ca1ccU,0x2de92c6fU,0x4a7484aaU,0x5cb0a9dcU,0x76f988daU,
    0x983e5152U,0xa831c66dU,0xb00327c8U,0xbf597fc7U,0xc6e00bf3U,0xd5a79147U,0x06ca6351U,0x14292967U,
    0x27b70a85U,0x2e1b2138U,0x4d2c6dfcU,0x53380d13U,0x650a7354U,0x766a0abbU,0x81c2c92eU,0x92722c85U,
    0xa2bfe8a1U,0xa81a664bU,0xc24b8b70U,0xc76c51a3U,0xd192e819U,0xd6990624U,0xf40e3585U,0x106aa070U,
    0x19a4c116U,0x1e376c08U,0x2748774cU,0x34b0bcb5U,0x391c0cb3U,0x4ed8aa4aU,0x5b9cca4fU,0x682e6ff3U,
    0x748f82eeU,0x78a5636fU,0x84c87814U,0x8cc70208U,0x90befffaU,0xa4506cebU,0xbef9a3f7U,0xc67178f2U
};

static uint32_t rotate_right(uint32_t value, unsigned count)
{
    return (value >> count) | (value << (32U - count));
}

static void sha256_transform(sha256_ctx* ctx, const unsigned char block[64])
{
    uint32_t w[64];
    uint32_t a, b, c, d, e, f, g, h;
    size_t i;
    for (i = 0; i < 16; ++i) {
        w[i] = ((uint32_t)block[i * 4] << 24) | ((uint32_t)block[i * 4 + 1] << 16) |
               ((uint32_t)block[i * 4 + 2] << 8) | (uint32_t)block[i * 4 + 3];
    }
    for (i = 16; i < 64; ++i) {
        uint32_t s0 = rotate_right(w[i - 15], 7) ^ rotate_right(w[i - 15], 18) ^ (w[i - 15] >> 3);
        uint32_t s1 = rotate_right(w[i - 2], 17) ^ rotate_right(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    a=ctx->state[0]; b=ctx->state[1]; c=ctx->state[2]; d=ctx->state[3];
    e=ctx->state[4]; f=ctx->state[5]; g=ctx->state[6]; h=ctx->state[7];
    for (i = 0; i < 64; ++i) {
        uint32_t s1 = rotate_right(e, 6) ^ rotate_right(e, 11) ^ rotate_right(e, 25);
        uint32_t choose = (e & f) ^ ((~e) & g);
        uint32_t temp1 = h + s1 + choose + sha256_k[i] + w[i];
        uint32_t s0 = rotate_right(a, 2) ^ rotate_right(a, 13) ^ rotate_right(a, 22);
        uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
        uint32_t temp2 = s0 + majority;
        h=g; g=f; f=e; e=d+temp1; d=c; c=b; b=a; a=temp1+temp2;
    }
    ctx->state[0]+=a; ctx->state[1]+=b; ctx->state[2]+=c; ctx->state[3]+=d;
    ctx->state[4]+=e; ctx->state[5]+=f; ctx->state[6]+=g; ctx->state[7]+=h;
}

static void sha256_init(sha256_ctx* ctx)
{
    static const uint32_t initial[8] = {0x6a09e667U,0xbb67ae85U,0x3c6ef372U,0xa54ff53aU,0x510e527fU,0x9b05688cU,0x1f83d9abU,0x5be0cd19U};
    memcpy(ctx->state, initial, sizeof(initial));
    ctx->bit_count = 0;
    ctx->block_length = 0;
}

static void sha256_update(sha256_ctx* ctx, const unsigned char* data, size_t length)
{
    size_t index;
    ctx->bit_count += (uint64_t)length * 8U;
    for (index = 0; index < length; ++index) {
        ctx->block[ctx->block_length++] = data[index];
        if (ctx->block_length == 64) {
            sha256_transform(ctx, ctx->block);
            ctx->block_length = 0;
        }
    }
}

static void sha256_final(sha256_ctx* ctx, unsigned char digest[32])
{
    size_t index;
    ctx->block[ctx->block_length++] = 0x80U;
    if (ctx->block_length > 56) {
        while (ctx->block_length < 64) ctx->block[ctx->block_length++] = 0;
        sha256_transform(ctx, ctx->block);
        ctx->block_length = 0;
    }
    while (ctx->block_length < 56) ctx->block[ctx->block_length++] = 0;
    for (index = 0; index < 8; ++index) {
        ctx->block[63 - index] = (unsigned char)(ctx->bit_count >> (index * 8));
    }
    sha256_transform(ctx, ctx->block);
    for (index = 0; index < 8; ++index) {
        digest[index * 4] = (unsigned char)(ctx->state[index] >> 24);
        digest[index * 4 + 1] = (unsigned char)(ctx->state[index] >> 16);
        digest[index * 4 + 2] = (unsigned char)(ctx->state[index] >> 8);
        digest[index * 4 + 3] = (unsigned char)ctx->state[index];
    }
}

static int sb_reserve(string_builder* builder, size_t extra)
{
    size_t needed = builder->length + extra + 1;
    size_t capacity = builder->capacity ? builder->capacity : 4096;
    char* replacement;
    while (capacity < needed) {
        if (capacity > ((size_t)-1) / 2) return -1;
        capacity *= 2;
    }
    if (capacity == builder->capacity) return 0;
    replacement = (char*)realloc(builder->data, capacity);
    if (replacement == NULL) return -1;
    builder->data = replacement;
    builder->capacity = capacity;
    return 0;
}

static int sb_addf(string_builder* builder, const char* format, ...)
{
    va_list arguments;
    va_list copy;
    int count;
    va_start(arguments, format);
    va_copy(copy, arguments);
    count = vsnprintf(NULL, 0, format, copy);
    va_end(copy);
    if (count < 0 || sb_reserve(builder, (size_t)count) != 0) {
        va_end(arguments);
        return -1;
    }
    vsnprintf(builder->data + builder->length, builder->capacity - builder->length, format, arguments);
    va_end(arguments);
    builder->length += (size_t)count;
    return 0;
}

static int primitive_info(const char* primitive, int* has_rs, int* has_ag, const char** lower)
{
    if (strcmp(primitive, "AllReduce") == 0) { *has_rs=1; *has_ag=1; *lower="allreduce"; return 0; }
    if (strcmp(primitive, "AllGather") == 0) { *has_rs=0; *has_ag=1; *lower="allgather"; return 0; }
    if (strcmp(primitive, "ReduceScatter") == 0) { *has_rs=1; *has_ag=0; *lower="reducescatter"; return 0; }
    return -1;
}

static uint64_t chunk_length(uint64_t message, int32_t ranks, int32_t chunk)
{
    return message / (uint64_t)ranks + ((uint64_t)chunk < message % (uint64_t)ranks ? 1U : 0U);
}

static uint64_t chunk_offset(uint64_t message, int32_t ranks, int32_t chunk)
{
    uint64_t base = message / (uint64_t)ranks;
    uint64_t remainder = message % (uint64_t)ranks;
    return (uint64_t)chunk * base + ((uint64_t)chunk < remainder ? (uint64_t)chunk : remainder);
}

static int serialize_schedule(
    string_builder* builder, const char* primitive, int32_t ranks, uint64_t message,
    const char* dtype, const char* reduce_op, const char* lower, int has_rs, int has_ag,
    const char* hash
)
{
    int32_t phase_count = (has_rs + has_ag) * (ranks - 1);
    uint64_t chunk_size = (message + (uint64_t)ranks - 1U) / (uint64_t)ranks;
    int32_t phase;
    if (sb_addf(builder, "{\"algorithm\":\"Ring\",\"chunk_count\":%d,\"chunk_size_bytes\":%llu,\"dependencies\":[", ranks, (unsigned long long)chunk_size) != 0) return -1;
    for (phase = 1; phase < phase_count; ++phase) {
        if (phase > 1) if (sb_addf(builder, ",") != 0) return -1;
        if (sb_addf(builder, "{\"from\":\"phase-%04d\",\"to\":\"phase-%04d\"}", phase - 1, phase) != 0) return -1;
    }
    if (sb_addf(builder, "],\"dtype\":\"%s\",\"estimated_metrics\":{\"critical_path_steps\":%d,\"modeled_transfer_bytes\":%llu,\"phase_count\":%d},", dtype, phase_count, (unsigned long long)(message * (uint64_t)phase_count), phase_count) != 0) return -1;
    if (sb_addf(builder, "\"failure_policy\":{\"fallback_policy\":\"NONE\",\"max_retries\":3,\"on_no_path\":\"EXPECTED_NO_PATH_FAILURE\",\"retry_policy\":\"BOUNDED\"},") != 0) return -1;
    if (sb_addf(builder, "\"hardware_profile_hash\":\"g3-b2-frozen-hardware-v1\",\"memory_plan\":{\"bounded\":true,\"buffer_count\":2,\"logical_message_bytes\":%llu,\"materialization_mode\":\"CHUNK_STREAMING\",\"peak_materialized_bytes\":%llu},", (unsigned long long)message, (unsigned long long)(chunk_size * 2U)) != 0) return -1;
    if (sb_addf(builder, "\"message_size_bytes\":%llu,\"phases\":[", (unsigned long long)message) != 0) return -1;
    for (phase = 0; phase < phase_count; ++phase) {
        int is_rs = has_rs && phase < ranks - 1;
        int local_step = is_rs ? phase : phase - (has_rs ? ranks - 1 : 0);
        int32_t source;
        if (phase > 0) if (sb_addf(builder, ",") != 0) return -1;
        if (phase == 0) {
            if (sb_addf(builder, "{\"dependencies\":[],") != 0) return -1;
        } else {
            if (sb_addf(builder, "{\"dependencies\":[\"phase-%04d\"],", phase - 1) != 0) return -1;
        }
        if (sb_addf(builder, "\"phase_id\":\"phase-%04d\",\"phase_index\":%d,\"phase_type\":\"%s\",\"transfers\":[", phase, phase, is_rs ? "REDUCE_SCATTER" : "ALL_GATHER") != 0) return -1;
        for (source = 0; source < ranks; ++source) {
            int32_t chunk = is_rs ? (source - local_step - 1 + ranks * 2) % ranks : (source - local_step + ranks * 2) % ranks;
            int32_t destination = (source + 1) % ranks;
            if (source > 0) if (sb_addf(builder, ",") != 0) return -1;
            if (sb_addf(builder, "{\"chunk_id\":%d,\"destination_rank\":%d,\"length_bytes\":%llu,\"link_id\":\"ring:%d->%d\",\"offset_bytes\":%llu,\"operation\":\"%s\",\"source_rank\":%d,\"transfer_id\":\"transfer-%04d-%04d\"}", chunk, destination, (unsigned long long)chunk_length(message, ranks, chunk), source, destination, (unsigned long long)chunk_offset(message, ranks, chunk), is_rs ? "REDUCE" : "COPY", source, phase, source) != 0) return -1;
        }
        if (sb_addf(builder, "]}") != 0) return -1;
    }
    if (sb_addf(builder, "],\"primitive\":\"%s\",\"rank_size\":%d,\"reduce_op\":", primitive, ranks) != 0) return -1;
    if (strcmp(primitive, "AllGather") == 0) {
        if (sb_addf(builder, "null") != 0) return -1;
    } else {
        if (sb_addf(builder, "\"%s\"", reduce_op) != 0) return -1;
    }
    if (sb_addf(builder, ",\"schedule_id\":\"ring-%s-r%d-m%llu\",", lower, ranks, (unsigned long long)message) != 0) return -1;
    if (hash != NULL && sb_addf(builder, "\"schedule_hash\":\"%s\",", hash) != 0) return -1;
    if (sb_addf(builder, "\"schema_version\":\"g3-b2-schedule-ir-v1\",\"topology_hash\":\"test-topology-v1\"}") != 0) return -1;
    return 0;
}

int hccl_schedule_ir_generate_json(const char* primitive, int32_t rank_size, uint64_t message_size_bytes, const char* dtype, const char* reduce_op, char** json_out)
{
    int has_rs = 0, has_ag = 0;
    const char* lower = NULL;
    string_builder preimage = {0};
    string_builder final = {0};
    sha256_ctx sha;
    unsigned char digest[32];
    char hash[65];
    size_t index;
    if (json_out == NULL || primitive == NULL || dtype == NULL || reduce_op == NULL ||
        rank_size < 2 || rank_size > 64 || message_size_bytes < 1U ||
        primitive_info(primitive, &has_rs, &has_ag, &lower) != 0) return -1;
    *json_out = NULL;
    if (serialize_schedule(&preimage, primitive, rank_size, message_size_bytes, dtype, reduce_op, lower, has_rs, has_ag, NULL) != 0) goto fail;
    sha256_init(&sha);
    sha256_update(&sha, (const unsigned char*)preimage.data, preimage.length);
    sha256_final(&sha, digest);
    for (index = 0; index < 32; ++index) snprintf(hash + index * 2, 3, "%02x", digest[index]);
    hash[64] = '\0';
    if (serialize_schedule(&final, primitive, rank_size, message_size_bytes, dtype, reduce_op, lower, has_rs, has_ag, hash) != 0) goto fail;
    free(preimage.data);
    *json_out = final.data;
    return 0;
fail:
    free(preimage.data);
    free(final.data);
    return -1;
}

void hccl_schedule_ir_free_json(char* json_value)
{
    free(json_value);
}
