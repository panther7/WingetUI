from PySide6.QtGui import QIcon
from tools import getMedia, _


class Store():
    def __init__(self, id: str, label = "", canShowInfo = False):
        if (id == ""): raise Exception("Id must ba a non-empty string")
        self.id = id
        self.icon = QIcon(getMedia(id))
        self.label = label or id
        self.canShowInfo = canShowInfo


unknownStore = Store(id = "__unknown__", label = "Unknown")


class Stores():
    def __init__(self):
        self._list: dict[str, Store] = {}
        
    def get(self, id: str) -> Store:
        return self._list.get(id, None)

    def exists(self, id: str):
        return (id in self._list)

    def _set(self, store: Store):
        self._list[store.id] = store


stores = Stores()
stores._set(Store(id = "winget", label = "Winget", canShowInfo = True))
stores._set(Store(id = "scoop", label = "Scoop", canShowInfo = True))
stores._set(Store(id = "localpc", label = _("Local PC")))
stores._set(Store(id = "msstore", label = "Microsoft Store"))
stores._set(Store(id = "steam", label = "Steam"))
stores._set(Store(id = "gog", label = "GOG"))
stores._set(Store(id = "uplay", label = "Ubisoft Connect"))


# only export stores
__all__ = ["stores"]
