from edwin.views.tests.twillbase import TwillTest

class TestHomePage(TwillTest):
    def test_homepage(self):
        from twill import commands as b
        b.go('http://localhost:8080/')
        b.code(200)

        b.find('July 1975')
        b.find('1975-12-06')
