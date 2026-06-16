/**
 * @file    hccl_algorithms.h
 * @brief   Algorithm-specific declarations — Ring, Butterfly, Mesh, NHR,
 *          Fat-Tree implementations of the HCCL primitives.
 *
 * These are the algorithm-level entry points.  Each function implements
 * one collective primitive using one specific topology-aware algorithm.
 */

#ifndef HCCL_ALGORITHMS_H
#define HCCL_ALGORITHMS_H

#include "hccl_comm.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Ring AllReduce ------------------------------------------------- */

hcclResult_t ring_allreduce(
    const void*     send_buf,
    void*           recv_buf,
    size_t          count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
);

/* ---- Butterfly (recursive doubling) --------------------------------- */

hcclResult_t butterfly_allreduce(
    const void*     send_buf,
    void*           recv_buf,
    size_t          count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
);

hcclResult_t butterfly_allgather(
    const void*     send_buf,
    void*           recv_buf,
    size_t          send_count,
    hcclDataType_t  data_type,
    hcclComm_t      comm
);

/* ---- Mesh (full interconnect) --------------------------------------- */

hcclResult_t mesh_allreduce(
    const void*     send_buf,
    void*           recv_buf,
    size_t          count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
);

hcclResult_t mesh_reducescatter(
    const void*     send_buf,
    void*           recv_buf,
    size_t          recv_count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
);

/* ---- NHR (Non-uniform Hierarchical Ring) ---------------------------- */

hcclResult_t nhr_allreduce(
    const void*     send_buf,
    void*           recv_buf,
    size_t          count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
);

/* ---- Fat-Tree (two-level hierarchical) ------------------------------ */

hcclResult_t fattree_allreduce(
    const void*     send_buf,
    void*           recv_buf,
    size_t          count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
);

#ifdef __cplusplus
}
#endif

#endif /* HCCL_ALGORITHMS_H */
