from edwin.views.tests.twillbase import TwillTest

class TestHomePage(TwillTest):
    def test_homepage(self):
        from twill import commands as b
        b.go('http://localhost:8080/')
        b.code(200)
