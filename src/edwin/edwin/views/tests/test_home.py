from edwin.views.tests.twillbase import TwillTest

class TestHomePage(TwillTest):
    def test_homepage(self):
        from twill import commands as b
        b.find('July 1975')
        b.find('1975-12-06')
