import unittest
from src.audit.logger import AuditLogger

class TestAuditLogger(unittest.TestCase):

    def setUp(self):
        self.logger = AuditLogger()

    def test_log_action(self):
        action = "Test action"
        result = self.logger.log_action(action)
        self.assertTrue(result)
        # Here you would typically check if the action was logged correctly

    def test_get_logs(self):
        self.logger.log_action("Test action 1")
        self.logger.log_action("Test action 2")
        logs = self.logger.get_logs()
        self.assertEqual(len(logs), 2)
        self.assertIn("Test action 1", logs)
        self.assertIn("Test action 2", logs)

    def test_clear_logs(self):
        self.logger.log_action("Test action")
        self.logger.clear_logs()
        logs = self.logger.get_logs()
        self.assertEqual(len(logs), 0)

if __name__ == '__main__':
    unittest.main()