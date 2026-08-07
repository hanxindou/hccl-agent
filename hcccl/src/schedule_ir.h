#ifndef HCCL_INTERNAL_SCHEDULE_IR_H
#define HCCL_INTERNAL_SCHEDULE_IR_H

#include <stddef.h>
#include <stdint.h>

/* Internal-only API. The ELF version script keeps these symbols local. */
int hccl_schedule_ir_generate_json(
    const char* primitive,
    int32_t rank_size,
    uint64_t message_size_bytes,
    const char* dtype,
    const char* reduce_op,
    char** json_out
);

void hccl_schedule_ir_free_json(char* json_value);

#endif
