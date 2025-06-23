from .purchase import Purchase


class Portfolio():
    def __init__(
            self,
            source: str,
            source_id: str,
            created_date: str,
            id: str = None,
            start_value: float = 0,
            current_value: float = 0,
            profit_percentage: float = 0,
            profit_total: float = 0,
            total_investment: float = 0,
            btci_current_value: float = 0,
            btci_profit_percentage: float = 0,
            btci_profit_total: float = 0,
            updated_date: str = None
    ):
        self.id = id
        self.source = source
        self.source_id = source_id
        self.start_value = start_value
        self.current_value = current_value
        self.profit_percentage = profit_percentage
        self.profit_total = profit_total
        self.total_investment = total_investment
        self.btci_current_value = btci_current_value
        self.btci_start_amount: float = 0  # Assuming btci_start_value is same as start_value
        self.btci_profit_percentage = btci_profit_percentage
        self.btci_profit_total = btci_profit_total
        self.created_date = created_date
        self.updated_date = updated_date
        self.purchases: Purchase = []

    def get_portfolio_as_dict(self):
        return {
            "id": self.id,
            "start_value": self.start_value,
            "current_value": self.current_value,
            "profit_percentage": self.profit_percentage,
            "profit_total": self.profit_total,
            "total_investment": self.total_investment,
            "btci_current_value": self.btci_current_value,
            "btci_profit_percentage": self.btci_profit_percentage,
            "btci_profit_total": self.btci_profit_total,
            "source": self.source,
            "source_id": self.source_id,
            "created_date": self.created_date,
            "updated_date": self.updated_date,
            "btci_start_amount": self.btci_start_amount
        }

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
    
    def add_purchase(self, purchase: Purchase):
        if not isinstance(purchase, Purchase):
            raise TypeError("Expected a Purchase instance.")
        self.purchases.append(purchase)
        return self
    
    @classmethod
    def from_db_row(cls, row: tuple):
        pass
