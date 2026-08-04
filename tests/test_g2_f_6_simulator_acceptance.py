"""G2-F-6 simulator topology/performance/reliability contracts."""

import unittest

from simulator.g2_f_6_acceptance import (
    ExperimentSpec, MESSAGE_SIZES, REQUIRED_EVIDENCE_FILES, SCALE_RANKS,
    SimulatorAcceptance, validate_evidence_contract,
)


class TestG2F6SimulatorAcceptance(unittest.TestCase):
    def setUp(self):
        self.acceptance = SimulatorAcceptance()

    def test_topology_inventory_has_directed_hccs_roce_pcie_profiles(self):
        inventory = self.acceptance.topology_inventory()
        self.assertEqual({item["topology"] for item in inventory}, {"FULL_MESH", "RING", "FAT_TREE", "HETEROGENEOUS"})
        links = [link for item in inventory for link in item["links"]]
        self.assertEqual({"HCCS", "RoCE", "PCIe"}, {link["link_type"] for link in links})
        self.assertTrue(all(link["source"] != link["destination"] and link["effective_bandwidth_gbps"] > 0 for link in links))
        hetero = next(item for item in inventory if item["topology"] == "HETEROGENEOUS")
        self.assertGreater(hetero["oversubscription"], 1.0)
        required_link_fields = {"source", "destination", "link_type", "nominal_bandwidth_gbps", "effective_bandwidth_gbps", "one_way_latency_ms", "full_duplex", "oversubscription_ratio", "current_utilization_percent", "queue_depth", "fault_probability", "numa_domain", "enabled"}
        self.assertTrue(all(required_link_fields <= set(link) for link in links))

    def test_all_primitives_have_non_negative_unit_bearing_events(self):
        for primitive, op in (("AllReduce", "SUM"), ("AllGather", None), ("ReduceScatter", "SUM")):
            item = self.acceptance.simulate_iteration(ExperimentSpec(f"unit-{primitive}", primitive, "Fat-Tree", "FAT_TREE", 8, "1KB", 1024, reduce_op=op), 0)
            self.assertTrue(item["correctness_gate"]["correctness_gate_passed"])
            self.assertGreater(item["simulated_collective_time_us"], 0)
            self.assertGreater(item["effective_payload_bandwidth_gb_s"], 0)
            self.assertTrue(all(value >= 0 for value in item["cost_components_us"].values()))

    def test_message_and_scale_matrix_meets_required_bounds(self):
        matrix = self.acceptance.experiment_matrix()
        self.assertEqual({size for _, size in MESSAGE_SIZES}, {item.logical_message_bytes for item in matrix if item.identifier.startswith("message-")})
        self.assertEqual(set(SCALE_RANKS), {item.ranks for item in matrix if item.identifier.startswith("scale-")})

    def test_deterministic_and_bandwidth_monotonic(self):
        spec = ExperimentSpec("deterministic", "AllReduce", "Fat-Tree", "FAT_TREE", 64, "128MB", 128 * 1024 * 1024)
        self.assertEqual(self.acceptance.simulate_iteration(spec, 3), self.acceptance.simulate_iteration(spec, 3))
        low = self.acceptance.simulate_iteration(spec, 0, bandwidth_scale=.9)
        high = self.acceptance.simulate_iteration(spec, 0, bandwidth_scale=1.1)
        self.assertGreater(low["simulated_collective_time_us"], high["simulated_collective_time_us"])
        self.assertLess(low["effective_payload_bandwidth_gb_s"], high["effective_payload_bandwidth_gb_s"])
        full_mesh = self.acceptance.simulate_iteration(ExperimentSpec("full-mesh", "AllReduce", "Ring AllReduce", "FULL_MESH", 8, "1MB", 1024 * 1024), 0)
        hetero = self.acceptance.simulate_iteration(ExperimentSpec("hetero", "AllReduce", "Ring AllReduce", "HETEROGENEOUS", 8, "1MB", 1024 * 1024), 0)
        self.assertGreater(hetero["simulated_collective_time_us"], full_mesh["simulated_collective_time_us"])

    def test_large_rank_correctness_gate_is_bounded(self):
        spec = ExperimentSpec("large-rank", "AllReduce", "Fat-Tree", "FAT_TREE", 1024, "logical_1GB", 1024 * 1024 * 1024)
        item = self.acceptance.simulate_iteration(spec, 0)
        self.assertTrue(item["correctness_gate"]["correctness_gate_passed"])
        self.assertEqual(item["materialized_message_bytes"], 4 * 1024 * 1024)
        self.assertEqual(item["chunk_count"], 256)

    def test_sensitivity_is_explicit(self):
        results = self.acceptance.sensitivity_analysis()
        self.assertGreaterEqual(len(results), 10)
        self.assertTrue(any(item["parameter_change"] == "bandwidth_minus_10_percent" for item in results))
        self.assertTrue(all("latency_change_percent" in item for item in results))
        self.assertTrue(all(len(item["variant_algorithm_ranking"]) == 5 for item in results))

    def test_statistics_and_evidence_contract_are_traceable(self):
        summary, raw = self.acceptance.run_experiment(ExperimentSpec("statistics", "AllReduce", "Fat-Tree", "FAT_TREE", 64, "1MB", 1024 * 1024))
        self.assertEqual(len(raw), 30)
        self.assertLessEqual(summary["latency_statistics_us"]["p50"], summary["latency_statistics_us"]["p95"])
        result = {"checkpoint": "G2-F-6", "validation_track": "SIMULATOR_ACCEPTANCE", "checkpoint_status": "COMPLETED", "simulator_topology_status": "SIMULATOR_TOPOLOGY_PASS", "simulator_performance_status": "SIMULATOR_PERFORMANCE_PASS", "simulator_scale_status": "SIMULATOR_SCALE_PASS", "simulator_reliability_status": "SIMULATOR_RELIABILITY_PASS", "real_device_acceptance": "HARDWARE_BLOCKED", "performance_claim_type": "SIMULATED_ONLY", "measured_on_real_npu": False, "profiling_source": "SIMULATOR_TRACE", "msprof_executed": False, "direct_hccl_api_call": False, "real_ascend_npu_validated": False, "runtime_api_calls": []}
        validate_evidence_contract(REQUIRED_EVIDENCE_FILES, result)

    def test_fault_recovery_and_explicit_no_path_failure(self):
        records = self.acceptance.reliability_scenarios()
        self.assertEqual(len(records), 12)
        self.assertEqual({"transient_link_failure", "permanent_link_failure", "bandwidth_degradation", "latency_spike", "corruption", "node_exit", "congestion_queue", "timeout", "retry", "alternate_route", "dynamic_node_removal", "dynamic_node_recovery"}, {item["fault_type"] for item in records})
        recovered = [item for item in records if item["collective_completion_status"] == "RECOVERED"]
        self.assertTrue(all(item["correctness_recheck"]["correctness_gate_passed"] for item in recovered))
        self.assertEqual(sum(item["collective_completion_status"] == "EXPECTED_NO_PATH_FAILURE" for item in records), 1)

    def test_logical_72h_workload_and_profiler_are_simulator_only(self):
        summary = self.acceptance.logical_72h()
        self.assertTrue(summary["logical_72h_simulation"])
        self.assertFalse(summary["real_72h_hardware_stress"])
        workloads = self.acceptance.workload_trace()
        self.assertEqual({"BERT_LIKE", "LLAMA_LIKE"}, {item["workload_name"] for item in workloads})
        record = self.acceptance.simulate_iteration(ExperimentSpec("profile", "AllReduce", "Ring AllReduce", "RING", 8, "1KB", 1024), 0)
        trace = self.acceptance.profiling_trace(record)
        self.assertTrue(trace and all(item["duration_us"] >= 0 for item in trace))


if __name__ == "__main__":
    unittest.main()
