/**
 * @file    test_topology.c
 * @brief   Unit test for communicator init, topology discovery, and destroy.
 *
 * Build (from hcccl/):
 *   mkdir -p build && cd build
 *   cmake .. && make
 *   ./test_topology
 */

#include "hccl_comm.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int tests_run  = 0;
static int tests_pass = 0;
static int tests_fail = 0;

#define TEST(name)  do {                                    \
    tests_run++;                                            \
    printf("  %-52s ", name);                               \
} while (0)

#define PASS()  do {                                        \
    printf("PASS\n");                                       \
    tests_pass++;                                           \
} while (0)

#define FAIL(msg)  do {                                     \
    printf("FAIL — %s\n", msg);                             \
    tests_fail++;                                           \
} while (0)

/* ------------------------------------------------------------------ */
/*  Test: valid hcclCommInit                                          */
/* ------------------------------------------------------------------ */

static void test_comm_init_valid(void)
{
    TEST("hcclCommInit (valid 8 devices)");

    int32_t ids[] = {0, 1, 2, 3, 4, 5, 6, 7};
    hcclComm_t comm = NULL;
    hcclResult_t rc = hcclCommInit(&comm, 8, ids);

    if (rc != HCCL_SUCCESS)          { FAIL("rc != HCCL_SUCCESS"); return; }
    if (comm == NULL)                { FAIL("comm is NULL");       return; }

    hcclCommDestroy(comm);
    PASS();
}

/* ------------------------------------------------------------------ */
/*  Test: hcclCommInit rejects invalid args                           */
/* ------------------------------------------------------------------ */

static void test_comm_init_null_comm(void)
{
    TEST("hcclCommInit (NULL comm pointer)");

    int32_t ids[] = {0, 1};
    hcclResult_t rc = hcclCommInit(NULL, 2, ids);

    if (rc == HCCL_ERR_INVALID_ARG)  { PASS(); }
    else                             { FAIL("expected INVALID_ARG"); }
}

static void test_comm_init_zero_devices(void)
{
    TEST("hcclCommInit (zero devices)");

    int32_t ids[] = {0};
    hcclComm_t comm = NULL;
    hcclResult_t rc = hcclCommInit(&comm, 0, ids);

    if (rc == HCCL_ERR_INVALID_ARG)  { PASS(); }
    else                             { FAIL("expected INVALID_ARG"); }
}

static void test_comm_init_null_ids(void)
{
    TEST("hcclCommInit (NULL device_ids)");

    hcclComm_t comm = NULL;
    hcclResult_t rc = hcclCommInit(&comm, 4, NULL);

    if (rc == HCCL_ERR_INVALID_ARG)  { PASS(); }
    else                             { FAIL("expected INVALID_ARG"); }
}

/* ------------------------------------------------------------------ */
/*  Test: hcclCommDestroy rejects NULL                                */
/* ------------------------------------------------------------------ */

static void test_comm_destroy_null(void)
{
    TEST("hcclCommDestroy (NULL)");

    hcclResult_t rc = hcclCommDestroy(NULL);

    if (rc == HCCL_ERR_INVALID_ARG)  { PASS(); }
    else                             { FAIL("expected INVALID_ARG"); }
}

/* ------------------------------------------------------------------ */
/*  Test: hcclGetTopology — Full Mesh for 4 devices                   */
/* ------------------------------------------------------------------ */

static void test_topology_full_mesh_4(void)
{
    TEST("hcclGetTopology (4-device Full Mesh)");

    int32_t ids[] = {0, 1, 2, 3};
    hcclComm_t comm = NULL;
    hcclCommInit(&comm, 4, ids);

    hcclTopology_t* topo = NULL;
    hcclResult_t rc = hcclGetTopology(comm, &topo);

    if (rc != HCCL_SUCCESS)          { FAIL("rc != HCCL_SUCCESS");            goto out; }
    if (topo == NULL)                { FAIL("topo is NULL");                  goto out; }
    if (topo->num_devices != 4)      { FAIL("num_devices != 4");              goto out; }
    if (topo->num_links != 12)       { FAIL("num_links != 12 (4*3)");        goto out; }

    /* Check first link properties. */
    hcclLinkInfo_t* l0 = &topo->links[0];
    if (l0->src_device != 0)         { FAIL("first link src != 0");           goto out; }
    if (strcmp(l0->link_type, "HCCS") != 0)
                                     { FAIL("link_type != HCCS");              goto out; }
    if (l0->bandwidth_gbps != 100.0f){ FAIL("bandwidth != 100");              goto out; }
    if (l0->latency_us != 1.0f)      { FAIL("latency != 1");                  goto out; }
    if (l0->healthy != 1)            { FAIL("healthy != 1");                  goto out; }

    /* No self-loops. */
    for (int32_t i = 0; i < topo->num_links; i++) {
        if (topo->links[i].src_device == topo->links[i].dst_device) {
            FAIL("found self-loop");
            goto out;
        }
    }

    /* Every src->dst pair (src!=dst) should be present exactly once. */
    int count[4][4];
    memset(count, 0, sizeof(count));
    for (int32_t i = 0; i < topo->num_links; i++) {
        int32_t s = topo->links[i].src_device;
        int32_t d = topo->links[i].dst_device;
        count[s][d]++;
    }
    for (int32_t s = 0; s < 4; s++) {
        for (int32_t d = 0; d < 4; d++) {
            if (s == d && count[s][d] != 0) { FAIL("unexpected self-link");   goto out; }
            if (s != d && count[s][d] != 1) { FAIL("missing src->dst link");  goto out; }
        }
    }

    hcclFreeTopology(topo);
    hcclCommDestroy(comm);
    PASS();
    return;

out:
    if (topo) hcclFreeTopology(topo);
    if (comm) hcclCommDestroy(comm);
}

/* ------------------------------------------------------------------ */
/*  Test: hcclGetTopology handles 1 device                            */
/* ------------------------------------------------------------------ */

static void test_topology_single_device(void)
{
    TEST("hcclGetTopology (1 device, 0 links)");

    int32_t ids[] = {0};
    hcclComm_t comm = NULL;
    hcclCommInit(&comm, 1, ids);

    hcclTopology_t* topo = NULL;
    hcclResult_t rc = hcclGetTopology(comm, &topo);

    if (rc != HCCL_SUCCESS)          { FAIL("rc != HCCL_SUCCESS");            goto out; }
    if (topo == NULL)                { FAIL("topo is NULL");                  goto out; }
    if (topo->num_devices != 1)      { FAIL("num_devices != 1");              goto out; }
    if (topo->num_links != 0)        { FAIL("num_links != 0");                goto out; }

    hcclFreeTopology(topo);
    hcclCommDestroy(comm);
    PASS();
    return;

out:
    if (topo) hcclFreeTopology(topo);
    if (comm) hcclCommDestroy(comm);
}

/* ------------------------------------------------------------------ */
/*  Test: hcclGetTopology rejects NULL args                           */
/* ------------------------------------------------------------------ */

static void test_topology_null_comm(void)
{
    TEST("hcclGetTopology (NULL comm)");

    hcclTopology_t* topo = NULL;
    hcclResult_t rc = hcclGetTopology(NULL, &topo);

    if (rc == HCCL_ERR_INVALID_ARG)  { PASS(); }
    else                             { FAIL("expected INVALID_ARG"); }
}

static void test_topology_null_topo(void)
{
    TEST("hcclGetTopology (NULL topo pointer)");

    int32_t ids[] = {0, 1};
    hcclComm_t comm = NULL;
    hcclCommInit(&comm, 2, ids);

    hcclResult_t rc = hcclGetTopology(comm, NULL);

    if (rc == HCCL_ERR_INVALID_ARG)  { PASS(); }
    else                             { FAIL("expected INVALID_ARG"); }

    hcclCommDestroy(comm);
}

/* ------------------------------------------------------------------ */
/*  Driver                                                            */
/* ------------------------------------------------------------------ */

int main(void)
{
    printf("\n");
    printf("============================================\n");
    printf(" test_topology — communicator + topology\n");
    printf("============================================\n\n");

    test_comm_init_valid();
    test_comm_init_null_comm();
    test_comm_init_zero_devices();
    test_comm_init_null_ids();
    test_comm_destroy_null();
    test_topology_full_mesh_4();
    test_topology_single_device();
    test_topology_null_comm();
    test_topology_null_topo();

    printf("\n");
    printf("============================================\n");
    printf(" Results: %d run, %d passed, %d failed\n",
           tests_run, tests_pass, tests_fail);
    printf("============================================\n\n");

    return tests_fail > 0 ? 1 : 0;
}
