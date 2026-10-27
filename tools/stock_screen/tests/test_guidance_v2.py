"""Guard the first-target midpoint and short-record conventions."""
import unittest
from tools.stock_screen.build_v2 import guidance_score


def pair(year,actual):
    return {'fiscal_year':year,'target_low':6,'target_high':10,'actual':actual,
            'first_target_source':{'published_on':f'{year}-02-01'},
            'actual_source':{'published_on':f'{year+1}-02-01'}}


class GuidanceTests(unittest.TestCase):
    def test_lower_bound_hit_is_not_a_midpoint_hit(self):
        result=guidance_score([pair(2023,7),pair(2024,8),pair(2025,9)])
        self.assertEqual(result['hits'],2)
        self.assertEqual(result['score'],4)

    def test_short_record_is_capped_without_inventing_missing_years(self):
        self.assertEqual(guidance_score([pair(2025,10)])['score'],3)
        self.assertEqual(guidance_score([pair(y,10)for y in range(2021,2025)])['score'],4)
        self.assertEqual(guidance_score([pair(y,10)for y in range(2021,2026)])['score'],5)

    def test_actual_must_follow_first_publication(self):
        p=pair(2025,8);p['first_target_source']['published_on']='2026-03-01'
        with self.assertRaises(ValueError):guidance_score([p])


if __name__=='__main__':unittest.main()
