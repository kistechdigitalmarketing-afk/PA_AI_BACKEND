import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
import os

# 1. SETUP & LOADING
excel_file = "tasks_export.xlsx"
if not os.path.exists(excel_file):
    print(f"❌ Error: {excel_file} not found.")
    exit()

print("📊 Loading Excel data...")
df = pd.read_excel(excel_file)

# 2. COLUMN SAFETY MAPPING
# This section renames your Excel columns to exactly what the script expects
# even if there are hidden spaces or different casing.
df.columns = df.columns.str.strip() # Remove hidden spaces

# Map the names found in your image to the names needed by the script
column_mapping = {
    'Working Count': 'Working Count',
    'User Role': 'User Role',
    'User ID': 'User ID',
    'Status': 'Status',
    'Approval Status': 'Approval Status',
    'Due Date': 'Due Date',
    'Submitted At': 'Submitted At',
    'Approved At': 'Approved At'
}
df = df.rename(columns=column_mapping)

# 3. DATA CLEANING
# Convert all date columns to actual datetime objects
date_cols = ['Due Date', 'Created At', 'Submitted At', 'Approved At']
for col in date_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# 4. FEATURE ENGINEERING
today = pd.Timestamp.now()
df['is_overdue'] = (df['Status'].str.lower() != 'completed') & (df['Due Date'] < today)

# Calculate Supervisor Speed
df['approval_speed_hrs'] = (df['Approved At'] - df['Submitted At']).dt.total_seconds() / 3600
df['approval_speed_hrs'] = df['approval_speed_hrs'].fillna(0)

# 5. TRAINING STAFF MODEL
print("🤖 Training Staff Brain...")
staff_features = []

for user, group in df.groupby('User ID'):
    total = len(group)
    comp_rate = group[group['Status'].str.lower() == 'completed'].shape[0] / total
    overdue_rate = group[group['is_overdue'] == True].shape[0] / total
    
    # Using .get() prevents the script from crashing if a column is missing
    avg_logs = group['Working Count'].mean() if 'Working Count' in group.columns else 0
    
    staff_features.append([comp_rate, overdue_rate, avg_logs])

X_staff = pd.DataFrame(staff_features, columns=['comp_rate', 'overdue_rate', 'avg_logs'])
# Lowered contamination to 0.05 for more accurate scoring
staff_model = IsolationForest(contamination=0.05, random_state=42)
staff_model.fit(X_staff)

# Ensure app directory exists
if not os.path.exists("app"):
    os.makedirs("app")

joblib.dump(staff_model, "app/staff_model.pkl")

# 6. TRAINING SUPERVISOR MODEL
print("🤖 Training Supervisor Model...")
supervisor_roles = ['supervisor', 'country_admin']
sup_df = df[df['User Role'].str.lower().isin(supervisor_roles)]
sup_features = []

for user, group in sup_df.groupby('User ID'):
    total = len(group)
    valid_approvals = group[group['approval_speed_hrs'] > 0]
    avg_speed = valid_approvals['approval_speed_hrs'].mean() if not valid_approvals.empty else 0
    rej_rate = group[group['Approval Status'].str.lower() == 'rejected'].shape[0] / total
    sup_features.append([avg_speed, rej_rate])

if sup_features:
    X_sup = pd.DataFrame(sup_features, columns=['avg_speed', 'rej_rate'])
    sup_model = IsolationForest(contamination=0.05, random_state=42)
    sup_model.fit(X_sup)
    joblib.dump(sup_model, "app/supervisor_model.pkl")

print("\n🎉 All models trained and saved successfully in 'app/' folder!")