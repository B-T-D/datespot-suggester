import unittest

try:
    from python_backend.user_api import UserAPI

except:
    from user_api import UserAPI

class TestHelloWorld(unittest.TestCase):

    def test_tests_setup(self):
        self.assertEqual(1, 1)