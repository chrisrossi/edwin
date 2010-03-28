import unittest

class TestFormatDateRange(unittest.TestCase):
    def test_it(self):
        from edwin.views.util import format_date_range
        from datetime import date
        self.assertEqual(
            format_date_range((date(2007, 9, 9), date(2007, 9, 9))),
            'September 9, 2007'
        )
        self.assertEqual(
            format_date_range((date(2007, 9, 9), date(2007, 9, 11))),
            'September 9-11, 2007'
        )
        self.assertEqual(
            format_date_range((date(2007, 9, 9), date(2007, 10, 9))),
            'September 9 - October 9, 2007'
        )
        self.assertEqual(
            format_date_range((date(2007, 9, 9), date(2008, 9, 9))),
            'September 9, 2007 - September 9, 2008'
        )
