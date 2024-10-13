# utils.py
import random
import string


def code_generator(length=3):
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )
