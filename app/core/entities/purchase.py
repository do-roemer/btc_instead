from app.core.database.asset_db_handler import (
    get_asset_price_from_db_by_iso_week_year
)


class Purchase():
    def __init__(
            self,
            source: str,
            source_id: str,
            name: str,
            abbreviation: str,
            amount: float,
            total_purchase_value: float,
            purchase_date: str = None,
            id: str = None,
    ):
        self.id = id
        self.source = source
        self.source_id = source_id
        self.name = name
        self.abbreviation = abbreviation
        self.amount = amount
        self.purchase_price_per_unit = total_purchase_value / amount 
        self.purchase_date = purchase_date
        self.total_purchase_value = total_purchase_value
        self.current_value: float = 0.0

    def get_purchase_as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "abbreviation": self.abbreviation,
            "amount": self.amount,
            "purchase_price_per_unit": self.purchase_price_per_unit,
            "total_purchase_value": self.total_purchase_value,
            "total_current_value": self.total_current_value,
            "source_id": self.source_id,
            "purchase_date": self.purchase_date
        }

    def get_current_value_from_db(self, db_interface) -> float:
        """
        Calculate the current value of the purchase.
        This method should be overridden in subclasses if needed.
        """
        iso_year, iso_week, _ = self.purchase_date.isocalendar()
        asset_price = get_asset_price_from_db_by_iso_week_year(
            db_interface=db_interface,
            name=self.name,
            abbreviation=self.abbreviation,
            iso_week=iso_week,
            iso_year=iso_year
        )
        if asset_price is None:
            raise ValueError(
                f"No price found for {self.name} "
                f"({self.abbreviation}) on {self.purchase_date}."
            )
        self.total_current_value = asset_price * self.amount
        return self.total_current_value

    def update_values(
            self,
            **kwargs: dict[str, float | str | int | None]
    ):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Invalid attribute: {key}")
        return self

    @classmethod
    def from_db_row(cls, row: tuple):
        pass
