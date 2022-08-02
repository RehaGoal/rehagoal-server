from django.test import TestCase
from ..urls import urlpatterns

class URLsTestCase(TestCase):
    """
    Tests registered URL patterns
    """

    def test_files_url(self):
        """
        files/ path should only allow alphanumeric IDs of length 12.
        """
        matching_patterns = list(filter(lambda pattern: str(pattern.pattern).startswith('^files/'), urlpatterns))
        self.assertEqual(len(matching_patterns), 1)
        files_urlpattern = matching_patterns[0]
        self.assertEquals(str(files_urlpattern.pattern), r'^files/(?P<path>[A-Za-z0-9]{12}|)$')
