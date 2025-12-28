"""
Lightweight tqdm shim for QGIS deployments where the real tqdm package is absent.
Provides a minimal iterable wrapper so existing loops continue to function.
"""

class _Tqdm:
    def __init__(self, iterable, total=None, disable=False, **kwargs):
        self.iterable = iterable
        self.total = total
        self.disable = disable

    def __iter__(self):
        for item in self.iterable:
            yield item

    def close(self):
        # Compatibility no-op
        return None


def tqdm(iterable=None, total=None, disable=False, **kwargs):
    if iterable is None:
        iterable = range(total or 0)
    return _Tqdm(iterable, total=total, disable=disable, **kwargs)
