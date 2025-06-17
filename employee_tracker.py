
import streamlit as st
import pandas as pd
import plotly.express as px
import uuid

# Set page configuration
st.set_page_config(page_title="Employee Performance Dashboard", layout="wide")

st.title("Employee Performance Dashboard")
st.markdown("Interactive visualizations of employee performance metrics.")

@st.cache_data
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/1OxU_4C8zAp_3sqcmj2dnn4YB7N6xcI6PUPLWSG-yl4E/export?format=csv"
    df = pd.read_csv(sheet_url)
    return df

df = load_data()

# Preprocessing
df['Hire_Date'] = pd.to_datetime(df['Hire_Date'], dayfirst=True, errors='coerce')
df['Years_At_Company'] = (pd.Timestamp.now() - df['Hire_Date']).dt.days / 365.25
df['Performance_Level'] = df['Performance_Score'].apply(lambda x: 'Low' if x < 3 else 'Medium' if x == 3 else 'High')

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

# Department filter
departments = df['Department'].dropna().unique().tolist()
department_colors = px.colors.qualitative.Dark2[:len(departments)]
department_color_map = dict(zip(departments, department_colors))

if 'selected_department' not in st.session_state:
    st.session_state.selected_department = departments

dept_input = st.sidebar.text_input("Type Department(s) (comma-separated)", value=", ".join(st.session_state.selected_department))
if dept_input:
    input_depts = [d.strip() for d in dept_input.split(",") if d.strip() in departments]
    st.session_state.selected_department = input_depts if input_depts else st.session_state.selected_department

col1, col2 = st.sidebar.columns(2)
if col1.button("Select All Departments"):
    st.session_state.selected_department = departments
if col2.button("Deselect All Departments"):
    st.session_state.selected_department = []

# Job title filter
job_titles = df['Job_Title'].dropna().unique().tolist()
job_title_colors = px.colors.qualitative.Dark24[:len(job_titles)]
job_title_color_map = dict(zip(job_titles, job_title_colors))

if 'selected_job_title' not in st.session_state:
    st.session_state.selected_job_title = job_titles

job_input = st.sidebar.text_input("Type Job Title(s) (comma-separated)", value=", ".join(st.session_state.selected_job_title))
if job_input:
    input_jobs = [j.strip() for j in job_input.split(",") if j.strip() in job_titles]
    st.session_state.selected_job_title = input_jobs if input_jobs else st.session_state.selected_job_title

col3, col4 = st.sidebar.columns(2)
if col3.button("Select All Job Titles"):
    st.session_state.selected_job_title = job_titles
if col4.button("Deselect All Job Titles"):
    st.session_state.selected_job_title = []

# Apply filters
filtered_df = df[df['Department'].isin(st.session_state.selected_department) & df['Job_Title'].isin(st.session_state.selected_job_title)]

# Employee Details Table
st.subheader("Employee Details")
details_columns = ['Employee_ID', 'Department', 'Job_Title', 'Performance_Score', 
                 'Employee_Satisfaction_Score', 'Productivity score', 'Remote_Work_Category']
st.dataframe(
    filtered_df[details_columns],
    use_container_width=True,
    column_config={
        "Employee_ID": st.column_config.TextColumn("Employee ID"),
        "Performance_Score": st.column_config.NumberColumn("Performance Score", format="%.1f"),
        "Employee_Satisfaction_Score": st.column_config.NumberColumn("Satisfaction Score", format="%.1f"),
        "Productivity score": st.column_config.NumberColumn("Productivity Score", format="%.2f")
    }
)

# Treemap
st.subheader("Performance Level Distribution by Job Title")
tree_data = filtered_df.groupby(['Job_Title', 'Performance_Level']).agg({'Employee_ID': 'count'}).reset_index()
fig_tree = px.treemap(
    tree_data,
    path=['Job_Title', 'Performance_Level'],
    values='Employee_ID',
    color='Performance_Level',
    color_discrete_map={'Low': '#FF4040', 'Medium': '#FFA500', 'High': '#228B22'},
    title="Click on a job title to drill down"
)
fig_tree.update_traces(
    hovertemplate='%{label}<br>Count: %{value}',
    textinfo="label+value+percent parent"
)
st.plotly_chart(fig_tree, use_container_width=True)

# Retention Risk Bar Chart
st.subheader("Employee Count by Retention Risk Level and Job Title")
retention_count = filtered_df.groupby(['Job_Title', 'Retention_Risk_Level'])['Employee_ID'].count().reset_index()
fig_ret = px.bar(
    retention_count,
    x='Job_Title',
    y='Employee_ID',
    color='Retention_Risk_Level',
    title='Employee Count by Retention Risk Level (Click bars to filter)',
    color_discrete_map={'Low': '#8B0000', 'Medium': '#FFA500', 'High': '#006400'}
)
fig_ret.update_layout(clickmode='event+select')
st.plotly_chart(fig_ret, use_container_width=True)

# Pie Chart: Remote Work with Department Filter
st.subheader("Remote Work Type Distribution")
remote_dept_filter = st.multiselect(
    "Filter by Department for Remote Work",
    departments,
    default=departments,
    key=str(uuid.uuid4())
)
remote_filtered_df = filtered_df[filtered_df['Department'].isin(remote_dept_filter)]
remote_data = remote_filtered_df['Remote_Work_Category'].value_counts().reset_index()
remote_data.columns = ['Remote_Work_Category', 'Count']
fig_pie = px.pie(
    remote_data,
    names='Remote_Work_Category',
    values='Count',
    title="Remote Work Type Distribution (Hover for details)",
    color='Remote_Work_Category',
    color_discrete_map={'Work From Home': '#1E90FF', 'Work From Office': '#696969', 'Hybrid': '#228B22'}
)
fig_pie.update_traces(
    hovertemplate='%{label}: %{value} employees (%{percent})',
    textposition='inside',
    textinfo='percent+label'
)
st.plotly_chart(fig_pie, use_container_width=True)

# Satisfaction Chart
st.subheader("Average Employee Satisfaction by Department")
sat_avg = filtered_df.groupby('Department')['Employee_Satisfaction_Score'].mean().reset_index()
fig_sat = px.bar(
    sat_avg,
    x='Department',
    y='Employee_Satisfaction_Score',
    title="Average Satisfaction Score by Department",
    color='Department',
    color_discrete_map=department_color_map
)
fig_sat.update_traces(
    hovertemplate='Department: %{x}<br>Average Satisfaction Score: %{y:.2f}',
    marker=dict(line=dict(color='#000000', width=1))
)
fig_sat.update_yaxes(range=[0, 5])
st.plotly_chart(fig_sat, use_container_width=True)

# Line Chart: Performance Over Time
st.subheader("Performance Score Trend by Years at Company")
filtered_df['Years_Bin'] = pd.cut(filtered_df['Years_At_Company'], bins=10).apply(lambda x: x.mid)
trend_data = filtered_df.groupby(['Years_Bin', 'Job_Title'])['Performance_Score'].mean().reset_index()
fig_line = px.line(
    trend_data,
    x='Years_Bin',
    y='Performance_Score',
    color='Job_Title',
    title="Performance Score Trend Over Time (Hover for details)",
    color_discrete_map=job_title_color_map
)
fig_line.update_traces(mode='lines+markers', hovertemplate='Years: %{x:.1f}<br>Score: %{y:.2f}<br>Job: %{customdata[0]}', customdata=trend_data[['Job_Title']])
st.plotly_chart(fig_line, use_container_width=True)

# Productivity Chart
st.subheader("Average Productivity Score by Job Title")
prod_avg = filtered_df.groupby('Job_Title')['Productivity score'].mean().reset_index()
fig_prod = px.bar(
    prod_avg,
    x='Job_Title',
    y='Productivity score',
    color='Job_Title',
    title="Average Productivity Score by Job Title",
    color_discrete_map=job_title_color_map
)
fig_prod.update_traces(
    hovertemplate='Job Title: %{x}<br>Average Productivity: %{y:.2f}',
    marker=dict(line=dict(color='#000000', width=1))
)
fig_prod.update_yaxes(range=[0, 2])
st.plotly_chart(fig_prod, use_container_width=True)

from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 60 seconds
st_autorefresh(interval=60000, key="refresh")
