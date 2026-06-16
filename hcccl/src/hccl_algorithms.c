/**
 * @file    hccl_algorithms.c
 * @brief   HCCL collective algorithm implementations.
 *
 * STATUS: ring_allreduce — CPU-simulated, zero external dependencies.
 *         All other functions remain STUBS.
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
    /*
     * ALGORITHM (log2(N) steps):
     *   For step s in 0..log2(N)-1:
     *     distance = 2^s
     *     Each rank i exchanges ALL data accumulated so far with
     *     rank (i XOR distance).
     *
     *   After log2(N) steps, every rank has data from all N ranks.
     */
    (void)send_buf;
    (void)recv_buf;
    (void)send_count;
    (void)data_type;
    (void)comm;
    fprintf(stderr, "[STUB] butterfly_allgather — not implemented.\n");
    return HCCL_ERR_NOT_SUPPORTED;
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
    /*
     * ALGORITHM (two-level hierarchical):
     *   Level 1 — Intra-rack (Full Mesh via HCCS):
     *     Each rack of 8 NPUs does a Mesh AllReduce independently.
     *   Level 2 — Inter-rack (Ring via RoCE):
     *     Rack representatives exchange reduced results via a ring.
     *
     *   BEST FOR: multi-server clusters (64-1024 NPUs).
     */
    (void)send_buf;
    (void)recv_buf;
    (void)count;
    (void)data_type;
    (void)op;
    (void)comm;
    fprintf(stderr, "[STUB] fattree_allreduce — not implemented.\n");
    return HCCL_ERR_NOT_SUPPORTED;
}
