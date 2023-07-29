import pandas as pd
import plotly.express as px
import streamlit as st
import os
import json


# Q1. Loading the Data

# 1.1 Create data frame for the main data
## Create an empty list of dataframes
dataframes = []
data_folder = "./rotate_data_case/data/flight_events/"
data_list = [file for file in os.listdir(data_folder) if file.endswith(".csv")]

## Read each CSV into a dataframe and store it in the list
for csvs in data_list:
    file_path = os.path.join(data_folder, csvs)
    df = pd.read_csv(file_path, sep = ';')
    dataframes.append(df)

## Iterate through each dataframe to print the column names
### Checking the correspondence of column names in each dataframes

for idx, df in enumerate(dataframes):
    print(f"Columns of DataFrame {idx+1}:")
    print(df.columns.tolist())
    print() # all csv files have the same columns

## Concatenate all dataframes into a single dataframe
combined_df = pd.concat(dataframes, ignore_index = True)

## Create subset of data that is relevant for the current analysis
subset_df = combined_df[['destination_icao', 'origin_icao', 'equipment', 'date']]

#%% 1.2 Load aircraft details json file

data_folder_json = "./rotate_data_case/data/airplane_details.json"
airdetails = []

with open(data_folder_json, 'r') as f:
    for line in f:
        airdetails.append(json.loads(line))

# Convert it to pandas DataFrame
airdetails = pd.DataFrame(airdetails)

#%% 1.3 Merge two dataframes

## Rename equipment to code_icao
subset_df.rename(columns = {'equipment': 'code_icao'}, inplace = True)

## Use 'inner' argument to merged based on the common 'code_icao' column
## Those that do not have info about volume nor category information cannot be used

alldetails_df = pd.merge(subset_df, airdetails, on = 'code_icao', how = 'inner')

#%% 1.4 Data Proprocessing

# Handeling missing values
## 1. Check what the proportion of the missing values are
missing_rows = alldetails_df[alldetails_df.isna().any(axis = 1)]
proportion_missing = missing_rows.shape[0] / alldetails_df.shape[0]
print("Proportion of missing data in the dataset: ", proportion_missing)
print("Specific NA Proportions Per Category:\n", alldetails_df.isna().mean())

### Since the proportion is lower 1% of the data, dropna() can be used
clean_df = alldetails_df.dropna()

#%% Q2. Capacity Table Calculation

# 1. Count flights that traveled between different airports

# Group the data by 'destination_icao', 'origin_icao', and 'code_icao', and count the flights for each group
clean_df['FlightCount'] = clean_df.groupby(['destination_icao', 
                                            'origin_icao', 
                                            'code_icao',
                                            'date'])['destination_icao'].transform('count')

# Filter out rows:
## where 'origin_icao' and 'destination_icao' are the same ((same airports)
clean_df = clean_df[clean_df['origin_icao'] != clean_df['destination_icao']]
## duplicates (leaving with only unique combination)
clean_df = clean_df[-clean_df.duplicated()]

# 2. Calculate Cargo Capacity

summary_df = clean_df.groupby(['destination_icao', 'origin_icao', 'date']).agg({
    'FlightCount': 'sum',
    'payload': 'sum',
    'volume': 'sum'}).reset_index()

summary_df['total_cargo_capacity_weight'] = summary_df['payload'] / summary_df['FlightCount']
summary_df['total_cargo_capacity_volume'] = summary_df['volume'] / summary_df['FlightCount']

print(summary_df)

#%% Q3. Create an interactive api

st.title("Total Cargo Capacity Per Day")

# Select airports
origin_icao = st.selectbox('Select Origin ICAO Code', summary_df['origin_icao'].unique())
destination_icao = st.selectbox('Select Destination ICAO Code', summary_df['destination_icao'].unique())

# Filter the DataFrame based on the selected airports
filtered_df = summary_df[
    (summary_df['origin_icao'] == origin_icao) &
    (summary_df['destination_icao'] == destination_icao)
]

# Group the filtered data by date and calculate the total cargo capacity per day
total_capacity_per_day = filtered_df.groupby(['date']).agg({
    'FlightCount': 'sum',
    'total_cargo_capacity_weight': 'sum',
    'total_cargo_capacity_volume': 'sum'
}).reset_index()

# Display the selected airports and the total cargo capacity per day
st.write(f"Selected Origin ICAO Code: {origin_icao}")
st.write(f"Selected Destination ICAO Code: {destination_icao}")

# Rename the columns for display in the DataFrame
display_df = total_capacity_per_day.rename(columns={
    'date': 'Date',
    'FlightCount': "Flight Counts",
    'total_cargo_capacity_weight': 'Total Cargo Capacity (Weight kg)',
    'total_cargo_capacity_volume': 'Total Cargo Capacity (Volume m3)'
})

# Show the DataFrame with the user-friendly column names
st.dataframe(display_df)


# Visualize cargo capacity per day
st.subheader("Capacity Weigtht & Volume")

fig = px.bar(total_capacity_per_day, x='date', y='total_cargo_capacity_weight', title='Total Cargo Capacity per Day')
fig2 = px.bar(total_capacity_per_day, x='date', y='total_cargo_capacity_volume', title='Total Cargo Capacity per Day')

# Set the Y-axis label
fig.update_yaxes(title_text='Total Weight Capacity (kg)')
fig2.update_yaxes(title_text='Total Volume Capacity (m3)')

# Set the x-axis label
x_axis_values = ['2022-10-03', '2022-10-04', '2022-10-05', '2022-10-06', 
                 '2022-10-07', '2022-10-08', '2022-10-09']
fig.update_xaxes(tickvals=x_axis_values, ticktext=x_axis_values)
fig2.update_xaxes(tickvals=x_axis_values, ticktext=x_axis_values)

fig.update_xaxes(title_text='Date')
fig2.update_xaxes(title_text='Date')

tab1, tab2 = st.tabs(["Total Capacity Weight", "Total Capacity Volume"])
with tab1:
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
with tab2:
    st.plotly_chart(fig2, theme="streamlit", use_container_width=True)
    
    
