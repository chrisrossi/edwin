from edwin.views.tests.twillbase import TwillTest

class AlbumViewTest(TwillTest):
    def test_it(self):
        from twill import commands as b
        b.follow('1975-11-04')
        b.find('1975-11-04')