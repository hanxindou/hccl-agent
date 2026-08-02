// G2-F-3 ELF-link audit artifact.  Do not execute this program: it exists only
// for CMake/linker/readelf/nm/ldd inspection and makes no ACL/HCCL API call.

#include <cstdint>

#include <acl/acl_rt.h>
#include <hccl/hccl.h>
#include <hccl/hccl_comm.h>

namespace {

// Volatile function-address anchors require each frozen official DSO at link
// time without invoking a function from it.  The executable is never run.
volatile std::uintptr_t kOfficialSymbolAnchors[] = {
    reinterpret_cast<std::uintptr_t>(&HcclAllReduce),
    reinterpret_cast<std::uintptr_t>(&HcclAllGather),
    reinterpret_cast<std::uintptr_t>(&HcclReduceScatter),
    reinterpret_cast<std::uintptr_t>(&HcclCommInitClusterInfo),
    reinterpret_cast<std::uintptr_t>(&HcclCommDestroy),
    reinterpret_cast<std::uintptr_t>(&aclInit),
    reinterpret_cast<std::uintptr_t>(&aclFinalize),
    reinterpret_cast<std::uintptr_t>(&aclrtSetDevice),
    reinterpret_cast<std::uintptr_t>(&aclrtCreateContext),
    reinterpret_cast<std::uintptr_t>(&aclrtCreateStream),
    reinterpret_cast<std::uintptr_t>(&aclrtMalloc),
    reinterpret_cast<std::uintptr_t>(&aclrtMemcpy),
};

}  // namespace

int main() {
    // Keep anchors in the binary.  This line does not call an official API.
    return kOfficialSymbolAnchors[0] == 0 ? 1 : 0;
}
