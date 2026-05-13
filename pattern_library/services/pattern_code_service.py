from django.db import IntegrityError, transaction
from django.utils import timezone

from pattern_library.models import Pattern, PatternCategory, PatternCategorySerial


def _build_date_key(category: PatternCategory) -> str:
    today = timezone.localdate()
    mode = category.date_mode
    if mode == PatternCategory.DateMode.YEAR:
        return today.strftime("%Y")
    if mode == PatternCategory.DateMode.MONTH:
        return today.strftime("%Y%m")
    if mode == PatternCategory.DateMode.DAY:
        return today.strftime("%Y%m%d")
    return ""


def _build_pattern_code(category: PatternCategory, date_key: str, serial: int) -> str:
    prefix = str(category.code_prefix or "").strip()
    serial_str = str(serial).zfill(int(category.serial_digits))
    return f"{prefix}{date_key}{serial_str}"


def _is_code_available(code: str) -> bool:
    return not Pattern.objects.filter(code=code).exists()


def _find_next_available_serial(
    category: PatternCategory, date_key: str, start_serial: int
) -> tuple[int, str]:
    serial = max(1, int(start_serial))
    for _ in range(1000):
        code = _build_pattern_code(category, date_key, serial)
        if _is_code_available(code):
            return serial, code
        serial += 1
    raise RuntimeError("无法生成可用版号")


def build_pattern_code_preview(category: PatternCategory) -> str:
    date_key = _build_date_key(category)
    current_serial = (
        PatternCategorySerial.objects.filter(category=category, date_key=date_key)
        .values_list("current_serial", flat=True)
        .first()
        or 0
    )
    _, code = _find_next_available_serial(category, date_key, current_serial + 1)
    return code


@transaction.atomic
def consume_next_pattern_code(category: PatternCategory) -> str:
    date_key = _build_date_key(category)
    serial_obj = (
        PatternCategorySerial.objects.select_for_update()
        .filter(category=category, date_key=date_key)
        .first()
    )
    if serial_obj is None:
        try:
            serial_obj = PatternCategorySerial.objects.create(
                category=category,
                date_key=date_key,
                current_serial=0,
            )
        except IntegrityError:
            serial_obj = (
                PatternCategorySerial.objects.select_for_update()
                .get(category=category, date_key=date_key)
            )
        else:
            serial_obj = (
                PatternCategorySerial.objects.select_for_update().get(pk=serial_obj.pk)
            )
    serial_obj.current_serial += 1
    serial_obj.save(update_fields=["current_serial", "update_time"])
    serial, code = _find_next_available_serial(category, date_key, serial_obj.current_serial)
    if serial != serial_obj.current_serial:
        serial_obj.current_serial = serial
        serial_obj.save(update_fields=["current_serial", "update_time"])
    return code
