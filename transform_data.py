from utils import load_data, transform_product, transform_trnx, denormalise_data, create_customer_profile

# Load Data
print("Loading raw data...")
trnx, product, store, display = load_data()
print("\tDone!")
# Data Transformation & Feature Engineering

print("Running transformations on raw data...")
product = transform_product(product)
trnx = transform_trnx(trnx)
print("\tDone!")

print("Denormalising data...")
denorm_trnx = denormalise_data(trnx, product, store, display)
print("\tDone!")

# Save profile to disk
print("Saving Denormalised data to disk...")
denorm_trnx.to_csv("data/denorm_trnx.csv")
print("\tDone!")

# Create Customer Profile Table
print("Creating Customer Profile table...")
customer_profile = create_customer_profile(denorm_trnx)
print("\tDone")

# Save profile to disk
print("Saving Customer Profile to Disk...")
customer_profile.to_csv("data/customer_profile.csv")
print("\tDone!")
