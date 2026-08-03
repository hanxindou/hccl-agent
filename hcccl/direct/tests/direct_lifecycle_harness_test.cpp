#include "hccl_direct_adapter.h"

#include <cassert>
#include <cstdint>
#include <thread>

namespace {

hccl_direct_session_config_t model_config() {
    return {HCCL_DIRECT_RANK_TABLE, 0, 2, 0, "rank_table.json", 0, 1};
}

hccl_direct_session_t *ready_session() {
    hccl_direct_session_t *session = nullptr;
    hccl_direct_error_t error{};
    assert(hccl_direct_session_create(&session, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    const auto config = model_config();
    assert(hccl_direct_session_configure(session, &config, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    assert(hccl_direct_session_preflight(session, 0, &error) == HCCL_DIRECT_STATUS_NO_DEVICE_EXPECTED);
    assert(hccl_direct_session_state(session) == HCCL_DIRECT_SESSION_NO_DEVICE_EXPECTED);
    return session;
}

void test_capacity() {
    hccl_direct_capacity_t capacity{};
    hccl_direct_error_t error{};
    assert(hccl_direct_calculate_capacity(HCCL_DIRECT_ALL_REDUCE, 8, 2, HCCL_DIRECT_DTYPE_FP32, HCCL_DIRECT_REDUCE_SUM, &capacity, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    assert(capacity.input_elements_per_rank == 8 && capacity.output_elements_per_rank == 8 && capacity.input_bytes_per_rank == 32 && capacity.output_bytes_per_rank == 32);
    assert(hccl_direct_calculate_capacity(HCCL_DIRECT_ALL_GATHER, 3, 4, HCCL_DIRECT_DTYPE_FP16, HCCL_DIRECT_REDUCE_NONE, &capacity, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    assert(capacity.input_elements_per_rank == 3 && capacity.output_elements_per_rank == 12 && capacity.input_bytes_per_rank == 6 && capacity.output_bytes_per_rank == 24);
    assert(hccl_direct_calculate_capacity(HCCL_DIRECT_REDUCE_SCATTER, 5, 3, HCCL_DIRECT_DTYPE_FP64, HCCL_DIRECT_REDUCE_SUM, &capacity, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    assert(capacity.input_elements_per_rank == 15 && capacity.output_elements_per_rank == 5 && capacity.input_bytes_per_rank == 120 && capacity.output_bytes_per_rank == 40);
    assert(hccl_direct_calculate_capacity(HCCL_DIRECT_ALL_GATHER, 1, 2, HCCL_DIRECT_DTYPE_FP32, HCCL_DIRECT_REDUCE_SUM, &capacity, &error) == HCCL_DIRECT_STATUS_INVALID_ARGUMENT);
    assert(hccl_direct_calculate_capacity(HCCL_DIRECT_ALL_REDUCE, UINT64_MAX, 2, HCCL_DIRECT_DTYPE_FP64, HCCL_DIRECT_REDUCE_SUM, &capacity, &error) == HCCL_DIRECT_STATUS_OVERFLOW);
}

void test_model_and_cleanup() {
    auto *session = ready_session(); hccl_direct_error_t error{};
    assert(hccl_direct_session_run_model(session, HCCL_DIRECT_FAILURE_NONE, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    assert(hccl_direct_session_state(session) == HCCL_DIRECT_SESSION_COMPLETED);
    assert(hccl_direct_session_cleanup_count(session) == 7);
    assert(hccl_direct_session_cleanup_action(session, 0) == HCCL_DIRECT_CLEANUP_RECV_BUFFER);
    assert(hccl_direct_session_cleanup_action(session, 6) == HCCL_DIRECT_CLEANUP_RUNTIME_LEASE);
    assert(hccl_direct_runtime_lease_count() == 0);
    assert(hccl_direct_session_destroy(session, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    assert(hccl_direct_session_destroy(session, &error) == HCCL_DIRECT_STATUS_INVALID_STATE);
    assert(hccl_direct_session_request_execution(session, 0, &error) == HCCL_DIRECT_STATUS_INVALID_STATE);
}

void test_process_scoped_runtime_lease() {
    auto *first = ready_session(); auto *second = ready_session(); hccl_direct_error_t error{};
    assert(hccl_direct_session_model_acquire_lease(first, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    assert(hccl_direct_session_model_acquire_lease(second, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    assert(hccl_direct_runtime_lease_count() == 2);
    assert(hccl_direct_session_model_cleanup(first, HCCL_DIRECT_FAILURE_NONE, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    assert(hccl_direct_runtime_lease_count() == 1);
    assert(hccl_direct_session_model_cleanup(second, HCCL_DIRECT_FAILURE_CLEANUP_RUNTIME_LEASE, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    assert(hccl_direct_session_cleanup_error_count(second) == 1);
    assert(hccl_direct_runtime_lease_count() == 0);
    assert(hccl_direct_session_destroy(first, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    assert(hccl_direct_session_destroy(second, &error) == HCCL_DIRECT_STATUS_SUCCESS);
}

void test_every_failure() {
    for (int point = HCCL_DIRECT_FAILURE_RUNTIME_LEASE; point <= HCCL_DIRECT_FAILURE_SYNCHRONIZE; ++point) {
        auto *session = ready_session(); hccl_direct_error_t error{};
        assert(hccl_direct_session_run_model(session, static_cast<hccl_direct_failure_point_t>(point), &error) == HCCL_DIRECT_STATUS_INJECTED_FAILURE);
        assert(hccl_direct_session_state(session) == HCCL_DIRECT_SESSION_FAILED);
        assert(hccl_direct_session_first_error(session, &error) == HCCL_DIRECT_STATUS_INJECTED_FAILURE);
        assert(hccl_direct_runtime_lease_count() == 0);
        assert(hccl_direct_session_destroy(session, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    }
    for (int point = HCCL_DIRECT_FAILURE_CLEANUP_RECV_BUFFER; point <= HCCL_DIRECT_FAILURE_CLEANUP_RUNTIME_LEASE; ++point) {
        auto *session = ready_session(); hccl_direct_error_t error{};
        assert(hccl_direct_session_run_model(session, static_cast<hccl_direct_failure_point_t>(point), &error) == HCCL_DIRECT_STATUS_SUCCESS);
        assert(hccl_direct_session_cleanup_error_count(session) == 1);
        assert(hccl_direct_session_first_error(session, &error) == HCCL_DIRECT_STATUS_SUCCESS);
        assert(hccl_direct_session_destroy(session, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    }
}

void test_config_guard_and_owner() {
    hccl_direct_session_t *session = nullptr; hccl_direct_error_t error{};
    assert(hccl_direct_session_create(&session, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    auto bad = model_config(); bad.rank_size = 1;
    assert(hccl_direct_session_configure(session, &bad, &error) == HCCL_DIRECT_STATUS_CONFIGURATION_ERROR);
    bad = model_config(); bad.root_rank = 1;
    assert(hccl_direct_session_configure(session, &bad, &error) == HCCL_DIRECT_STATUS_CONFIGURATION_ERROR);
    assert(hccl_direct_session_state(session) == HCCL_DIRECT_SESSION_CREATED);
    const auto config = model_config();
    assert(hccl_direct_session_configure(session, &config, &error) == HCCL_DIRECT_STATUS_SUCCESS);
    assert(hccl_direct_session_configure(session, &config, &error) == HCCL_DIRECT_STATUS_INVALID_STATE);
    assert(hccl_direct_session_run_model(session, HCCL_DIRECT_FAILURE_NONE, &error) == HCCL_DIRECT_STATUS_INVALID_STATE);
    assert(hccl_direct_session_request_execution(session, 0, &error) == HCCL_DIRECT_STATUS_NO_DEVICE_EXPECTED);
    assert(hccl_direct_session_request_execution(session, 1, &error) == HCCL_DIRECT_STATUS_HARDWARE_BLOCKED);
    assert(hccl_direct_session_verify_owner(session, 9, &error) == HCCL_DIRECT_STATUS_OWNERSHIP_VIOLATION);
    hccl_direct_status_t from_other_thread = HCCL_DIRECT_STATUS_SUCCESS;
    std::thread other([&] { hccl_direct_error_t local{}; from_other_thread = hccl_direct_session_verify_owner(session, 0, &local); });
    other.join();
    assert(from_other_thread == HCCL_DIRECT_STATUS_OWNERSHIP_VIOLATION);
    assert(hccl_direct_session_destroy(session, &error) == HCCL_DIRECT_STATUS_SUCCESS);
}

}  // namespace

int main() { test_capacity(); test_model_and_cleanup(); test_process_scoped_runtime_lease(); test_every_failure(); test_config_guard_and_owner(); }
