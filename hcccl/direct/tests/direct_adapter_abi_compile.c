#include "hccl_direct_adapter.h"

_Static_assert(HCCL_DIRECT_STATUS_SUCCESS == 0, "direct ABI status values are stable");
_Static_assert(HCCL_DIRECT_SESSION_NEW == 0, "direct ABI state values are stable");

void hccl_direct_adapter_c_abi_compile_probe(void)
{
    hccl_direct_session_t *session = 0;
    hccl_direct_error_t error = {0};
    (void) session;
    (void) error;
}
