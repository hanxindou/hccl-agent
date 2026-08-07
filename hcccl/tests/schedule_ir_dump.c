#include "schedule_ir.h"

#include <stdio.h>
#include <stdlib.h>

int main(int argc, char** argv)
{
    char* json_value = NULL;
    const char* reduce_op;
    if (argc != 6) {
        fprintf(stderr, "usage: schedule_ir_dump PRIMITIVE RANKS BYTES DTYPE REDUCE_OP\n");
        return 2;
    }
    reduce_op = argv[5];
    if (hccl_schedule_ir_generate_json(argv[1], (int32_t)strtol(argv[2], NULL, 10), (uint64_t)strtoull(argv[3], NULL, 10), argv[4], reduce_op, &json_value) != 0) {
        return 3;
    }
    puts(json_value);
    hccl_schedule_ir_free_json(json_value);
    return 0;
}
