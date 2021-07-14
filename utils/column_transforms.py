import re
import math


# Function to convert product_size to OZ
def product_size_oz(val):

    nums = re.compile("([0-9]+([.][0-9]+)?)")
    num_frac = re.compile("[0-9]+ [0-9]+[/][0-9]+")
    if type(val) is float and math.isnan(val):
        value = 0
    elif "LB" in val:
        if "OZ" in val:
            [(lb, _), (oz, _)] = nums.findall(val)
            value = 16*float(lb) + float(oz)
        else:
            value = 16*float(nums.search(val).group(0))
    elif "OZ" in val or "OUNCE" in val:
        if num_frac.search(val):
            match_val = num_frac.search(val).group(0)
            (whole, frac) = match_val.split(" ")
            (num, dem) = frac.split("/")
            value = int(whole) + (int(num) / int(dem))
        elif nums.search(val):
            value = float(nums.search(val).group(0))
        else:
            value = 0
    elif "GAL" in val:
        value = 128.0
    else:
        value = 0
    return value


def fill_product_size(row):

    if (type(row["product_size"]) is float and math.isnan(row["product_size"])) or\
            (("OZ" not in row["product_size"]) and
                ("LB" not in row["product_size"]) and
                ("OUNCE" not in row["product_size"]) and
                ("GAL" not in row["product_size"])):
        res = re.search("[0-9]+([.][0-9]+)? OZ", row["product_description"])
        if res:
            return res.group(0)
        else:
            return row["product_size"]
    else:
        return row["product_size"]


def sweet_or_savoury(val):
    if "pasta" in val:
        return "Savoury"
    else:
        return "Sweet"


def purchase_customer_segment(row):
    if row["max_week"] < 52:
        return "Lost Customer"
    elif row["num_visits"] == 1 and row["max_week"] < 100:
        return "One and Done"
    elif row["num_visits"] == 1:
        return "New Customer"
    elif row["num_weeks"] > 52:
        return "Frequent Flyer"
    elif (row["total_units"] / row["num_visits"]) > 5:
        return "Bulk Buyer"
    elif (row["total_sales"] / row["total_units"]) > 5:
        return "High Roller"
    elif row["num_stores"] == 1:
        return "Store Loyal"
    else:
        return "Average Joe"


def product_customer_segment(row):
    if row["num_products"] == 1 and row["num_visits"] > 1:
        return "Product Loyal"
    elif row["num_brand"] == 1 and row["num_visits"] > 1:
        return "Brand Loyal"
    elif row["num_commodity"] == 1 and row["num_visits"] > 1:
        return "Single Type"
    elif row["sweet_savoury_mix"] != "Both":
        return "Single Taste"
    elif row["num_visits"] == 1:
        return "Too New To Tell"
    else:
        return "Limited Loyalty"
