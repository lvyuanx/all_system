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
        """
        生成数据库唯一流水号
        - 字母部分随机位置
        - 总长度固定
        """
        if length <= 0:
            raise ValueError("length 必须为正整数")
        if letter_length < 0 or letter_length > length:
            raise ValueError("letter_length 必须在 0 ~ length 之间")

        digit_length = length - letter_length

        for _ in range(100):
            with self._lock:
                ts_ms = int(time.time() * 1000) & ((1 << 48) - 1)
                self._counter = (self._counter + 1) & 0xFFFF
                ctr = self._counter

            # 生成随机数字部分
            rnd_digits = random.getrandbits(digit_length * 4)
            digit_str = self._encode(rnd_digits, self.DIGITS)
            if len(digit_str) < digit_length:
                digit_str = self.DIGITS[0] * (digit_length - len(digit_str)) + digit_str
            else:
                digit_str = digit_str[-digit_length:]

            # 生成字母部分
            letter_str = "".join(random.choice(self.LETTERS) for _ in range(letter_length))

            # 将字母随机插入数字序列
            all_chars = list(digit_str + letter_str)
            random.shuffle(all_chars)
            sn_body = "".join(all_chars)

            sn = f"{prefix}{sn_body}"

            try:
                with transaction.atomic():
                    SerialNumber.objects.create(sn=sn, used_for=used_for)
                return sn
            except IntegrityError:
                continue

        raise RuntimeError("生成唯一流水号失败：超过最大重试次数")

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
