from slowapi import Limiter
from slowapi.util import get_remote_address

lim = Limiter(key_func=get_remote_address)
