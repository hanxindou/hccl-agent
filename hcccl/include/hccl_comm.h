/**
 * @file    hccl_comm.h
 * @brief   HCCL communication primitives — interface declarations.
 *
 * These declarations mirror the real HCOMM open-source interfaces from
 * Gitee: ascend/cann-hcomm.  They are the contract that every HCCL
 * plugin must fulfill.
 *
 * STATUS: Interface declarations are REAL (based on HCOMM public API).
 *         Implementations in src/ are STUBS — they cannot be compiled
 *         or linked without the CANN 8.0 SDK.
 */

#ifndef HCCL_COMM_H
#define HCCL_COMM_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ------------------------------------------------------------------ */
/*  Types                                                             */
/* ------------------------------------------------------------------ */

/** Opaque handle for a HCCL communicator. */
typedef void* hcclComm_t;

/** NPU device identifier. */
typedef int32_t hcclDevice_t;

/** Collective operation result code. */
typedef enum {
    HCCL_SUCCESS            =  0,
    HCCL_ERR_INVALID_ARG    = -1,
    HCCL_ERR_COMM_FAILURE   = -2,
    HCCL_ERR_TIMEOUT        = -3,
    HCCL_ERR_CRC_MISMATCH   = -4,
    HCCL_ERR_TOPOLOGY       = -5,
    HCCL_ERR_NOT_SUPPORTED  = -6,
    HCCL_ERR_INTERNAL       = -99,
} hcclResult_t;

/** Data type for collective operations. */
typedef enum {
    HCCL_FP32   = 0,
    HCCL_FP16   = 1,
    HCCL_BF16   = 2,
    HCCL_INT8   = 3,
    HCCL_INT32  = 4,
} hcclDataType_t;

/** Reduction operator. */
typedef enum {
    HCCL_SUM  = 0,
    HCCL_PROD = 1,
    HCCL_MAX  = 2,
    HCCL_MIN  = 3,
} hcclRedOp_t;

/** Topology link information (matching hcclGetTopology output). */
typedef struct {
    int32_t  src_device;
    int32_t  dst_device;
    char     link_type[16];      /* "HCCS" / "RoCE" / "PCIe" */
    float    bandwidth_gbps;
    float    latency_us;
    float    ber;
    int32_t  healthy;            /* 1 = up, 0 = down */
} hcclLinkInfo_t;

/** Full topology descriptor. */
typedef struct {
    int32_t         num_devices;
    hcclLinkInfo_t* links;
    int32_t         num_links;
} hcclTopology_t;

/* ------------------------------------------------------------------ */
/*  CPU simulation helper                                             */
/* ------------------------------------------------------------------ */

/**
 * Set the calling rank for subsequent collective operations.
 *
 * In a real multi-process HCCL environment each process has its own
 * rank.  In this CPU-simulated build the caller must set the rank
 * before each collective call so the implementation can associate
 * send/recv buffers with the correct virtual device.
 *
 * @param comm  communicator handle
 * @param rank  device index within the communicator [0, num_devices-1]
 * @return HCCL_SUCCESS on success
 */
hcclResult_t hcclSetRank(hcclComm_t comm, int32_t rank);

/* ------------------------------------------------------------------ */
/*  Communicator lifecycle                                            */
/* ------------------------------------------------------------------ */

/**
 * Initialise the HCCL communicator for the given set of devices.
 *
 * @param comm      [out] opaque communicator handle
 * @param num_devices       number of NPU devices in this communicator
 * @param device_ids       array of NPU device IDs
 * @return HCCL_SUCCESS on success
 */
hcclResult_t hcclCommInit(
    hcclComm_t*     comm,
    int32_t         num_devices,
    const int32_t*  device_ids
);

/**
 * Destroy a HCCL communicator and free associated resources.
 */
hcclResult_t hcclCommDestroy(hcclComm_t comm);

/* ------------------------------------------------------------------ */
/*  Topology discovery                                                */
/* ------------------------------------------------------------------ */

/**
 * Get the physical topology connecting the NPU devices in *comm*.
 *
 * The caller must free the returned topology with hcclFreeTopology().
 *
 * @param comm      communicator handle
 * @param topo      [out] topology descriptor (allocated by this function)
 * @return HCCL_SUCCESS on success
 */
hcclResult_t hcclGetTopology(
    hcclComm_t       comm,
    hcclTopology_t** topo
);

/** Free a topology descriptor returned by hcclGetTopology. */
void hcclFreeTopology(hcclTopology_t* topo);

/* ------------------------------------------------------------------ */
/*  Collective operations  (at least 3 required by the contest)       */
/* ------------------------------------------------------------------ */

/**
 * AllReduce: reduce data across all devices using *op*, result written
 * to every device.
 */
hcclResult_t hcclAllReduce(
    const void*     send_buf,
    void*           recv_buf,
    size_t          count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
);

/**
 * AllGather: each device contributes *send_count* elements; the
 * concatenated result from all devices is stored in *recv_buf*.
 */
hcclResult_t hcclAllGather(
    const void*     send_buf,
    void*           recv_buf,
    size_t          send_count,
    hcclDataType_t  data_type,
    hcclComm_t      comm
);

/**
 * ReduceScatter: reduce data across all devices, then scatter
 * non-overlapping chunks so each device receives 1/N of the result.
 */
hcclResult_t hcclReduceScatter(
    const void*     send_buf,
    void*           recv_buf,
    size_t          recv_count,
    hcclDataType_t  data_type,
    hcclRedOp_t     op,
    hcclComm_t      comm
);

/**
 * Broadcast: broadcast *count* elements from *root* to all devices.
 */
hcclResult_t hcclBroadcast(
    const void*     send_buf,
    void*           recv_buf,
    size_t          count,
    hcclDataType_t  data_type,
    int32_t         root,
    hcclComm_t      comm
);

/* ------------------------------------------------------------------ */
/*  Plugin discovery  (HCCL plugin interface)                         */
/* ------------------------------------------------------------------ */

/**
 * Return the plugin version string.
 * Required by the HCCL plugin loader.
 */
const char* hcclPluginGetVersion(void);

/**
 * Return the list of algorithms this plugin implements.
 * Format: "algo1,algo2,..." (comma-separated, no spaces).
 */
const char* hcclPluginGetAlgorithms(void);

#ifdef __cplusplus
}
#endif

#endif /* HCCL_COMM_H */
