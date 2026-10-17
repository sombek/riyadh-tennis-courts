import unittest
from monitor.browser import booking_window,parse_slots

class WindowTests(unittest.TestCase):
    def test_public_serialized_one_day_window(self):
        self.assertEqual(booking_window(r'{\"maxAdvanceBookingDays\":1}'),1)
        self.assertEqual(booking_window('{"maxAdvanceBookingDays":null}'),30)
    def test_missing_or_conflicting_window_fails_closed(self):
        for html in ['', '{"maxAdvanceBookingDays":1,"maxAdvanceBookingDays":2}']:
            with self.assertRaises(ValueError): booking_window(html)
    def test_unlabelled_empty_response_cannot_be_reused_for_other_dates(self):
        with self.assertRaises(ValueError):
            parse_slots('1:{"success":true,"results":[{"result":{"success":true,"data":[]}}]}','2026-10-18',55)

    def test_wrong_duration_or_date_cannot_be_used_from_browser_cache(self):
        body='1:{"success":true,"results":[{"result":{"success":true,"data":[{"booking_date":"2026-10-18","start_time":"23:00","end_time":"00:50","is_available":true}]}}]}'
        self.assertEqual(parse_slots(body,'2026-10-18',110),[dict(start='23:00',end='00:50',duration=110)])
        with self.assertRaises(ValueError): parse_slots(body,'2026-10-18',55)
        with self.assertRaises(ValueError): parse_slots(body,'2026-10-19',110)
