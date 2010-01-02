from edwin.views.tests.twillbase import TwillTest

class TestPhotoView(TwillTest):
    def test_it(self):
        from twill import commands as b
        b.follow('1975-11-04')
        b.find('1975-11-04')
        b.follow('photo_02.jpg')
        b.find('Test 2')
        b.find('November 04, 1975')
        b.follow('download')
        b.code(200)
