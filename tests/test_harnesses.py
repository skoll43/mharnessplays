import unittest

from llm_harness.harnesses import (
    AnalystHarness,
    BroadcasterHarness,
    DeliberatorHarness,
    MetaCoderHarness,
    StrategistHarness,
)


class StrategistHarnessTests(unittest.TestCase):
    def test_emits_valid_directive_schema(self):
        harness = StrategistHarness()
        result = harness.invoke(
            {
                "objective_registry": ["HEAL_AND_HOLD"],
                "cartographer_nodes": ["town"],
                "raw_output": '{"directive_id":"d1","goal":"HEAL_AND_HOLD","priority":1,"target_node":"town","reasoning_summary":"safe","constraints":{"avoid_high_grass":true,"heal_before_departure":true,"require_item":[]},"expires_after_minutes":5}',
            }
        )
        self.assertFalse(result.fallback_used)
        self.assertTrue(result.report.output_valid)

    def test_rejects_unknown_goal_names(self):
        harness = StrategistHarness()
        result = harness.invoke(
            {
                "objective_registry": ["HEAL_AND_HOLD"],
                "cartographer_nodes": ["town"],
                "raw_outputs": ['{"directive_id":"d1","goal":"UNKNOWN","priority":1,"target_node":"town","reasoning_summary":"safe","constraints":{"avoid_high_grass":true,"heal_before_departure":true,"require_item":[]},"expires_after_minutes":5}'],
            }
        )
        self.assertTrue(result.fallback_used)

    def test_rejects_invalid_target_nodes(self):
        harness = StrategistHarness()
        result = harness.invoke(
            {
                "objective_registry": ["HEAL_AND_HOLD"],
                "cartographer_nodes": ["town"],
                "raw_outputs": ['{"directive_id":"d1","goal":"HEAL_AND_HOLD","priority":1,"target_node":"forest","reasoning_summary":"safe","constraints":{"avoid_high_grass":true,"heal_before_departure":true,"require_item":[]},"expires_after_minutes":5}'],
            }
        )
        self.assertTrue(result.fallback_used)

    def test_falls_back_on_timeout(self):
        harness = StrategistHarness()
        result = harness.invoke({"force_timeout": True})
        self.assertTrue(result.fallback_used)


class DeliberatorHarnessTests(unittest.TestCase):
    def test_emits_valid_primitive_schema(self):
        harness = DeliberatorHarness()
        result = harness.invoke(
            {
                "legal_actions": ["WAIT", "SAFE_PAUSE"],
                "raw_output": '{"action_id":"a1","primitive":"WAIT","params":{},"confidence_note":null}',
            }
        )
        self.assertFalse(result.fallback_used)

    def test_rejects_raw_controller_bitmasks(self):
        harness = DeliberatorHarness()
        result = harness.invoke(
            {
                "legal_actions": ["WAIT", "SAFE_PAUSE"],
                "raw_outputs": [
                    '{"action_id":"a1","primitive":"WAIT","params":{"input":"A|B"},"confidence_note":null}'
                ],
            }
        )
        self.assertTrue(result.fallback_used)

    def test_rejects_navigate_during_battle_if_illegal(self):
        harness = DeliberatorHarness()
        result = harness.invoke(
            {
                "game_mode": "BATTLE",
                "legal_actions": ["WAIT", "RUN_AWAY"],
                "raw_outputs": ['{"action_id":"a1","primitive":"NAVIGATE","params":{},"confidence_note":null}'],
            }
        )
        self.assertTrue(result.fallback_used)

    def test_falls_back_safe_pause_on_repeated_invalid_output(self):
        harness = DeliberatorHarness()
        result = harness.invoke(
            {
                "belief_confidence_low": True,
                "legal_actions": ["WAIT", "SAFE_PAUSE"],
                "raw_outputs": [
                    '{"action_id":"a1","primitive":"INVALID","params":{},"confidence_note":null}',
                    '{"action_id":"a1","primitive":"INVALID","params":{},"confidence_note":null}',
                    '{"action_id":"a1","primitive":"INVALID","params":{},"confidence_note":null}',
                ],
            }
        )
        self.assertTrue(result.fallback_used)
        self.assertEqual(result.output["primitive"], "SAFE_PAUSE")


class MetaCoderHarnessTests(unittest.TestCase):
    def test_produces_proposal_only_not_live_patch(self):
        harness = MetaCoderHarness()
        result = harness.invoke(
            {
                "raw_output": '{"proposal_id":"p1","incident_id":"i1","risk_level":"low","target":"planner","proposal_type":"code","summary":"Adjust parser","diff_ref":"d1","tests_required":["unit","replay"],"rollback_plan":"revert commit"}'
            }
        )
        self.assertFalse(result.fallback_used)

    def test_rejects_access_to_secrets(self):
        harness = MetaCoderHarness()
        result = harness.invoke(
            {
                "raw_outputs": ['{"proposal_id":"p1","incident_id":"i1","risk_level":"low","target":"planner","proposal_type":"code","summary":"Deploy now with secret token","diff_ref":"d1","tests_required":["unit"],"rollback_plan":"revert commit"}'],
                "incident_id": "i1",
            }
        )
        self.assertTrue(result.fallback_used)

    def test_requires_replay_validation_flag(self):
        harness = MetaCoderHarness()
        result = harness.invoke(
            {
                "raw_outputs": ['{"proposal_id":"p1","incident_id":"i1","risk_level":"low","target":"planner","proposal_type":"code","summary":"Adjust parser","diff_ref":"d1","tests_required":["unit"],"rollback_plan":"revert commit"}'],
                "incident_id": "i1",
            }
        )
        self.assertTrue(result.fallback_used)

    def test_falls_back_to_human_review_on_failure(self):
        harness = MetaCoderHarness()
        result = harness.invoke({"force_timeout": True, "incident_id": "i1"})
        self.assertTrue(result.fallback_used)
        self.assertTrue(result.output.get("requires_human_review"))


class BroadcasterHarnessTests(unittest.TestCase):
    def test_redacts_secrets_and_invalidates_output(self):
        harness = BroadcasterHarness()
        result = harness.invoke(
            {
                "raw_outputs": [
                    '{"message":"my password is hunter2","tone":"neutral","tts_enabled":false,"spoiler_safe":true}'
                ]
            }
        )
        self.assertTrue(result.fallback_used)

    def test_avoids_control_instructions(self):
        harness = BroadcasterHarness()
        result = harness.invoke(
            {
                "raw_outputs": [
                    '{"message":"press A now","tone":"neutral","tts_enabled":false,"spoiler_safe":true}'
                ]
            }
        )
        self.assertTrue(result.fallback_used)

    def test_produces_stream_safe_output(self):
        harness = BroadcasterHarness()
        result = harness.invoke(
            {
                "raw_output": '{"message":"That was a clutch escape!","tone":"excited","tts_enabled":true,"spoiler_safe":true}',
                "spoiler_safe_mode": True,
            }
        )
        self.assertFalse(result.fallback_used)

    def test_falls_back_to_templates_on_timeout(self):
        harness = BroadcasterHarness()
        result = harness.invoke({"force_timeout": True, "template_commentary": "Template line"})
        self.assertTrue(result.fallback_used)
        self.assertEqual(result.output["message"], "Template line")


class AnalystHarnessTests(unittest.TestCase):
    def test_produces_fault_domain_label(self):
        harness = AnalystHarness()
        result = harness.invoke(
            {
                "raw_output": '{"incident_id":"i1","fault_domain":"control","severity":"medium","summary":"loop stuck","recommended_next_step":"inspect controller"}'
            }
        )
        self.assertFalse(result.fallback_used)

    def test_does_not_mutate_incident_data(self):
        harness = AnalystHarness()
        incident = {"id": "i1", "msg": "abc"}
        _ = harness.invoke(
            {
                "incident_packets": [incident],
                "raw_output": '{"incident_id":"i1","fault_domain":"unknown","severity":"low","summary":"queued","recommended_next_step":"queue"}',
            }
        )
        self.assertEqual(incident, {"id": "i1", "msg": "abc"})

    def test_handles_malformed_incident_gracefully(self):
        harness = AnalystHarness()
        result = harness.invoke({"raw_outputs": ["not-json"], "incident_id": "i1"})
        self.assertTrue(result.fallback_used)


if __name__ == "__main__":
    unittest.main()
