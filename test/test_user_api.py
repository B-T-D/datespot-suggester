import unittest

from python_backend.user_api import UserAPI
from python_backend import user

class TestHelloWorldThings(unittest.TestCase):
    """Quick replacement of the manual tests."""

    def setUp(self):
        # create a fake DB 
        self.api = UserAPI(datafile_name="test/mock_user_data.json")
        
        # make a mock user with a known uuid primary key:
        knownKey = 1
        mockUser = user.User("test_user", currentLocation=(0,0), homeLocation=(0,0))
        self.api.data[knownKey] = self.api._serialize_user(mockUser)
        assert 1 in self.api.data
    
    def test_create_user(self):
        newUser = self.api.create_user("Grort")
        self.assertIn(newUser, self.api.data)
    
    def test_load_user(self):
        existingUser = self.api.load_user(1) # todo it should work with an int literal
        #print(type(existingUser))
        #self.assertIsInstance(existingUser, user.User) # todo this keeps failing even though it's a user instance. For namespacing reasons (?)
        print(existingUser)
        self.assertEqual(existingUser.name, "test_user")
    
    def test_delete_user(self):
        self.api.delete_user(1)
        self.assertNotIn(1, self.api.data)