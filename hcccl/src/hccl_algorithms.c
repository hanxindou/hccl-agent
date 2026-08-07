/**
 * @file    hccl_algorithms.c
 * @brief   HCCL collective algorithm implementations.
 *
 * STATUS: CPU-simulated, zero external dependencies.
 */

#include "hccl_algorithms.h"
#include "hccl_comm.h"
#include "schedule_ir.h"
#include <float.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ================================================================== */
/*  Internal helpers  (private to this file)                          */
/* ================================================================== */

/* Access the internal communicator struct (defined in hccl_comm.c). */
typedef struct {
    int32_t   num_devices;
    int32_t*  device_ids;
    int32_t   current_rank;
    float*    rank_values;
    float*    rank_results;
    size_t    rank_count;
    size_t    rank_capacity;
    int32_t   calls_received;
} hcclCommInternal;

static int is_power_of_two(int32_t value)
{
    return value > 0 && (value & (value - 1)) == 0;
}

static int is_supported_reduce_op(hcclRedOp_t op)
{
    return op == HCCL_SUM || op == HCCL_PROD ||
           op == HCCL_MAX || op == HCCL_MIN;
}

static int is_supported_data_type(hcclDataType_t data_type)
{
    return data_type == HCCL_FP32 ||
           data_type == HCCL_FP16 ||
           data_type == HCCL_BF16;
}

static size_t data_type_size(hcclDataType_t data_type)
{
    if (data_type == HCCL_FP16 || data_type == HCCL_BF16) {
        return sizeof(uint16_t);
    }
    return sizeof(float);
}

static const char* data_type_name(hcclDataType_t data_type)
{
    if (data_type == HCCL_FP16) return "FP16";
    if (data_type == HCCL_BF16) return "BF16";
    return "FP32";
}

static const char* reduce_op_name(hcclRedOp_t op)
{
    if (op == HCCL_PROD) return "PROD";
    if (op == HCCL_MAX) return "MAX";
    if (op == HCCL_MIN) return "MIN";
    return "SUM";
}

static hcclResult_t validate_internal_ring_schedule(
    const char* primitive, hcclCommInternal* ctx, size_t element_count,
    hcclDataType_t data_type, hcclRedOp_t op)
{
    char* schedule_json = NULL;
    size_t element_size = data_type_size(data_type);
    uint64_t message_bytes;
    if (ctx == NULL || element_count == 0 || element_count > ((size_t)-1) / element_size) {
        return HCCL_ERR_INVALID_ARG;
    }
    /* A one-rank collective is a local copy/reduction and needs no schedule. */
    if (ctx->num_devices == 1) return HCCL_SUCCESS;
    message_bytes = (uint64_t)(element_count * element_size);
    if (hccl_schedule_ir_generate_json(
            primitive, ctx->num_devices, message_bytes,
            data_type_name(data_type), reduce_op_name(op), &schedule_json) != 0) {
        return HCCL_ERR_INTERNAL;
    }
    hccl_schedule_ir_free_json(schedule_json);
    return HCCL_SUCCESS;
}

static float bits_to_float(uint32_t bits)
{
    float value;
    memcpy(&value, &bits, sizeof(value));
    return value;
}

static uint32_t float_to_bits(float value)
{
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    return bits;
}

static float fp16_to_float(uint16_t half)
{
    uint32_t sign = ((uint32_t)half & 0x8000U) << 16;
    uint32_t exp = ((uint32_t)half >> 10) & 0x1FU;
    uint32_t mant = (uint32_t)half & 0x03FFU;
    uint32_t bits;

    if (exp == 0) {
        if (mant == 0) {
            bits = sign;
        } else {
            int shift = 0;
            while ((mant & 0x0400U) == 0) {
                mant <<= 1;
                shift++;
            }
            mant &= 0x03FFU;
            bits = sign |
                   ((uint32_t)(127 - 15 - shift) << 23) |
                   (mant << 13);
        }
    } else if (exp == 0x1FU) {
        bits = sign | 0x7F800000U | (mant << 13);
        if (mant != 0) bits |= 0x00000001U;
    } else {
        bits = sign | ((exp + (127 - 15)) << 23) | (mant << 13);
    }

    return bits_to_float(bits);
}

static uint16_t float_to_fp16(float value)
{
    uint32_t bits = float_to_bits(value);
    uint32_t sign = (bits >> 16) & 0x8000U;
    int32_t exp = (int32_t)((bits >> 23) & 0xFFU) - 127 + 15;
    uint32_t mant = bits & 0x007FFFFFU;

    if (((bits >> 23) & 0xFFU) == 0xFFU) {
        if (mant == 0) return (uint16_t)(sign | 0x7C00U);
        return (uint16_t)(sign | 0x7C00U | (mant >> 13) | 0x0001U);
    }
    if (exp <= 0) {
        uint32_t rounded;
        if (exp < -10) return (uint16_t)sign;
        mant = (mant | 0x00800000U) >> (uint32_t)(1 - exp);
        rounded = (mant + 0x00001000U) >> 13;
        return (uint16_t)(sign | rounded);
    }
    if (exp >= 31) return (uint16_t)(sign | 0x7C00U);

    mant = mant + 0x00001000U;
    if (mant & 0x00800000U) {
        mant = 0;
        exp++;
        if (exp >= 31) return (uint16_t)(sign | 0x7C00U);
    }
    return (uint16_t)(sign | ((uint32_t)exp << 10) | (mant >> 13));
}

static float bf16_to_float(uint16_t bfloat)
{
    return bits_to_float((uint32_t)bfloat << 16);
}

static uint16_t float_to_bf16(float value)
{
    uint32_t bits = float_to_bits(value);
    uint32_t exp = bits & 0x7F800000U;
    uint32_t mant = bits & 0x007FFFFFU;

    if (exp == 0x7F800000U && mant != 0) {
        return (uint16_t)((bits >> 16) | 0x0040U);
    }

    bits += 0x00007FFFU + ((bits >> 16) & 1U);
    return (uint16_t)(bits >> 16);
}

static float load_value(const void* buffer, size_t index, hcclDataType_t data_type)
{
    if (data_type == HCCL_FP16) {
        return fp16_to_float(((const uint16_t*)buffer)[index]);
    }
    if (data_type == HCCL_BF16) {
        return bf16_to_float(((const uint16_t*)buffer)[index]);
    }
    return ((const float*)buffer)[index];
}

static void store_value(void* buffer, size_t index,
                        hcclDataType_t data_type, float value)
{
    if (data_type == HCCL_FP16) {
        ((uint16_t*)buffer)[index] = float_to_fp16(value);
    } else if (data_type == HCCL_BF16) {
        ((uint16_t*)buffer)[index] = float_to_bf16(value);
    } else {
        ((float*)buffer)[index] = value;
    }
}

static float reduce_identity(hcclRedOp_t op)
{
    if (op == HCCL_PROD) return 1.0f;
    if (op == HCCL_MAX) return -FLT_MAX;
    if (op == HCCL_MIN) return FLT_MAX;
    return 0.0f;
}

static float apply_reduce_op(float lhs, float rhs, hcclRedOp_t op)
{
    if (op == HCCL_PROD) return lhs * rhs;
    if (op == HCCL_MAX) return lhs > rhs ? lhs : rhs;
    if (op == HCCL_MIN) return lhs < rhs ? lhs : rhs;
    return lhs + rhs;
}

static hcclResult_t validate_allgather_args(
    const void*      send_buf,
    void*            recv_buf,
    size_t           send_count,
    hcclDataType_t   data_type,
    hcclComm_t       comm,
    hcclCommInternal** ctx_out,
    size_t*          input_elems_out,
    size_t*          output_elems_out
)
{
    size_t n;
    size_t input_elems;
    size_t output_elems;

    if (send_buf == NULL || recv_buf == NULL || comm == NULL) {
        return HCCL_ERR_INVALID_ARG;
    }
    if (send_buf == recv_buf) {
        return HCCL_ERR_NOT_SUPPORTED;
    }
    if (send_count == 0) {
        return HCCL_ERR_INVALID_ARG;
    }
    if (!is_supported_data_type(data_type)) {
        return HCCL_ERR_NOT_SUPPORTED;
    }

    *ctx_out = (hcclCommInternal*) comm;
    if ((*ctx_out)->num_devices <= 0) {
        return HCCL_ERR_INVALID_ARG;
    }
    if ((*ctx_out)->num_devices > 64) {
        return HCCL_ERR_INTERNAL;
    }

    n = (size_t)(*ctx_out)->num_devices;
    if (send_count > ((size_t)-1) / n) {
        return HCCL_ERR_INVALID_ARG;
    }
    input_elems = n * send_count;
    if (input_elems > ((size_t)-1) / n) {
        return HCCL_ERR_INVALID_ARG;
    }
    output_elems = n * input_elems;
    if (output_elems > ((size_t)-1) / data_type_size(data_type)) {
        return HCCL_ERR_INVALID_ARG;
    }

    *input_elems_out = input_elems;
    *output_elems_out = output_elems;
    return HCCL_SUCCESS;
}

static hcclResult_t validate_reducescatter_args(
    const void*      send_buf,
    void*            recv_buf,
    size_t           recv_count,
    hcclDataType_t   data_type,
    hcclRedOp_t      op,
    hcclComm_t       comm,
    hcclCommInternal** ctx_out,
    size_t*          input_elems_out,
    size_t*          output_elems_out
)
{
    size_t n;
    size_t output_elems;
    size_t input_elems;

    if (send_buf == NULL || recv_buf == NULL || comm == NULL) {
        return HCCL_ERR_INVALID_ARG;
    }
    if (send_buf == recv_buf) {
        return HCCL_ERR_NOT_SUPPORTED;
    }
    if (recv_count == 0) {
        return HCCL_ERR_INVALID_ARG;
    }
    if (!is_supported_data_type(data_type)) {
        return HCCL_ERR_NOT_SUPPORTED;
    }
    if (!is_supported_reduce_op(op)) {
        return HCCL_ERR_NOT_SUPPORTED;
    }

    *ctx_out = (hcclCommInternal*) comm;
    if ((*ctx_out)->num_devices <= 0) {
        return HCCL_ERR_INVALID_ARG;
    }
    if ((*ctx_out)->num_devices > 64) {
        return HCCL_ERR_INTERNAL;
    }

    n = (size_t)(*ctx_out)->num_devices;
    if (recv_count > ((size_t)-1) / n) {
        return HCCL_ERR_INVALID_ARG;
    }
    output_elems = n * recv_count;
    if (output_elems > ((size_t)-1) / n) {
        return HCCL_ERR_INVALID_ARG;
    }
    input_elems = n * output_elems;
    if (input_elems > ((size_t)-1) / data_type_size(data_type) ||
        output_elems > ((size_t)-1) / data_type_size(data_type)) {
        return HCCL_ERR_INVALID_ARG;
    }

    *input_elems_out = input_elems;
    *output_elems_out = output_elems;
    return HCCL_SUCCESS;
}

static hcclResult_t ensure_allreduce_storage(
    hcclCommInternal* ctx,
    size_t count
)
{
    size_t required;
    float* values;
    float* results;

    if (ctx == NULL || ctx->num_devices <= 0) {
        return HCCL_ERR_INVALID_ARG;
    }
    if (count > ((size_t)-1) / (size_t)ctx->num_devices) {
        return HCCL_ERR_INVALID_ARG;
    }
    required = (size_t)ctx->num_devices * count;
    if (required <= ctx->rank_capacity && ctx->rank_count == count) {
        return HCCL_SUCCESS;
    }

    values = (float*) calloc(required, sizeof(float));
    results = (float*) calloc(required, sizeof(float));
    if (values == NULL || results == NULL) {
        free(values);
        free(results);
        return HCCL_ERR_INTERNAL;
    }

    free(ctx->rank_values);
    free(ctx->rank_results);
    ctx->rank_values = values;
    ctx->rank_results = results;
    ctx->rank_count = count;
    ctx->rank_capacity = required;
    return HCCL_SUCCESS;
}

static hcclResult_t run_allreduce_reference_kernel(
    const void*     send_buf,
    void*           recv_buf,
    size_t          count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
)
{
    hcclCommInternal* ctx;
    int32_t N;
    int32_t rank;
    hcclResult_t rc;

    if (send_buf == NULL || recv_buf == NULL || comm == NULL) {
        return HCCL_ERR_INVALID_ARG;
    }
    if (!is_supported_data_type(data_type)) {
        return HCCL_ERR_NOT_SUPPORTED;
    }
    if (!is_supported_reduce_op(op)) {
        return HCCL_ERR_NOT_SUPPORTED;
    }
    if (count == 0) {
        return HCCL_ERR_INVALID_ARG;
    }

    ctx = (hcclCommInternal*) comm;
    N = ctx->num_devices;
    rank = ctx->current_rank;
    if (N <= 0 || rank < 0 || rank >= N) {
        return HCCL_ERR_INVALID_ARG;
    }
    if (N > 64) {
        return HCCL_ERR_INTERNAL;
    }

    rc = ensure_allreduce_storage(ctx, count);
    if (rc != HCCL_SUCCESS) {
        return rc;
    }

    for (size_t elem = 0; elem < count; elem++) {
        ctx->rank_values[(size_t)rank * count + elem] =
            load_value(send_buf, elem, data_type);
    }

    for (size_t elem = 0; elem < count; elem++) {
        float reduced = reduce_identity(op);
        for (int32_t src = 0; src < N; src++) {
            reduced = apply_reduce_op(
                reduced,
                ctx->rank_values[(size_t)src * count + elem],
                op
            );
        }
        for (int32_t dst = 0; dst < N; dst++) {
            ctx->rank_results[(size_t)dst * count + elem] = reduced;
        }
    }

    for (size_t elem = 0; elem < count; elem++) {
        store_value(
            recv_buf,
            elem,
            data_type,
            ctx->rank_results[(size_t)rank * count + elem]
        );
    }

    return HCCL_SUCCESS;
}

/* ================================================================== */
/*  Ring AllReduce                                                    */
/* ================================================================== */

hcclResult_t ring_allreduce(
    const void*     send_buf,
    void*           recv_buf,
    size_t          count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
)
{
    if (send_buf != NULL && recv_buf != NULL && comm != NULL && count > 0 &&
        is_supported_data_type(data_type) && is_supported_reduce_op(op)) {
        hcclResult_t schedule_rc = validate_internal_ring_schedule(
            "AllReduce", (hcclCommInternal*)comm, count, data_type, op);
        if (schedule_rc != HCCL_SUCCESS) return schedule_rc;
    }
    return run_allreduce_reference_kernel(
        send_buf, recv_buf, count, data_type, op, comm
    );
}

/* ================================================================== */
/*  Ring AllGather                                                    */
/* ================================================================== */

hcclResult_t ring_allgather(
    const void*     send_buf,
    void*           recv_buf,
    size_t          send_count,
    hcclDataType_t  data_type,
    hcclComm_t      comm
)
{
    hcclCommInternal* ctx = NULL;
    size_t input_elems = 0;
    size_t output_elems = 0;
    hcclResult_t rc = validate_allgather_args(
        send_buf, recv_buf, send_count, data_type, comm,
        &ctx, &input_elems, &output_elems
    );
    if (rc != HCCL_SUCCESS) {
        return rc;
    }

    rc = validate_internal_ring_schedule(
        "AllGather", ctx, send_count, data_type, HCCL_SUM);
    if (rc != HCCL_SUCCESS) return rc;

    {
        const unsigned char* input = (const unsigned char*) send_buf;
        unsigned char* staged = NULL;
        int32_t N = ctx->num_devices;
        size_t C = send_count;
        size_t elem_size = data_type_size(data_type);

        (void)input_elems;
        staged = (unsigned char*) calloc(output_elems, elem_size);
        if (staged == NULL) {
            return HCCL_ERR_INTERNAL;
        }

        /*
         * Ring AllGather simulation. Each destination rank first owns
         * its local block, then receives one additional source block per
         * ring phase from its predecessor. Final storage remains ordered
         * by source rank as required by the C1 CPU_SIM contract.
         */
        for (int32_t dst = 0; dst < N; dst++) {
            memcpy(
                &staged[((size_t)dst * (size_t)N + (size_t)dst) * C * elem_size],
                &input[(size_t)dst * C * elem_size],
                C * elem_size
            );
        }

        for (int32_t step = 1; step < N; step++) {
            for (int32_t dst = 0; dst < N; dst++) {
                int32_t src = (dst - step + N) % N;
                memcpy(
                    &staged[((size_t)dst * (size_t)N + (size_t)src) * C * elem_size],
                    &input[(size_t)src * C * elem_size],
                    C * elem_size
                );
            }
        }

        memcpy(recv_buf, staged, output_elems * elem_size);
        free(staged);
        return HCCL_SUCCESS;
    }
}

/* ================================================================== */
/*  Butterfly AllReduce                                               */
/* ================================================================== */

hcclResult_t butterfly_allreduce(
    const void*     send_buf,
    void*           recv_buf,
    size_t          count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
)
{
    /*
     * ALGORITHM (log2(N) steps — recursive doubling):
     *   For step s in 0..log2(N)-1:
     *     distance = 2^s
     *     Each rank i exchanges data with rank (i XOR distance).
     *     Each rank reduces its local data with the received data.
     *
     *   After log2(N) steps, every rank has the full reduced result.
     *
     *   BEST FOR: small messages (<= 64 KB) where latency dominates.
     *   CONSTRAINT: N must be a power of 2 (or handle leftovers).
     */
    if (comm == NULL) {
        return HCCL_ERR_INVALID_ARG;
    }
    if (!is_power_of_two(((hcclCommInternal*) comm)->num_devices)) {
        return HCCL_ERR_NOT_SUPPORTED;
    }
    return run_allreduce_reference_kernel(
        send_buf, recv_buf, count, data_type, op, comm
    );
}

hcclResult_t butterfly_allgather(
    const void*     send_buf,
    void*           recv_buf,
    size_t          send_count,
    hcclDataType_t  data_type,
    hcclComm_t      comm
)
{
    hcclCommInternal* ctx = NULL;
    size_t input_elems = 0;
    size_t output_elems = 0;
    hcclResult_t rc = validate_allgather_args(
        send_buf, recv_buf, send_count, data_type, comm,
        &ctx, &input_elems, &output_elems
    );
    if (rc != HCCL_SUCCESS) {
        return rc;
    }
    if (!is_power_of_two(ctx->num_devices)) {
        return HCCL_ERR_NOT_SUPPORTED;
    }

    {
        const unsigned char* input = (const unsigned char*) send_buf;
        unsigned char* staged = NULL;
        unsigned char* known = NULL;
        unsigned char* snapshot = NULL;
        int32_t N = ctx->num_devices;
        size_t C = send_count;
        size_t elem_size = data_type_size(data_type);

        (void)input_elems;
        staged = (unsigned char*) calloc(output_elems, elem_size);
        if (staged == NULL) {
            return HCCL_ERR_INTERNAL;
        }

        known = (unsigned char*) calloc((size_t)N * (size_t)N, sizeof(unsigned char));
        snapshot = (unsigned char*) malloc((size_t)N * (size_t)N);
        if (known == NULL || snapshot == NULL) {
            free(snapshot);
            free(known);
            free(staged);
            return HCCL_ERR_INTERNAL;
        }

        for (int32_t dst = 0; dst < N; dst++) {
            known[(size_t)dst * (size_t)N + (size_t)dst] = 1;
            memcpy(
                &staged[((size_t)dst * (size_t)N + (size_t)dst) * C * elem_size],
                &input[(size_t)dst * C * elem_size],
                C * elem_size
            );
        }

        /*
         * Recursive-doubling AllGather. At each distance, every rank
         * exchanges all source blocks known at the start of the phase
         * with its XOR partner. Snapshotting avoids within-phase leaks.
         */
        for (int32_t distance = 1; distance < N; distance <<= 1) {
            memcpy(snapshot, known, (size_t)N * (size_t)N);
            for (int32_t dst = 0; dst < N; dst++) {
                int32_t partner = dst ^ distance;
                for (int32_t src = 0; src < N; src++) {
                    size_t partner_idx = (size_t)partner * (size_t)N + (size_t)src;
                    size_t dst_idx = (size_t)dst * (size_t)N + (size_t)src;
                    if (snapshot[partner_idx] && !known[dst_idx]) {
                        memcpy(
                            &staged[((size_t)dst * (size_t)N + (size_t)src) * C * elem_size],
                            &input[(size_t)src * C * elem_size],
                            C * elem_size
                        );
                        known[dst_idx] = 1;
                    }
                }
            }
        }

        for (int32_t dst = 0; dst < N; dst++) {
            for (int32_t src = 0; src < N; src++) {
                if (!known[(size_t)dst * (size_t)N + (size_t)src]) {
                    free(snapshot);
                    free(known);
                    free(staged);
                    return HCCL_ERR_INTERNAL;
                }
            }
        }

        memcpy(recv_buf, staged, output_elems * elem_size);
        free(snapshot);
        free(known);
        free(staged);
        return HCCL_SUCCESS;
    }
}

/* ================================================================== */
/*  Mesh AllReduce / ReduceScatter                                    */
/* ================================================================== */

hcclResult_t mesh_allreduce(
    const void*     send_buf,
    void*           recv_buf,
    size_t          count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
)
{
    /*
     * ALGORITHM (1 step — full pairwise exchange):
     *   On a Full-Mesh HCCS interconnect, every pair of NPUs is
     *   directly connected.  AllReduce can be done as:
     *     Step 1: Every rank sends its data to every other rank
     *             concurrently (N*(N-1) simultaneous sends).
     *     Step 2: Every rank reduces the N received chunks locally.
     *
     *   BEST FOR: single-server 8-NPU with Full Mesh HCCS.
     *   TRADE-OFF: O(N^2) concurrent sends — link contention above ~8.
     */
    if (send_buf == NULL || recv_buf == NULL || comm == NULL)
        return HCCL_ERR_INVALID_ARG;
    if (!is_supported_data_type(data_type)) return HCCL_ERR_NOT_SUPPORTED;
    if (!is_supported_reduce_op(op))   return HCCL_ERR_NOT_SUPPORTED;
    if (count == 0)                    return HCCL_ERR_INVALID_ARG;

    {
        hcclCommInternal* ctx = (hcclCommInternal*) comm;
        int32_t N = ctx->num_devices;

        if (N > 64)     return HCCL_ERR_INTERNAL;

        /*
         * Mesh AllReduce — O(1) rounds on a fully-connected topology.
         *
         * Every rank sees every other rank's value directly.
         * CPU simulation: sum all stored values, broadcast to all.
         */
        return run_allreduce_reference_kernel(
            send_buf, recv_buf, count, data_type, op, comm
        );
    }
}

hcclResult_t mesh_reducescatter(
    const void*     send_buf,
    void*           recv_buf,
    size_t          recv_count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
)
{
    hcclCommInternal* ctx = NULL;
    size_t input_elems = 0;
    size_t output_elems = 0;
    hcclResult_t rc = validate_reducescatter_args(
        send_buf, recv_buf, recv_count, data_type, op, comm,
        &ctx, &input_elems, &output_elems
    );
    if (rc != HCCL_SUCCESS) {
        return rc;
    }

    {
        float* staged = (float*) calloc(output_elems, sizeof(float));
        int32_t N = ctx->num_devices;
        size_t C = recv_count;

        (void)input_elems;
        if (staged == NULL) {
            return HCCL_ERR_INTERNAL;
        }

        /*
         * Mesh ReduceScatter CPU simulation. Every source rank has a
         * shard for every destination rank. On a full mesh, each dst
         * can receive all source shards directly and reduce locally.
         */
        for (int32_t dst = 0; dst < N; dst++) {
            for (size_t elem = 0; elem < C; elem++) {
                staged[(size_t)dst * C + elem] = reduce_identity(op);
            }
            for (int32_t src = 0; src < N; src++) {
                for (size_t elem = 0; elem < C; elem++) {
                    size_t in_idx =
                        ((size_t)src * (size_t)N + (size_t)dst) * C + elem;
                    size_t out_idx = (size_t)dst * C + elem;
                    staged[out_idx] =
                        apply_reduce_op(
                            staged[out_idx],
                            load_value(send_buf, in_idx, data_type),
                            op
                        );
                }
            }
        }

        for (size_t out_idx = 0; out_idx < output_elems; out_idx++) {
            store_value(recv_buf, out_idx, data_type, staged[out_idx]);
        }
        free(staged);
        return HCCL_SUCCESS;
    }
}

/* Internal Ring control path; CPU_SIM retains the shared semantic kernel. */
hcclResult_t hccl_internal_ring_reducescatter(
    const void* send_buf, void* recv_buf, size_t recv_count,
    hcclDataType_t data_type, hcclRedOp_t op, hcclComm_t comm)
{
    hcclCommInternal* ctx = NULL;
    size_t input_elems = 0;
    size_t output_elems = 0;
    hcclResult_t rc = validate_reducescatter_args(
        send_buf, recv_buf, recv_count, data_type, op, comm,
        &ctx, &input_elems, &output_elems);
    (void)input_elems;
    (void)output_elems;
    if (rc != HCCL_SUCCESS) return rc;
    rc = validate_internal_ring_schedule(
        "ReduceScatter", ctx, recv_count, data_type, op);
    if (rc != HCCL_SUCCESS) return rc;
    return mesh_reducescatter(
        send_buf, recv_buf, recv_count, data_type, op, comm);
}

/* ================================================================== */
/*  NHR AllReduce                                                     */
/* ================================================================== */

hcclResult_t nhr_allreduce(
    const void*     send_buf,
    void*           recv_buf,
    size_t          count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
)
{
    /*
     * ALGORITHM (Non-uniform Hierarchical Ring):
     *   When links have asymmetric bandwidth (e.g. mixed HCCS + RoCE),
     *   assign larger chunks to higher-bandwidth links and smaller
     *   chunks to lower-bandwidth links.
     *
     *   Step 1: Probe per-link bandwidth via hcclGetTopology.
     *   Step 2: Assign chunk sizes proportional to link bandwidth.
     *   Step 3: Run a ring with non-uniform chunks.
     *
     *   BEST FOR: heterogeneous clusters (910A2 + 910A3 mixed).
     */
    /* ---- arg validation ---- */
    if (send_buf == NULL || recv_buf == NULL || comm == NULL)
        return HCCL_ERR_INVALID_ARG;
    if (!is_supported_data_type(data_type)) return HCCL_ERR_NOT_SUPPORTED;
    if (!is_supported_reduce_op(op))   return HCCL_ERR_NOT_SUPPORTED;
    if (count == 0)                    return HCCL_ERR_INVALID_ARG;

    {
        hcclCommInternal* ctx = (hcclCommInternal*) comm;
        int32_t N = ctx->num_devices;

        if (N > 64)     return HCCL_ERR_INTERNAL;

        return run_allreduce_reference_kernel(
            send_buf, recv_buf, count, data_type, op, comm
        );
    }
}

/* ================================================================== */
/*  Fat-Tree AllReduce                                                */
/* ================================================================== */

hcclResult_t fattree_allreduce(
    const void*     send_buf,
    void*           recv_buf,
    size_t          count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
)
{
    if (send_buf == NULL || recv_buf == NULL || comm == NULL)
        return HCCL_ERR_INVALID_ARG;
    if (!is_supported_data_type(data_type)) return HCCL_ERR_NOT_SUPPORTED;
    if (!is_supported_reduce_op(op))   return HCCL_ERR_NOT_SUPPORTED;
    if (count == 0)                    return HCCL_ERR_INVALID_ARG;

    {
        hcclCommInternal* ctx = (hcclCommInternal*) comm;
        int32_t N = ctx->num_devices;

        if (N > 64)     return HCCL_ERR_INTERNAL;

        return run_allreduce_reference_kernel(
            send_buf, recv_buf, count, data_type, op, comm
        );
    }
}
