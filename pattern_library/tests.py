from datetime import date
from unittest.mock import patch

from django.test import TestCase

from pattern_library.models import Pattern, PatternCategory
from pattern_library.services import build_pattern_code_preview, consume_next_pattern_code


class PatternCodeServiceTests(TestCase):
    def test_day_mode_increments_and_resets_by_day(self):
        category = PatternCategory.objects.create(
            name="订单类",
            code_prefix="ODR",
            date_mode=PatternCategory.DateMode.DAY,
            serial_digits=2,
        )
        with patch("pattern_library.services.pattern_code_service.timezone.localdate", return_value=date(2026, 5, 8)):
            self.assertEqual(consume_next_pattern_code(category), "ODR2026050801")
            self.assertEqual(consume_next_pattern_code(category), "ODR2026050802")
        with patch("pattern_library.services.pattern_code_service.timezone.localdate", return_value=date(2026, 5, 9)):
            self.assertEqual(consume_next_pattern_code(category), "ODR2026050901")

    def test_year_mode_four_digits(self):
        category = PatternCategory.objects.create(
            name="年规则",
            code_prefix="ODR",
            date_mode=PatternCategory.DateMode.YEAR,
            serial_digits=4,
        )
        with patch("pattern_library.services.pattern_code_service.timezone.localdate", return_value=date(2026, 1, 2)):
            self.assertEqual(consume_next_pattern_code(category), "ODR20260001")
            self.assertEqual(consume_next_pattern_code(category), "ODR20260002")

    def test_preview_does_not_consume_serial(self):
        category = PatternCategory.objects.create(
            name="预览",
            code_prefix="ODR",
            date_mode=PatternCategory.DateMode.MONTH,
            serial_digits=3,
        )
        with patch("pattern_library.services.pattern_code_service.timezone.localdate", return_value=date(2026, 5, 8)):
            self.assertEqual(build_pattern_code_preview(category), "ODR202605001")
            self.assertEqual(consume_next_pattern_code(category), "ODR202605001")
            self.assertEqual(build_pattern_code_preview(category), "ODR202605002")

    def test_skip_existing_manual_code(self):
        category = PatternCategory.objects.create(
            name="冲突跳过",
            code_prefix="ODR",
            date_mode=PatternCategory.DateMode.DAY,
            serial_digits=2,
        )
        Pattern.objects.create(code="ODR2026050801")
        with patch("pattern_library.services.pattern_code_service.timezone.localdate", return_value=date(2026, 5, 8)):
            self.assertEqual(consume_next_pattern_code(category), "ODR2026050802")
