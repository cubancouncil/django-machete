from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner, reorder_suite
from django.utils.unittest import TestCase
from django.utils.unittest.loader import defaultTestLoader

class DiscoveryDjangoTestSuiteRunner(DjangoTestSuiteRunner):
    
    """
    Borrowed from github.com/carljm: https://gist.github.com/1450104
    
    A TEST_DISCOVERY_ROOT setting variable must be created as a path pointing to 
    the root of where you want the test runner to look for tests, likely your project root.
    
    You also need to modify the TEST_RUNNER setting with a 'dotted.path.to.DiscoveryDjangoTestSuiteRunner'.
    
    Adding these to your settings.py should suffice in most cases:
    
        TEST_RUNNER = 'apps.machete.test_runner.DiscoveryDjangoTestSuiteRunner'
        TEST_DISCOVERY_ROOT = os.path.dirname(__file__)
    
    Usage:
    
        Finds and runs all tests under TEST_DISCOVERY_ROOT:
        
            ./manage.py test
        
        Run a specific app's tests:
        
            ./manage.py test apps.some_app.tests
    
    """
    
    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        if test_labels:
            suite = defaultTestLoader.loadTestsFromNames(test_labels)
        else:
            suite = defaultTestLoader.discover(settings.TEST_DISCOVERY_ROOT)
        
        if extra_tests:
            for test in extra_tests:
                suite.addTest(test)

        return reorder_suite(suite, (TestCase,))