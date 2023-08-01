"""
This modules contains the connectivity class
"""

class Connectivity:
    """
    This class describes a connectivity.
    """
    _technology: int
    _quality: int

    def __init__(self, technology: str, quality: str = "universal"):
        match technology:
            case "leosat":
                self._technology = 0
            case "geosat":
                self._technology = 1
            case "3g":
                self._technology = 2
            case "4g":
                self._technology = 3
            case _:
                raise ValueError
        match quality:
            case "bad":
                self._quality = 0
            case "universal":
                self._quality = 1
            case "starlink":
                self._quality = 2
            case "medium":
                self._quality = 3
            case "good":
                self._quality = 4
            case _:
                raise ValueError

    def __eq__(self, other):
        if not isinstance(other, Connectivity):
            return False
        return self._technology == other._technology and self._quality == other._quality

    def __lt__(self, other):
        if not isinstance(other, Connectivity):
            return False
        return (self._technology < other._technology or
                (self._technology == other._technology and self._quality < other._quality))

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        match self._technology:
            case 0:
                name = "leosat"
            case 1:
                name = "geosat"
            case 2:
                name = "3g"
            case 3:
                name = "4g"
            case _:
                raise ValueError
        match self._quality:
            case 0:
                name += "\nbad"
            case 1:
                name += "\nuniversal"
            case 2:
                name += "\nstarlink"
            case 3:
                name += "\nmedium"
            case 4:
                name += "\ngood"
            case _:
                raise ValueError
        return name
