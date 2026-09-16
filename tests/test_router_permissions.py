import unittest

from llm_harness.permissions import assert_role_capability, role_has_capability
from llm_harness.router import CircuitBreakerOpenError, ModelRouter, ModelRouterConfig


class RouterAndPermissionsTests(unittest.TestCase):
    def test_router_loads_roles(self):
        config = ModelRouterConfig.from_dict(
            {
                "model_router": {
                    "roles": {
                        "strategist": {
                            "provider": "deepseek",
                            "model": "deepseek-v4.1-high",
                            "thinking_budget": "high",
                            "timeout_ms": 60000,
                            "max_retries": 1,
                            "fallback": ["heuristic_strategist"],
                        }
                    }
                }
            }
        )
        self.assertIn("STRATEGIST", config.roles)

    def test_circuit_breaker_uses_fallback_chain(self):
        config = ModelRouterConfig.from_dict(
            {
                "roles": {
                    "strategist": {
                        "provider": "deepseek",
                        "model": "deepseek-v4.1-high",
                        "thinking_budget": "high",
                        "timeout_ms": 60000,
                        "max_retries": 1,
                        "fallback": ["heuristic_strategist"],
                    },
                    "analyst": {
                        "provider": "bad",
                        "model": "x",
                        "thinking_budget": "low",
                        "timeout_ms": 1000,
                        "max_retries": 0,
                        "fallback": [],
                    },
                }
            }
        )
        router = ModelRouter(config)
        router.set_provider_health("deepseek", False)
        role = router.resolve_role("STRATEGIST")
        self.assertEqual(role.fallback, ["heuristic_strategist"])

        router.set_provider_health("bad", False)
        with self.assertRaises(CircuitBreakerOpenError):
            router.resolve_role("ANALYST")

    def test_permission_matrix_enforced(self):
        self.assertTrue(role_has_capability("STRATEGIST", "emit_strategic_directives"))
        with self.assertRaises(PermissionError):
            assert_role_capability("DELIBERATOR", "propose_patches")


if __name__ == "__main__":
    unittest.main()
