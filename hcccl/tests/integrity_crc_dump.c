#include "internal/integrity_transport.h"

#include <inttypes.h>
#include <stdio.h>


int main(void)
{
    const char vector[] = "123456789";
    const unsigned char payload[] = {0, 1, 2, 3, 4, 5, 6};
    printf("{\"empty_crc32\":\"%08" PRIx32 "\",\"known_vector\":\"123456789\",\"known_vector_crc32\":\"%08" PRIx32 "\",\"non_aligned_hex\":\"00010203040506\",\"non_aligned_crc32\":\"%08" PRIx32 "\"}\n",
           hccl_crc32(NULL, 0), hccl_crc32(vector, 9), hccl_crc32(payload, sizeof(payload)));
    return 0;
}
