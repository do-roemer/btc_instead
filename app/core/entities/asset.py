import pandas as pd


class Asset:
    def __init__(
        self,
        name: str,
        data: pd.DataFrame(),
        abbreviation: str = None
    ):
        self.name = name
        self.abbreviation = abbreviation
        self.data = data

    def __repr__(self):
        return f"Asset(name={self.name}, value={self.value})"