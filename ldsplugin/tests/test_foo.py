import unittest

class TestFoo(unittest.TestCase):
    
    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')
        

def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(TestFoo, 'test'))
    return suite

def run_tests():
    unittest.TextTestRunner(verbosity=3).run(suite())


