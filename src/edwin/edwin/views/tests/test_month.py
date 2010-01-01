from edwin.views.tests.twillbase import TwillTest

class TestMonth(TwillTest):
    def test_it(self):
        from twill import commands as b
        b.follow('October 1975')
        b.find('1975-10-19')
        b.notfind('1975-12-06')