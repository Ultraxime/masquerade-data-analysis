"""
Module for the bulk test result
"""

from typing import List, Dict

from .result import Result


class BulkTest(Result):
    """
    This class describes a bulk test's result.
    """
    def __init__(self, folder: str = ".", name: str = "bulk_download", **kwargs):
        super().__init__(folder, name, **kwargs)

    def plot(self):
        self.subplot("bulk download", unit="mbps",
                     convert=lambda x : [int(x) / 1000000], scale="log")

    def get_download(self) -> Dict[str, List[float]]:
        """
        Gets the download speed.

        :returns:   The download speed.
        :rtype:     str * (float List) dict
        """
        return {"native": [int(test) / 1000000 for test in self._native],
                "masquerade" : [int(test) / 1000000 for test in self._masquerade],
                "squid": [int(test) / 1000000 for test in self._squid]}
