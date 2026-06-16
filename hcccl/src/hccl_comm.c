/**
 * @file    hccl_comm.c
 * @brief   CPU-simulated HCCL communicator lifecycle and topology.
 *
 * This is a self-contained, CPU-only implementation of the communicator
 * infrastructure.  It does NOT require the Ascend CANN SDK or NPU
 * hardware — it allocates ordinary host memory and returns simulated
 * topology data so the rest of the framework can be developed and tested
 * on a plain Linux machine.
 *
 * When real hardware is available, replace each function body with the
 * corresponding HCOMM driver calls.
 */

#include "hccl_comm.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ================================================================== */
/*  Internal communicator struct  (hidden behind void*)                */
/* ================================================================== */

typedef struct {
    int32_t   num_devices;   /* number of NPU devices (ranks)        */
    int32_t*  device_ids;    /* array of device IDs, length == num_devices */
    int32_t   current_rank;  /* which rank is calling (set via hcclSetRank) */
    float*    rank_values;   /* [num_devices] per-rank input for simulation */
    float*    rank_results;  /* [num_devices] per-rank result for simulation */
    int32_t   calls_received;/* how many ranks have submitted data this round */
} hcclCommInternal;

/* ================================================================== */
/*  Communicator lifecycle                                            */
/* ================================================================== */

hcclResult_t hcclCommInit(
    hcclComm_t*     comm,
    int32_t         num_devices,
    const int32_t*  device_ids
)
{
    if (comm == NULL || num_devices <= 0 || device_ids == NULL) {
        return HCCL_ERR_INVALID_ARG;
    }

    hcclCommInternal* ctx = (hcclCommInternal*) malloc(
        sizeof(hcclCommInternal)
    );
    if (ctx == NULL) {
        return HCCL_ERR_INTERNAL;
    }

    ctx->num_devices = num_devices;

    ctx->device_ids = (int32_t*) malloc(
        (size_t)num_devices * sizeof(int32_t)
    );
    if (ctx->device_ids == NULL) {
        free(ctx);
        return HCCL_ERR_INTERNAL;
    }

    memcpy(ctx->device_ids, device_ids,
           (size_t)num_devices * sizeof(int32_t));

    /* Simulation buffers — one float per rank. */
    ctx->rank_values = (float*) calloc(
        (size_t)num_devices, sizeof(float)
    );
    ctx->rank_results = (float*) calloc(
        (size_t)num_devices, sizeof(float)
    );
    if (ctx->rank_values == NULL || ctx->rank_results == NULL) {
        free(ctx->rank_values);
        free(ctx->rank_results);
        free(ctx->device_ids);
        free(ctx);
        return HCCL_ERR_INTERNAL;
    }

    ctx->current_rank   = 0;
    ctx->calls_received = 0;

    *comm = (hcclComm_t) ctx;
    return HCCL_SUCCESS;
}

hcclResult_t hcclCommDestroy(hcclComm_t comm)
{
    if (comm == NULL) {
        return HCCL_ERR_INVALID_ARG;
    }

    hcclCommInternal* ctx = (hcclCommInternal*) comm;
    free(ctx->device_ids);
    free(ctx->rank_values);
    free(ctx->rank_results);
    free(ctx);
    return HCCL_SUCCESS;
}

/* ------------------------------------------------------------------ */
/*  Rank selection  (CPU simulation helper)                           */
/* ------------------------------------------------------------------ */

hcclResult_t hcclSetRank(hcclComm_t comm, int32_t rank)
{
    if (comm == NULL) {
        return HCCL_ERR_INVALID_ARG;
    }

    hcclCommInternal* ctx = (hcclCommInternal*) comm;
    if (rank < 0 || rank >= ctx->num_devices) {
        return HCCL_ERR_INVALID_ARG;
    }

    ctx->current_rank = rank;
    return HCCL_SUCCESS;
}

/* ================================================================== */
/*  Topology discovery  (simulated Full Mesh)                         */
/* ================================================================== */

hcclResult_t hcclGetTopology(
    hcclComm_t       comm,
    hcclTopology_t** topo
)
{
    if (comm == NULL || topo == NULL) {
        return HCCL_ERR_INVALID_ARG;
    }

    hcclCommInternal* ctx = (hcclCommInternal*) comm;
    int32_t N = ctx->num_devices;

    /*
     * Simulated Full Mesh: every device has a bidirectional link to
     * every other device, so there are N*(N-1) directed links total.
     */
    int32_t num_links = N * (N - 1);

    hcclTopology_t* t = (hcclTopology_t*) malloc(sizeof(hcclTopology_t));
    if (t == NULL) {
        return HCCL_ERR_INTERNAL;
    }

    t->num_devices = N;
    t->num_links   = num_links;

    t->links = (hcclLinkInfo_t*) malloc(
        (size_t)num_links * sizeof(hcclLinkInfo_t)
    );
    if (t->links == NULL) {
        free(t);
        return HCCL_ERR_INTERNAL;
    }

    int32_t idx = 0;
    for (int32_t src = 0; src < N; src++) {
        for (int32_t dst = 0; dst < N; dst++) {
            if (src == dst) {
                continue;  /* no self-loop */
            }

            hcclLinkInfo_t* link = &t->links[idx];
            link->src_device     = src;
            link->dst_device     = dst;
            link->bandwidth_gbps = 100.0f;
            link->latency_us     = 1.0f;
            link->ber            = 1e-12f;
            link->healthy        = 1;

            /* Snprintf is safer: always NUL-terminated. */
            snprintf(link->link_type, sizeof(link->link_type),
                     "HCCS");

            idx++;
        }
    }

    *topo = t;
    return HCCL_SUCCESS;
}

void hcclFreeTopology(hcclTopology_t* topo)
{
    if (topo) {
        free(topo->links);
        free(topo);
    }
}

/* ================================================================== */
/*  Plugin discovery  (unchanged)                                     */
/* ================================================================== */

const char* hcclPluginGetVersion(void)
{
    return "0.1.0-prototype";
}

const char* hcclPluginGetAlgorithms(void)
{
    return "RingAllReduce,Butterfly,Mesh,NHR,FatTree";
}
