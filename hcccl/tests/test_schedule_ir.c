#include "schedule_ir.h"

#include <stdio.h>
#include <string.h>

static int check(const char* primitive, int ranks, unsigned long long bytes)
{
    char* json_value = NULL;
    if (hccl_schedule_ir_generate_json(primitive, ranks, bytes, "FP32", "SUM", &json_value) != 0) return 1;
    if (strstr(json_value, "\"schema_version\":\"g3-b2-schedule-ir-v1\"") == NULL ||
        strstr(json_value, "\"schedule_hash\":") == NULL ||
        strstr(json_value, "\"fallback_policy\":\"NONE\"") == NULL) {
        hccl_schedule_ir_free_json(json_value);
        return 2;
    }
    hccl_schedule_ir_free_json(json_value);
    return 0;
}

int main(void)
{
    const char* primitives[] = {"AllReduce", "AllGather", "ReduceScatter"};
    const int ranks[] = {2, 4, 8, 16, 64};
    size_t p, r;
    for (p = 0; p < sizeof(primitives) / sizeof(primitives[0]); ++p) {
        for (r = 0; r < sizeof(ranks) / sizeof(ranks[0]); ++r) {
            if (check(primitives[p], ranks[r], (unsigned long long)ranks[r] * 4ULL + 3ULL) != 0) return 1;
        }
    }
    puts("schedule_ir: PASS");
    return 0;
}
