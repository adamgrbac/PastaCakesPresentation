import pandas as pd
from utils.column_transforms import product_size_oz, fill_product_size, sweet_or_savoury, purchase_customer_segment, product_customer_segment
        
def load_data(data_dir="data"):
    if data_dir[-1] in ["/", "\\"]:
        data_dir = data_dir[:-1]
    trnx = pd.read_csv(f"{data_dir}/transactions.csv", na_values = [" ", ""])
    product = pd.read_csv(f"{data_dir}/product_lookup.csv", na_values = [" ", ""])
    store = pd.read_csv(f"{data_dir}/store_lookup.csv", na_values = [" ", ""])
    display = pd.read_csv(f"{data_dir}/causal_lookup.csv", na_values = [" ", ""])
    
    return trnx, product, store, display
        
def transform_product(product):
    # Fill any missing product sizes where possible (43596 missing initially)
    product["product_size_fix"] = product.apply(func=fill_product_size, axis=1)

    # Convert Product Size to OZ
    product["product_size_oz"] = product["product_size_fix"].apply(func=product_size_oz)
        
    # Add Sweet or Savoury Column
    product["sweet_savoury"] = product["commodity"].apply(sweet_or_savoury)
    
    return product
    
def transform_trnx(trnx):

    # Change sales to float
    trnx["sales"] = trnx["Dollar Sales"].str.replace("$","").apply(func=float)

    # Change Trnx Date Time to a python datetime
    trnx["Transaction Date Time"] = pd.to_datetime(trnx["Transaction Date Time"],format="%d/%m/%Y %I:%M:%S %p")

    # Add price variable
    trnx["price"] = trnx.apply(lambda row: row["sales"] / row["Units"], axis=1)

    # Add "Year" Column
    trnx["Year"] = trnx["Week"].apply(lambda x: (x-1) // 52)

    # Add "WeekOfYear" Column
    trnx["WeekOfYear"] = trnx["Week"].apply(lambda x: (x-1) % 52)
    
    return trnx

def denormalise_data(trnx, product, store, display):
    
    denorm_trnx = trnx.merge(product, 
                         left_on= "Upc", 
                         right_on = "upc", 
                         how= "left").drop("upc", axis=1)
    denorm_trnx = denorm_trnx.merge(store, 
                                    left_on= "Store", 
                                    right_on = "store", 
                                    how= "left").drop("store", axis=1)
    denorm_trnx = denorm_trnx.merge(display, 
                                    left_on= ["Store","Upc","Week","Geography"], 
                                    right_on= ["store","upc","week","geography"], 
                                    how= "left").drop(["store","upc","week","geography"], axis=1)

    ## Fill NaN values for display data
    denorm_trnx["feature_desc"] = denorm_trnx["feature_desc"].fillna("Not on Feature")
    denorm_trnx["display_desc"] = denorm_trnx["display_desc"].fillna("Not on Display")
    
    return denorm_trnx
    
def create_customer_profile(denorm_trnx):
    customer_profile = denorm_trnx.groupby("Household").agg({"sales": ["sum"], 
                                                          "Units": ["sum"], 
                                                          "Upc": ["nunique"],
                                                          "Week": ["nunique", "max", "min"],
                                                          "Basket ID": ["nunique"],
                                                          "Coupon": ["sum", "mean"],
                                                          "commodity": ["nunique", pd.Series.mode],
                                                          "brand": ["nunique", pd.Series.mode],
                                                          "sweet_savoury": ["nunique", "min"],
                                                          "Store": ["nunique", pd.Series.mode],
                                                          "Transaction Date Time": ["max"]})

    # Rename columns to remove multilevel
    customer_profile.columns = ["total_sales", 
                                "total_units", 
                                "num_products", 
                                "num_weeks", 
                                "max_week",
                                "min_week",
                                "num_visits", 
                                "total_coupons",
                                "coupon_pct",
                                "num_commodity",
                                "fave_commodity",
                                "num_brand",
                                "fave_brand",
                                "num_sweet_savoury",
                                "sweet_or_savoury",
                                "num_stores",
                                "fave_store",
                                "last_trnx"]

    # Create profile attributes using only the latest year
    customer_profile_this_year = denorm_trnx[denorm_trnx["Week"] > 52].groupby("Household").agg({"sales": ["sum"], 
                                                                                                 "Units": ["sum"],
                                                                                                 "Week": ["nunique"],
                                                                                                 "Basket ID": ["nunique"]})

    # Rename columns to remove multilevel
    customer_profile_this_year.columns = ["total_sales_y2", 
                                          "total_units_y2", 
                                          "num_weeks_y2", 
                                          "num_visits_y2"]

    # Create new column to class a customer as "sweet" or "savoury"
    customer_profile["sweet_savoury_mix"] = customer_profile.apply(lambda row: "Both" if row["num_sweet_savoury"] == 2 else row["sweet_or_savoury"], axis= 1)

    # Remove uncessary columns
    customer_profile = customer_profile.drop(["num_sweet_savoury", "sweet_or_savoury"], axis=1)

    # Join latest year attributes
    customer_profile = customer_profile.join(customer_profile_this_year, how="left")

    # Create Customer Segments
    customer_profile["purchase_segment"] = customer_profile.apply(purchase_customer_segment, axis = 1)
    customer_profile["product_segment"] = customer_profile.apply(product_customer_segment, axis = 1)
    customer_profile["recency"] = customer_profile["max_week"].rank(pct=True).apply(lambda x: 1 if x > 0.66 else 2 if x > 0.33 else 3)
    customer_profile["frequency"] = customer_profile["num_visits_y2"].fillna(0).rank(pct=True).apply(lambda x: 1 if x > 0.66 else 2 if x > 0.33 else 3)
    customer_profile["monetary"] = customer_profile["total_sales_y2"].fillna(0).rank(pct=True).apply(lambda x: 1 if x > 0.66 else 2 if x > 0.33 else 3)
    
    return customer_profile