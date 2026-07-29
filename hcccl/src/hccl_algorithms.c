/**
 * @file    hccl_algorithms.c
 * @brief   HCCL collective algorithm implementations.
 *
 * STATUS: CPU-simulated, zero external dependencies.
 */

#include "hccl_algorithms.h"
#include "hccl_comm.h"
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
    if (data_type != HCCL_FP32) {
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
    if (output_elems > ((size_t)-1) / sizeof(float)) {
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
    if (data_type != HCCL_FP32) {
        return HCCL_ERR_NOT_SUPPORTED;
    }
    if (op != HCCL_SUM) {
        return HCCL_ERR_NOT_SUPPORTED;
    }
    if (count == 0) {
        return HCCL_ERR_INVALID_ARG;
    }

    hcclCommInternal* ctx = (hcclCommInternal*) comm;
    int32_t N = ctx->num_devices;
    int32_t rank = ctx->current_rank;

    /* ---- store this rank's input ---- */
    const float* input = (const float*) send_buf;
    /* count==1: one float per rank, direct index. */
    ctx->rank_values[rank] = input[0];

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
                partial[i] += received[i];  /* accumulate locally    */
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
        *(float*) recv_buf = ctx->rank_results[rank];

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
        const float* input = (const float*) send_buf;
        float* staged = (float*) calloc(output_elems, sizeof(float));
        int32_t N = ctx->num_devices;
        size_t C = send_count;

        (void)input_elems;
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
            memcpy(&staged[((size_t)dst * (size_t)N + (size_t)dst) * C],
                   &input[(size_t)dst * C],
                   C * sizeof(float));
        }

        for (int32_t step = 1; step < N; step++) {
            for (int32_t dst = 0; dst < N; dst++) {
                int32_t src = (dst - step + N) % N;
                memcpy(&staged[((size_t)dst * (size_t)N + (size_t)src) * C],
                       &input[(size_t)src * C],
                       C * sizeof(float));
            }
        }

        memcpy(recv_buf, staged, output_elems * sizeof(float));
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
    if (data_type != HCCL_FP32) {
        return HCCL_ERR_NOT_SUPPORTED;
    }
    if (op != HCCL_SUM) {
        return HCCL_ERR_NOT_SUPPORTED;
    }
    if (count == 0) {
        return HCCL_ERR_INVALID_ARG;
    }

    hcclCommInternal* ctx = (hcclCommInternal*) comm;
    int32_t N = ctx->num_devices;
    int32_t rank = ctx->current_rank;

    /* Store this rank's input. */
    const float* input = (const float*) send_buf;
    ctx->rank_values[rank] = input[0];

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
                    partial[i]     += snapshot[partner];
                    partial[partner] += snapshot[i];
                }
            }
        }

        /* Store results. */
        for (int32_t i = 0; i < N; i++) {
            ctx->rank_results[i] = partial[i];
        }
        *(float*) recv_buf = ctx->rank_results[rank];

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
        const float* input = (const float*) send_buf;
        float* staged = (float*) calloc(output_elems, sizeof(float));
        unsigned char* known = NULL;
        unsigned char* snapshot = NULL;
        int32_t N = ctx->num_devices;
        size_t C = send_count;

        (void)input_elems;
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
            memcpy(&staged[((size_t)dst * (size_t)N + (size_t)dst) * C],
                   &input[(size_t)dst * C],
                   C * sizeof(float));
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
                        memcpy(&staged[((size_t)dst * (size_t)N + (size_t)src) * C],
                               &input[(size_t)src * C],
                               C * sizeof(float));
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

        memcpy(recv_buf, staged, output_elems * sizeof(float));
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
    if (data_type != HCCL_FP32)   return HCCL_ERR_NOT_SUPPORTED;
    if (op != HCCL_SUM)           return HCCL_ERR_NOT_SUPPORTED;
    if (count == 0)               return HCCL_ERR_INVALID_ARG;

    {
        hcclCommInternal* ctx = (hcclCommInternal*) comm;
        int32_t N = ctx->num_devices;
        int32_t rank = ctx->current_rank;

        const float* input = (const float*) send_buf;
        ctx->rank_values[rank] = input[0];

        if (count != 1) return HCCL_ERR_NOT_SUPPORTED;
        if (N > 64)     return HCCL_ERR_INTERNAL;

        /*
         * Mesh AllReduce — O(1) rounds on a fully-connected topology.
         *
         * Every rank sees every other rank's value directly.
         * CPU simulation: sum all stored values, broadcast to all.
         */
        float global_sum = 0.0f;
        for (int32_t i = 0; i < N; i++)
            global_sum += ctx->rank_values[i];

        for (int32_t i = 0; i < N; i++)
            ctx->rank_results[i] = global_sum;

        *(float*) recv_buf = global_sum;
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
    /*
     * ALGORITHM:
     *   Each rank reduces a specific chunk (its "ownership" chunk)
     *   and receives the fully reduced result for that chunk.
     *   On Full Mesh, all ranks send their chunk-k to rank-k
     *   simultaneously in one step.
     */
    (void)send_buf;
    (void)recv_buf;
    (void)recv_count;
    (void)data_type;
    (void)op;
    (void)comm;
    fprintf(stderr, "[STUB] mesh_reducescatter — not implemented.\n");
    return HCCL_ERR_NOT_SUPPORTED;
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
    if (data_type != HCCL_FP32)   return HCCL_ERR_NOT_SUPPORTED;
    if (op != HCCL_SUM)           return HCCL_ERR_NOT_SUPPORTED;
    if (count == 0)               return HCCL_ERR_INVALID_ARG;

    {
        hcclCommInternal* ctx = (hcclCommInternal*) comm;
        int32_t N = ctx->num_devices;
        int32_t rank = ctx->current_rank;

        const float* input = (const float*) send_buf;
        ctx->rank_values[rank] = input[0];

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
            group_sum[g] = 0.0f;

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
                    accum[j]  += received[j];
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
                leader_accum[g] += received[g];
            }
        }
        /* After num_groups-1 steps every leader has the global sum. */
        float global_sum = leader_accum[0];

        /* ---- phase 3: broadcast global sum to all members ---- */
        for (int32_t i = 0; i < N; i++) {
            ctx->rank_results[i] = global_sum;
        }
        *(float*) recv_buf = global_sum;

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
    if (data_type != HCCL_FP32)   return HCCL_ERR_NOT_SUPPORTED;
    if (op != HCCL_SUM)           return HCCL_ERR_NOT_SUPPORTED;
    if (count == 0)               return HCCL_ERR_INVALID_ARG;

    {
        hcclCommInternal* ctx = (hcclCommInternal*) comm;
        int32_t N = ctx->num_devices;
        int32_t rank = ctx->current_rank;

        const float* input = (const float*) send_buf;
        ctx->rank_values[rank] = input[0];

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
            leader_sum[g] = 0.0f;
            int32_t start = g * FT_GROUP_SIZE;
            int32_t end   = (start + FT_GROUP_SIZE < N)
                            ? start + FT_GROUP_SIZE : N;
            for (int32_t r = start; r < end; r++)
                leader_sum[g] += ctx->rank_values[r];
        }

        /* ---- phase 2: core aggregation ---- */
        float global_sum = 0.0f;
        for (int32_t g = 0; g < num_groups; g++)
            global_sum += leader_sum[g];

        /* ---- phase 3: broadcast ---- */
        for (int32_t i = 0; i < N; i++)
            ctx->rank_results[i] = global_sum;
        *(float*) recv_buf = global_sum;

        return HCCL_SUCCESS;
#undef FT_GROUP_SIZE
    }
}
