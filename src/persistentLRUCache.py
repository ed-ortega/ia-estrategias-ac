import pickle
from pathlib import Path
from collections import OrderedDict
from threading import RLock


class PersistentLRUCache:
    def __init__(self, path: Path, max_size: int = 10000):
        self.path = path
        self.max_size = max_size
        self.lock = RLock()
        self.cache = OrderedDict()

        self._load()

    # =========================
    # 💾 LOAD
    # =========================
    def _load(self):
        if self.path.exists():
            try:
                with open(self.path, "rb") as f:
                    data = pickle.load(f)
                    if isinstance(data, dict):
                        self.cache = OrderedDict(data)
                print(f"🧊 Cache cargado: {len(self.cache)}")
            except Exception:
                print("⚠️ Cache corrupto, reiniciando...")
                self.cache = OrderedDict()

    # =========================
    # 💾 SAVE
    # =========================
    def save(self):
        with self.lock:
            with open(self.path, "wb") as f:
                pickle.dump(dict(self.cache), f)
        print(f"💾 Cache guardado: {len(self.cache)}")

    # =========================
    # 🔍 GET
    # =========================
    def get(self, key):
        with self.lock:
            if key not in self.cache:
                return None

            # mover a reciente (LRU)
            self.cache.move_to_end(key)
            return self.cache[key]

    # =========================
    # ➕ SET
    # =========================
    def set(self, key, value):
        with self.lock:
            self.cache[key] = value
            self.cache.move_to_end(key)

            # LRU eviction
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    # =========================
    # 📊 STATS
    # =========================
    def __len__(self):
        return len(self.cache)