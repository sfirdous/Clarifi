import pandas as pd
import math

def categorize_description(desc: str) -> str:
    desc = desc.strip().lower()

    categories = {
        "Groceries": ["grocery", "supermarket", "mart", "kirana"],
        "Utilities": ["electric", "water", "gas", "bill", "maintenance", "broadband", "recharge"],
        "Insurance": ["insurance", "premium"],
        "Healthcare": ["hospital", "clinic", "pharmacy", "apollo", "medic", "doctor"],
        "Education": ["school", "college", "tuition", "fees"],
        "Rent": ["rent", "landlord", "lease"],
        "Fuel": ["petrol", "diesel", "fuel", "hpcl", "indian oil", "ioc", "bharat petroleum"],
        "Transport": ["uber", "ola", "taxi", "train", "bus", "metro"],
        "Dining": ["restaurant", "cafe", "coffee", "eating", "swiggy", "zomato"],
        "Shopping": ["amazon", "flipkart", "shopping", "myntra", "snapdeal"],
        "Transfer": ["neft", "rtgs", "imps", "upi", "transfer", "paytm", "gpay", "phonepe"],
        "ATM Withdrawals": ["atm", "cash withdrawal"],
        "Misc": []  # Fallback category
    }

    for category, keywords in categories.items():
        if any(keyword in desc for keyword in keywords):
            return category

    return "Misc"

def get_week_of_month(date: pd.Timestamp) -> int:
    first_day = date.replace(day=1)
    dom = date.day
    adjusted_dom = dom + first_day.weekday()
    return math.ceil(adjusted_dom / 7.0)
