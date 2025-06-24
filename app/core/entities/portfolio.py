from datetime import datetime

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
        self.btci_start_amount: float = 0
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

    def __repr__(self):
        return (
            f"Portfolio(source={self.source}, source_id={self.source_id}, "
            f"created_date={self.created_date})"
        )

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

    def format_portfolio_summary(self) -> str:
        portfolio_id = getattr(self, "source_id", "N/A")

        # --- Helper for formatting values ---
        def format_value(value, value_type=None):
            if value is None:
                return "N/A"
            if value_type == "currency":
                return f"${value:,.2f}"
            if value_type == "percent":
                return f"{value:.2f}%"
            return str(value)

        # --- 1. Build the main comparison table ---
        lines = [
            f"--- Portfolio Performance Summary (ID: {portfolio_id}) ---",
            f"{'Metric':<22} | {'Your Portfolio':<18} | {'BTCI Benchmark':<18} | {'Difference'}",
            "-" * 78
        ]

        comparisons = [
            ("Current Value", "current_value",
             "btci_current_value", "currency"),
            ("Total Profit", "profit_total",
             "btci_profit_total", "currency"),
            ("Profit Percentage", "profit_percentage",
             "btci_profit_percentage", "percent")
        ]

        for name, key, btci_key, v_type in comparisons:
            # Access attributes using getattr for safety
            your_val = getattr(self, key, 0.0)
            btci_val = getattr(self, btci_key, 0.0)
            diff = your_val - btci_val

            sign = "+" if diff >= 0 else ""
            
            your_val_str = format_value(your_val, v_type)
            btci_val_str = format_value(btci_val, v_type)
            diff_str = f"{sign}{format_value(diff, v_type)}"
            
            lines.append(f"{name:<22} | {your_val_str:<18} | {btci_val_str:<18} | {diff_str}")

        # --- 2. Build the overview of other values ---
        lines.extend([
            "\n" + "-" * 30,
            "--- Additional Information ---",
            "-" * 30
        ])
        
        # Access attributes directly or with getattr
        overview_items = {
            "Total Investment": format_value(
                getattr(self, "total_investment", None), "currency"),
            "BTCI Start Amount": format_value(
                getattr(self, "btci_start_amount", None)),
            "Data Source": getattr(self, "source", "N/A"),
            "Source ID": getattr(self, "source_id", "N/A"),
            "Created Date": getattr(self, "created_date", "N/A"),
            "Last Updated": getattr(self, "updated_date", "N/A")
        }
        
        for key, value in overview_items.items():
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            lines.append(f"{key:<22}: {value}")
            
        return "\n".join(lines)