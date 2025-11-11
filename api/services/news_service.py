import json, requests
from functools import lru_cache

from config import config

@lru_cache(20)
def get_news():
    ...