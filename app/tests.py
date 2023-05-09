from django.test import SimpleTestCase
from app import calc


class CalcTest(SimpleTestCase):
    def test_add_should_return_correct_result(self):
        res = calc.add(5, 6)
        self.assertEqual(res, 11)

    def test_sub_should_return_correct_result(self):
        res = calc.sub(8, 6)
        self.assertEqual(res, 2)
