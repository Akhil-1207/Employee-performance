import streamlit as st
import pandas as pd
import plotly.express as px
import uuid
from streamlit_autorefresh import st_autorefresh

# Set page configuration
st.set_page_config(page_title="Employee Performance Dashboard", layout="wide")
st.markdown("""
    <style>
    .main {
        background-color: #f5f6f5;  /* Light neutral gray for a subtle, non-contrasting background */
    }
    </style>
    """, unsafe_allow_html=True)
st.title("Employee Performance Dashboard")
st.markdown("Interactive visualizations of employee performance metrics.")

# Load local CSV instead of Google Sheet
df = pd.read_csv("Extended_Employee_Performance_and_Productivity_Data(with kpi).csv")

# Preprocessing
df['Hire_Date'] = pd.to_datetime(df['Hire_Date'], errors='coerce')
df['Years_At_Company'] = (pd.Timestamp.now() - df['Hire_Date']).dt.days / 365.25
df['Performance_Level'] = df['Performance_Score'].apply(lambda x: 'Low' if x < 3 else 'Medium' if x == 3 else 'High')
df['Satisfaction_Level'] = df['Employee_Satisfaction_Score'].apply(lambda x: 'Low' if x < 3 else 'Medium' if x == 3 else 'High')

def retention_level(index):
    if index < 0.8:
        return 'Low'
    elif 0.8 <= index < 1.5:
        return 'Medium'
    else:
        return 'High'

df['Retention_Risk_Level'] = df['Retension risk index'].apply(retention_level)

def remote_category(val):
    if val == 0:
        return 'Work From Office'
    elif val == 100:
        return 'Work From Home'
    else:
        return 'Hybrid'

df['Remote_Work_Category'] = df['Remote_Work_Frequency'].apply(remote_category)

# Sidebar filters
st.sidebar.header("Filters")
departments = df['Department'].dropna().unique().tolist()
job_titles = df['Job_Title'].dropna().unique().tolist()
remote_options = ['All', 'Work From Home', 'Work From Office', 'Hybrid']

selected_department = st.sidebar.selectbox("Select Department", ["All"] + departments)
selected_job = st.sidebar.selectbox("Select Job Title", ["All"] + job_titles)
selected_remote = st.sidebar.selectbox("Select Remote Work Type", remote_options)
date_range = st.sidebar.date_input("Filter by Hire Date Range", [df['Hire_Date'].min(), df['Hire_Date'].max()])

# Apply filters
filtered_df = df.copy()
if selected_department != "All":
    filtered_df = filtered_df[filtered_df['Department'] == selected_department]
if selected_job != "All":
    filtered_df = filtered_df[filtered_df['Job_Title'] == selected_job]
if selected_remote != "All":
    filtered_df = filtered_df[filtered_df['Remote_Work_Category'] == selected_remote]
if len(date_range) == 2:
    filtered_df = filtered_df[(filtered_df['Hire_Date'] >= pd.to_datetime(date_range[0])) &
                              (filtered_df['Hire_Date'] <= pd.to_datetime(date_range[1]))]

# Cards for Productivity and Remote Work Efficiency
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        f"""
        <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
            <h3 style="margin: 0;">Average Productivity Score</h3>
            <p style="font-size: 24px; color: #0066cc;">{filtered_df['Productivity score'].mean():.2f}</p>
        </div>
        """, unsafe_allow_html=True)
with col2:
    remote_efficiency = filtered_df.groupby('Remote_Work_Category')['Productivity score'].mean()
    hybrid_score = remote_efficiency.get('Hybrid', 0)
    st.markdown(
        f"""
        <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
            <h3 style="margin: 0;">Remote Work Efficiency (Hybrid)</h3>
            <p style="font-size: 24px; color: #0066cc;">{hybrid_score:.2f}</p>
        </div>
        """, unsafe_allow_html=True)

# Employee Details Table
st.subheader("Employee Details")
details_columns = ['Employee_ID', 'Department', 'Job_Title', 'Performance_Level',
                   'Satisfaction_Level', 'Remote_Work_Category', 'Retention_Risk_Level']
st.dataframe(filtered_df[details_columns], use_container_width=True)

# Treemap
st.subheader("Performance Level Distribution by Job Title")
tree_data = filtered_df.groupby(['Job_Title', 'Performance_Level'])['Employee_ID'].count().reset_index()
tree_data.rename(columns={'Employee_ID': 'Number_of_Employees'}, inplace=True)
fig_tree = px.treemap(tree_data, path=['Job_Title', 'Performance_Level'], values='Number_of_Employees',
                      color='Performance_Level', color_discrete_map={'Low': '#FF4040', 'Medium': '#FFA500', 'High': '#228B22'})
fig_tree.update_traces(hovertemplate='%{label}<br>Count: %{value}', textinfo="label+value+percent parent")
st.plotly_chart(fig_tree, use_container_width=True)

# Retention Risk Bar Chart
st.subheader("Employee Count by Retention Risk Level and Job Title")
retention_count = filtered_df.groupby(['Job_Title', 'Retention_Risk_Level'])['Employee_ID'].count().reset_index()
retention_count.rename(columns={'Employee_ID': 'Number_of_Employees'}, inplace=True)
fig_ret = px.bar(retention_count, x='Job_Title', y='Number_of_Employees', color='Retention_Risk_Level',
                 color_discrete_map={'Low': '#8B0000', 'Medium': '#FFA500', 'High': '#006400'})
st.plotly_chart(fig_ret, use_container_width=True)

# Remote Work Pie Chart
st.subheader("Remote Work Type Distribution")
remote_data = filtered_df['Remote_Work_Category'].value_counts().reset_index()
remote_data.columns = ['Remote_Work_Category', 'Count']
fig_pie = px.pie(remote_data, names='Remote_Work_Category', values='Count',
                 color_discrete_map={'Work From Home': '#1E90FF', 'Work From Office': '#696969', 'Hybrid': '#228B22'})
fig_pie.update_traces(hovertemplate='%{label}: %{value} employees (%{percent})', textposition='inside',
                      textinfo='percent+label')
st.plotly_chart(fig_pie, use_container_width=True)

# Satisfaction Chart
st.subheader("Average Employee Satisfaction by Department")
sat_avg = filtered_df.groupby('Department')['Employee_Satisfaction_Score'].mean().reset_index()
fig_sat = px.bar(sat_avg, x='Department', y='Employee_Satisfaction_Score',
                 title="Average Satisfaction Score by Department",
                 color='Department',
                 color_discrete_sequence=px.colors.qualitative.Plotly)
fig_sat.update_traces(marker=dict(line=dict(color='#000000', width=1)))
fig_sat.update_yaxes(range=[0, 5])
st.plotly_chart(fig_sat, use_container_width=True)

# Line Chart
st.subheader("Performance Score Trend by Years at Company")
filtered_df['Years_Bin'] = pd.cut(filtered_df['Years_At_Company'], bins=10).apply(lambda x: x.mid)
trend_data = filtered_df.groupby(['Years_Bin', 'Job_Title'])['Performance_Score'].mean().reset_index()
fig_line = px.line(trend_data, x='Years_Bin', y='Performance_Score', color='Job_Title')
fig_line.update_traces(mode='lines+markers')
st.plotly_chart(fig_line, use_container_width=True)

# Productivity Chart
st.subheader("Average Productivity Score by Job Title")
prod_avg = filtered_df.groupby('Job_Title')['Productivity score'].mean().reset_index()
fig_prod = px.bar(prod_avg, x='Job_Title', y='Productivity score', color='Job_Title')
fig_prod.update_traces(marker=dict(line=dict(color='#000000', width=1)))
fig_prod.update_yaxes(range=[0, 2])
st.plotly_chart(fig_prod, use_container_width=True)

# Auto-refresh
st_autorefresh(interval=60000, key="refresh")
