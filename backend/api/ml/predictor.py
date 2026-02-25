def predict_business(business_type):
    if business_type == "Two-Wheeler Service Centre":
        return {
            "growth_score": 85,
            "demand_level": "High",
            "risk_level": "Low",
            "strategy": "High service demand near residential and office zones"
        }

    elif business_type == "Two-Wheeler Showroom":
        return {
            "growth_score": 72,
            "demand_level": "Medium",
            "risk_level": "Medium",
            "strategy": "Offer EMI options and festive discounts"
        }

    else:
        return {
            "growth_score": 68,
            "demand_level": "Medium",
            "risk_level": "Low",
            "strategy": "Maintain fast-moving spare parts inventory"
        }
