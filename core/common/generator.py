import time
import random
import threading
from django.db import IntegrityError, transaction
from .models import SerialNumber

class SerialNumberGenerator:
    DIGITS = "0123456789"
    LETTERS = "ABCDEFGHJKLMNOPQRSTUVWXYZ"

    def __init__(self):
        self._lock = threading.Lock()
        self._counter = random.randint(0, 0xFFFF)

    def next_id(
        self,
        prefix: str = "SN",
        used_for: str = None,
        length: int = 16,
        letter_length: int = 4
    ) -> str:
        """生成单个唯一流水号"""
        return self.next_ids(1, prefix, used_for, length, letter_length)[0]

    def next_ids(
        self,
        count: int,
        prefix: str = "SN",
        used_for: str = None,
        length: int = 16,
        letter_length: int = 4
    ) -> list[str]:
        """生成多个唯一流水号"""
        if count <= 0:
            raise ValueError("count 必须大于 0")
        if length <= 0:
            raise ValueError("length 必须为正整数")
        if letter_length < 0 or letter_length > length:
            raise ValueError("letter_length 必须在 0 ~ length 之间")

        digit_length = length - letter_length
        result = []
        max_attempts = 1000  # 总尝试次数，防止死循环

        attempts = 0
        while len(result) < count and attempts < max_attempts:
            attempts += 1
            batch_sn = []

            # 先生成候选流水号
            for _ in range(count - len(result)):
                with self._lock:
                    ts_ms = int(time.time() * 1000) & ((1 << 48) - 1)
                    self._counter = (self._counter + 1) & 0xFFFF
                    ctr = self._counter

                # 数字部分
                rnd_digits = random.getrandbits(digit_length * 4)
                digit_str = self._encode(rnd_digits, self.DIGITS)
                if len(digit_str) < digit_length:
                    digit_str = self.DIGITS[0] * (digit_length - len(digit_str)) + digit_str
                else:
                    digit_str = digit_str[-digit_length:]

                # 字母部分
                letter_str = "".join(random.choice(self.LETTERS) for _ in range(letter_length))

                # 混合字母数字
                all_chars = list(digit_str + letter_str)
                random.shuffle(all_chars)
                sn_body = "".join(all_chars)
                sn = f"{prefix}{sn_body}"
                batch_sn.append(sn)

            # 批量写入数据库
            try:
                with transaction.atomic():
                    for sn in batch_sn:
                        SerialNumber.objects.create(sn=sn, used_for=used_for)
                    result.extend(batch_sn)
            except IntegrityError:
                # 部分冲突，重新生成冲突的数量
                continue

        if len(result) < count:
            raise RuntimeError(f"生成唯一流水号失败：期望 {count} 个，实际生成 {len(result)} 个")

        return result

    @staticmethod
    def _encode(value: int, alphabet: str) -> str:
        if value == 0:
            return alphabet[0]
        base = len(alphabet)
        buf = []
        while value > 0:
            value, r = divmod(value, base)
            buf.append(alphabet[r])
        return "".join(reversed(buf))


# ----------------- 单例 -----------------
_sn_generator_instance = None
_sn_generator_lock = threading.Lock()

def get_sn_generator() -> SerialNumberGenerator:
    global _sn_generator_instance
    if _sn_generator_instance is None:
        with _sn_generator_lock:
            if _sn_generator_instance is None:
                _sn_generator_instance = SerialNumberGenerator()
    return _sn_generator_instance

sn_generator = get_sn_generator()
