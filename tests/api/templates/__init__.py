"""Configuration templates for test environment setup.

This package contains JSON template files for creating test configurations.
Templates support variable substitution using {{var}} syntax.

Available templates:
- minimal_robot.json: Minimal ROBOT configuration (DOC_STORE, LLM, CHAIN, BRAIN, DRIVE, ROBOT)
- robot_with_memory.json: ROBOT with MEMORY support (includes CONVERSATION_MANAGER)
- action_test_set.json: PROMPT_TEMPLATE + DOC_STORE for action testing
- batch_ref_chain.json: Complete ROBOT with DCChain (complex interdependent configuration)

Usage:
    from tests.api.base_test import BaseRobotTest

    class MyTest(BaseRobotTest):
        def test_example(self):
            # Load template with variable substitution
            template = self.load_template("action_test_set", setting_name="my_test")
            draft_ids = self.batch_create_drafts(template["drafts"])
            # ... test code ...
"""
