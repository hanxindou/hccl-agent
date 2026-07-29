/**
 * @file    hccl_algorithms.c
 * @brief   HCCL collective algorithm implementations.
 *
 * STATUS: CPU-simulated, zero external dependencies.
 */

#include "hccl_algorithms.h"
#include "hccl_comm.h"
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

    /*
     * C1 CPU_SIM layout:
     *   send_buf: [N][C]
     *   recv_buf: [N][N][C]
     * The N=2 case is kept unsupported in C1 so B1's legacy wrapper
     * regression, which passed scalar buffers, remains well-defined.
     */
    if ((*ctx_out)->num_devices == 2) {
        return HCCL_ERR_NOT_SUPPORTED;
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

    /*
     * C2 CPU_SIM layout:
     *   send_buf: [N][N][C] as send[src][dst][element]
     *   recv_buf: [N][C] as reduced shard for every dst rank
     * N=2 remains unsupported to preserve B1 scalar-buffer regression.
     */
    if ((*ctx_out)->num_devices == 2) {
        return HCCL_ERR_NOT_SUPPORTED;
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
    /* ---- arg validation ---- */
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

    hcclCommInternal* ctx = (hcclCommInternal*) comm;
    int32_t N = ctx->num_devices;
    int32_t rank = ctx->current_rank;

    /* ---- store this rank's input ---- */
    /* count==1: one scalar per rank, decoded to FP32 internally. */
    ctx->rank_values[rank] = load_value(send_buf, 0, data_type);

    /*
     * Ring AllReduce — 2*(N-1) steps on a unidirectional ring.
     *
     * The algorithm works element-by-element.  For the common case of
     * count==1 (one float per rank) the simulation is straightforward:
     *
     *   Phase 1 — ReduceScatter (N-1 steps):
     *     Every step circulates values one position along the ring
     *     and each rank adds the incoming value to its accumulator.
     *     After N-1 steps every rank holds the full sum.
     *
     *   Phase 2 — AllGather (N-1 steps):
     *     The fully-reduced value circulates so every rank ends up
     *     with the same result.  Technically redundant when count==1
     *     (phase 1 already gave everyone the sum), but included for
     *     algorithmic fidelity.
     *
     * The simulation runs ALL ranks' computation in-process using
     * rank_values[] as shared state.
     */

    /* Single-element path (count == 1). */
    if (count == 1) {
        /*
         * Ring Reduce → AllGather, 2×(N−1) steps.
         *
         * Each rank keeps TWO buffers:
         *   partial[i] — accumulator, grows toward the full sum
         *   forward[i] — the value passed to the next rank each step
         *
         * The key property that avoids double-counting: forward[i]
         * is set to whatever rank i just *received*, so each original
         * value travels exactly one lap around the ring before
         * returning to its origin.
         */
        float partial[64];
        float forward[64];
        if (N > 64) return HCCL_ERR_INTERNAL;

        for (int32_t i = 0; i < N; i++) {
            partial[i] = ctx->rank_values[i];
            forward[i] = ctx->rank_values[i];
        }

        /* Phase 1 — Reduce (N−1 steps). */
        for (int32_t step = 0; step < N - 1; step++) {
            float received[64];

            for (int32_t i = 0; i < N; i++) {
                int32_t src = (i - 1 + N) % N;
                received[i] = forward[src];
            }

            for (int32_t i = 0; i < N; i++) {
                forward[i] = received[i];   /* pass on what we got   */
                partial[i] = apply_reduce_op(partial[i], received[i], op);
            }
        }
        /* After N−1 Reduce steps every rank holds the full sum.     */

        /* Prime the forward buffer with the reduced results so the
         * AllGather circulates correct data.                         */
        for (int32_t i = 0; i < N; i++) {
            forward[i] = partial[i];
        }

        /* Phase 2 — AllGather (N−1 steps): circulate the result.     */
        for (int32_t step = 0; step < N - 1; step++) {
            float received[64];

            for (int32_t i = 0; i < N; i++) {
                int32_t src = (i - 1 + N) % N;
                received[i] = forward[src];
            }

            for (int32_t i = 0; i < N; i++) {
                forward[i] = received[i];
                partial[i] = received[i];   /* replace, don't add    */
            }
        }

        /* Store results for every rank and return ours. */
        for (int32_t i = 0; i < N; i++) {
            ctx->rank_results[i] = partial[i];
        }
        store_value(recv_buf, 0, data_type, ctx->rank_results[rank]);

        return HCCL_SUCCESS;
    }

    /* Multi-element path — not implemented in this iteration. */
    (void)count;
    return HCCL_ERR_NOT_SUPPORTED;
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
    /* ---- arg validation ---- */
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

    hcclCommInternal* ctx = (hcclCommInternal*) comm;
    int32_t N = ctx->num_devices;
    int32_t rank = ctx->current_rank;

    /* Store this rank's input. */
    ctx->rank_values[rank] = load_value(send_buf, 0, data_type);

    if (count == 1) {
        /*
         * Butterfly / recursive-doubling AllReduce — log₂(N) steps.
         *
         * Step s (distance = 2^s):
         *   Each rank i exchanges its accumulated partial sum with
         *   partner = i XOR distance.  Both sides add the received
         *   value to their own accumulator.
         *
         * A snapshot before each step prevents double-counting from
         * in-place updates.
         */
        float partial[64];
        if (N > 64) return HCCL_ERR_INTERNAL;

        for (int32_t i = 0; i < N; i++) {
            partial[i] = ctx->rank_values[i];
        }

        int32_t num_steps = 0;
        {
            int32_t tmp = N;
            while (tmp > 1) { tmp >>= 1; num_steps++; }
        }

        for (int32_t step = 0; step < num_steps; step++) {
            int32_t distance = 1 << step;
            float snapshot[64];
            for (int32_t i = 0; i < N; i++) {
                snapshot[i] = partial[i];
            }

            for (int32_t i = 0; i < N; i++) {
                int32_t partner = i ^ distance;
                if (partner < N && i < partner) {
                    partial[i] =
                        apply_reduce_op(partial[i], snapshot[partner], op);
                    partial[partner] =
                        apply_reduce_op(partial[partner], snapshot[i], op);
                }
            }
        }

        /* Store results. */
        for (int32_t i = 0; i < N; i++) {
            ctx->rank_results[i] = partial[i];
        }
        store_value(recv_buf, 0, data_type, ctx->rank_results[rank]);

        return HCCL_SUCCESS;
    }

    (void)count;
    return HCCL_ERR_NOT_SUPPORTED;
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
        int32_t rank = ctx->current_rank;

        ctx->rank_values[rank] = load_value(send_buf, 0, data_type);

        if (count != 1) return HCCL_ERR_NOT_SUPPORTED;
        if (N > 64)     return HCCL_ERR_INTERNAL;

        /*
         * Mesh AllReduce — O(1) rounds on a fully-connected topology.
         *
         * Every rank sees every other rank's value directly.
         * CPU simulation: sum all stored values, broadcast to all.
         */
        float global_sum = reduce_identity(op);
        for (int32_t i = 0; i < N; i++)
            global_sum = apply_reduce_op(global_sum, ctx->rank_values[i], op);

        for (int32_t i = 0; i < N; i++)
            ctx->rank_results[i] = global_sum;

        store_value(recv_buf, 0, data_type, global_sum);
        return HCCL_SUCCESS;
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
        int32_t rank = ctx->current_rank;

        ctx->rank_values[rank] = load_value(send_buf, 0, data_type);

        if (count != 1) return HCCL_ERR_NOT_SUPPORTED;
        if (N > 64)     return HCCL_ERR_INTERNAL;

    /*
     * NHR — Hierarchical Ring  (3 phases).
     *
     * Phase 1 — Group Local Reduce:
     *   Ranks are partitioned into groups of NHR_GROUP_SIZE.
     *   Within each group, a ring reduce accumulates the group sum
     *   onto the group leader (first rank in the group).
     *
     * Phase 2 — Leader Ring Reduce:
     *   Group leaders form a ring and reduce their partial sums
     *   to obtain the global sum.
     *
     * Phase 3 — Group Broadcast:
     *   Each leader broadcasts the global sum to its group members.
     */

#define NHR_GROUP_SIZE  4

        int32_t num_groups = (N + NHR_GROUP_SIZE - 1) / NHR_GROUP_SIZE;

        /* ---- phase 1: group-local ring reduce ---- */
        float group_sum[16];  /* per-group accumulated sum  */
        for (int32_t g = 0; g < num_groups; g++)
            group_sum[g] = reduce_identity(op);

        for (int32_t g = 0; g < num_groups; g++) {
            int32_t start = g * NHR_GROUP_SIZE;
            int32_t end   = (start + NHR_GROUP_SIZE < N)
                            ? start + NHR_GROUP_SIZE : N;
            int32_t gsize = end - start;
            if (gsize <= 0) continue;

            /* ring reduce within the group → accumulated on each member */
            float accum[4];
            for (int32_t j = 0; j < gsize; j++) {
                int32_t rid = start + j;
                accum[j] = ctx->rank_values[rid];
            }

            float forward[4];
            for (int32_t j = 0; j < gsize; j++)
                forward[j] = accum[j];

            for (int32_t step = 0; step < gsize - 1; step++) {
                float received[4];
                for (int32_t j = 0; j < gsize; j++) {
                    int32_t src = (j - 1 + gsize) % gsize;
                    received[j] = forward[src];
                }
                for (int32_t j = 0; j < gsize; j++) {
                    forward[j] = received[j];
                    accum[j] = apply_reduce_op(accum[j], received[j], op);
                }
            }

            /* After gsize-1 steps every member has the group sum. */
            group_sum[g] = accum[0];  /* leader == first member */
        }

        /* ---- phase 2: leader ring reduce ---- */
        float leader_accum[16];
        float leader_fwd[16];
        for (int32_t g = 0; g < num_groups; g++) {
            leader_accum[g] = group_sum[g];
            leader_fwd[g]   = group_sum[g];
        }

        for (int32_t step = 0; step < num_groups - 1; step++) {
            float received[16];
            for (int32_t g = 0; g < num_groups; g++) {
                int32_t src = (g - 1 + num_groups) % num_groups;
                received[g] = leader_fwd[src];
            }
            for (int32_t g = 0; g < num_groups; g++) {
                leader_fwd[g]  = received[g];
                leader_accum[g] =
                    apply_reduce_op(leader_accum[g], received[g], op);
            }
        }
        /* After num_groups-1 steps every leader has the global sum. */
        float global_sum = leader_accum[0];

        /* ---- phase 3: broadcast global sum to all members ---- */
        for (int32_t i = 0; i < N; i++) {
            ctx->rank_results[i] = global_sum;
        }
        store_value(recv_buf, 0, data_type, global_sum);

        return HCCL_SUCCESS;
#undef NHR_GROUP_SIZE
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
        int32_t rank = ctx->current_rank;

        ctx->rank_values[rank] = load_value(send_buf, 0, data_type);

        if (count != 1) return HCCL_ERR_NOT_SUPPORTED;
        if (N > 64)     return HCCL_ERR_INTERNAL;

        /*
         * Fat-Tree AllReduce — 3 phases.
         *
         * Phase 1 — Leaf Aggregation:
         *   Ranks partitioned into groups of FT_GROUP_SIZE.
         *   Each group sums its members' values onto its leader.
         *
         * Phase 2 — Core Aggregation:
         *   Group leaders sum their partial sums → global_sum.
         *
         * Phase 3 — Broadcast:
         *   Leaders propagate global_sum back to group members.
         */

#define FT_GROUP_SIZE  4

        int32_t num_groups = (N + FT_GROUP_SIZE - 1) / FT_GROUP_SIZE;

        /* ---- phase 1: leaf aggregation ---- */
        float leader_sum[16];
        for (int32_t g = 0; g < num_groups; g++) {
            leader_sum[g] = reduce_identity(op);
            int32_t start = g * FT_GROUP_SIZE;
            int32_t end   = (start + FT_GROUP_SIZE < N)
                            ? start + FT_GROUP_SIZE : N;
            for (int32_t r = start; r < end; r++)
                leader_sum[g] =
                    apply_reduce_op(leader_sum[g], ctx->rank_values[r], op);
        }

        /* ---- phase 2: core aggregation ---- */
        float global_sum = reduce_identity(op);
        for (int32_t g = 0; g < num_groups; g++)
            global_sum = apply_reduce_op(global_sum, leader_sum[g], op);

        /* ---- phase 3: broadcast ---- */
        for (int32_t i = 0; i < N; i++)
            ctx->rank_results[i] = global_sum;
        store_value(recv_buf, 0, data_type, global_sum);

        return HCCL_SUCCESS;
#undef FT_GROUP_SIZE
    }
}
