import requests
import mysql.connector
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from dateutil.parser import parse

# MySQL Configuration (Replace with your credentials)
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Replace with your MySQL username
    'password': 'root',  # Replace with your MySQL password
    'database': 'neo_data'
}

# Step 1: NASA API Key and Data Extraction
API_KEY = "Hvbz9u74Q2Pb7FRGladdQQ9cfEoVCi76iKdJCLcw"  # Replace with your NASA API key
BASE_URL = "https://api.nasa.gov/neo/rest/v1/feed"

def fetch_neo_data(start_date, end_date):
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "api_key": API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def extract_asteroid_data(start_date_str="2024-01-01", max_records=10000):
    asteroids = []
    close_approaches = []
    current_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    
    while len(asteroids) < max_records:
        end_date = current_date + timedelta(days=7)
        end_date_str = end_date.strftime("%Y-%m-%d")
        current_date_str = current_date.strftime("%Y-%m-%d")
        
        data = fetch_neo_data(current_date_str, end_date_str)
        
        for date, neo_list in data['near_earth_objects'].items():
            for neo in neo_list:
                if len(asteroids) >= max_records:
                    break
                
                asteroid_id = int(neo['id'])
                asteroid_data = {
                    'id': asteroid_id,
                    'name': neo['name'],
                    'absolute_magnitude_h': float(neo.get('absolute_magnitude_h', 0)),
                    'estimated_diameter_min_km': float(neo['estimated_diameter']['kilometers']['estimated_diameter_min']),
                    'estimated_diameter_max_km': float(neo['estimated_diameter']['kilometers']['estimated_diameter_max']),
                    'is_potentially_hazardous_asteroid': neo['is_potentially_hazardous_asteroid']
                }
                
                for approach in neo['close_approach_data']:
                    close_approach_data = {
                        'neo_reference_id': asteroid_id,
                        'close_approach_date': parse(approach['close_approach_date']).date(),
                        'relative_velocity_kmph': float(approach['relative_velocity']['kilometers_per_hour']),
                        'astronomical': float(approach['miss_distance']['astronomical']),
                        'miss_distance_km': float(approach['miss_distance']['kilometers']),
                        'miss_distance_lunar': float(approach['miss_distance']['lunar']),
                        'orbiting_body': approach['orbiting_body']
                    }
                    close_approaches.append(close_approach_data)
                
                asteroids.append(asteroid_data)
        
        next_url = data['links'].get('next')
        if not next_url:
            break
        current_date = end_date + timedelta(days=1)
    
    return asteroids, close_approaches

# Step 2: Create MySQL Database and Tables
def create_database():
    conn = mysql.connector.connect(
        host=MYSQL_CONFIG['host'],
        user=MYSQL_CONFIG['user'],
        password=MYSQL_CONFIG['password']
    )
    cursor = conn.cursor()
    
    cursor.execute("CREATE DATABASE IF NOT EXISTS neo_data")
    conn.commit()
    cursor.close()
    conn.close()
    
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asteroids (
            id INT,
            name VARCHAR(255),
            absolute_magnitude_h FLOAT,
            estimated_diameter_min_km FLOAT,
            estimated_diameter_max_km FLOAT,
            is_potentially_hazardous_asteroid BOOLEAN
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS close_approach (
            neo_reference_id INT,
            close_approach_date DATE,
            relative_velocity_kmph FLOAT,
            astronomical FLOAT,
            miss_distance_km FLOAT,
            miss_distance_lunar FLOAT,
            orbiting_body VARCHAR(50)
        )
    ''')
    
    conn.commit()
    return conn, cursor

# Step 3: Insert Data into MySQL
def insert_data(asteroids, close_approaches):
    conn, cursor = create_database()
    
    for asteroid in asteroids:
        cursor.execute('''
            INSERT INTO asteroids (id, name, absolute_magnitude_h, estimated_diameter_min_km, 
                                estimated_diameter_max_km, is_potentially_hazardous_asteroid)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            asteroid['id'],
            asteroid['name'],
            asteroid['absolute_magnitude_h'],
            asteroid['estimated_diameter_min_km'],
            asteroid['estimated_diameter_max_km'],
            asteroid['is_potentially_hazardous_asteroid']
        ))
    
    for approach in close_approaches:
        cursor.execute('''
            INSERT INTO close_approach (neo_reference_id, close_approach_date, relative_velocity_kmph, 
                                     astronomical, miss_distance_km, miss_distance_lunar, orbiting_body)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            approach['neo_reference_id'],
            approach['close_approach_date'],
            approach['relative_velocity_kmph'],
            approach['astronomical'],
            approach['miss_distance_km'],
            approach['miss_distance_lunar'],
            approach['orbiting_body']
        ))
    
    conn.commit()
    conn.close()

# Step 4: SQL Queries
QUERIES = {
    "Count asteroid approaches": '''
        SELECT a.name, COUNT(c.neo_reference_id) as approach_count
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        GROUP BY a.id, a.name
        ORDER BY approach_count DESC
    ''',
    "Average velocity per asteroid": '''
        SELECT a.name, AVG(c.relative_velocity_kmph) as avg_velocity
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        GROUP BY a.id, a.name
        ORDER BY avg_velocity DESC
    ''',
    "Top 10 fastest asteroids": '''
        SELECT a.name, MAX(c.relative_velocity_kmph) as max_velocity
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        GROUP BY a.id, a.name
        ORDER BY max_velocity DESC
        LIMIT 10
    ''',
    "Hazardous asteroids with >3 approaches": '''
        SELECT a.name, COUNT(c.neo_reference_id) as approach_count
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        WHERE a.is_potentially_hazardous_asteroid = 1
        GROUP BY a.id, a.name
        HAVING approach_count > 3
        ORDER BY approach_count DESC
    ''',
    "Month with most approaches": '''
        SELECT DATE_FORMAT(c.close_approach_date, '%Y-%m') as month, 
               COUNT(*) as approach_count
        FROM close_approach c
        GROUP BY month
        ORDER BY approach_count DESC
        LIMIT 1
    ''',
    "Fastest ever approach": '''
        SELECT a.name, c.relative_velocity_kmph, c.close_approach_date
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        ORDER BY c.relative_velocity_kmph DESC
        LIMIT 1
    ''',
    "Sort by max diameter": '''
        SELECT a.name, a.estimated_diameter_max_km
        FROM asteroids a
        ORDER BY a.estimated_diameter_max_km DESC
    ''',
    "Asteroid with decreasing distance": '''
        SELECT a.name, c.close_approach_date, c.miss_distance_km
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        WHERE a.id IN (
            SELECT neo_reference_id
            FROM close_approach
            GROUP BY neo_reference_id
            HAVING COUNT(*) > 1
        )
        ORDER BY a.id, c.close_approach_date, c.miss_distance_km
    ''',
    "Closest approach per asteroid": '''
        SELECT a.name, c.close_approach_date, MIN(c.miss_distance_km) as min_distance
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        GROUP BY a.id, a.name
    ''',
    "Asteroids with velocity > 50,000 km/h": '''
        SELECT DISTINCT a.name
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        WHERE c.relative_velocity_kmph > 50000
    ''',
    "Approaches per month": '''
        SELECT DATE_FORMAT(c.close_approach_date, '%Y-%m') as month, 
               COUNT(*) as approach_count
        FROM close_approach c
        GROUP BY month
        ORDER BY month
    ''',
    "Asteroid with highest brightness": '''
        SELECT a.name, a.absolute_magnitude_h
        FROM asteroids a
        WHERE a.absolute_magnitude_h = (
            SELECT MIN(absolute_magnitude_h) 
            FROM asteroids
        )
    ''',
    "Hazardous vs non-hazardous count": '''
        SELECT is_potentially_hazardous_asteroid, 
               COUNT(*) as count
        FROM asteroids
        GROUP BY is_potentially_hazardous_asteroid
    ''',
    "Asteroids closer than Moon": '''
        SELECT a.name, c.close_approach_date, c.miss_distance_lunar
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        WHERE c.miss_distance_lunar < 1
        ORDER BY c.miss_distance_lunar
    ''',
    "Asteroids within 0.05 AU": '''
        SELECT a.name, c.close_approach_date, c.astronomical
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        WHERE c.astronomical < 0.05
        ORDER BY c.astronomical
    '''
}

# Step 5: Streamlit Dashboard
def run_streamlit():
    st.title("NASA Asteroid Tracker")
    st.image("https://img.icons8.com/color/48/000000/rocket.png", width=40)  # Add a rocket icon
    
    # Sidebar for Queries
    st.sidebar.title("Asteroid Approaches")
    st.sidebar.subheader("Queries")
    query_name = st.sidebar.selectbox("Select Query", list(QUERIES.keys()))
    
    # Right-side Filters
    st.sidebar.title("Filter Criteria")
    st.sidebar.subheader("Filter")
    min_magnitude = st.sidebar.slider("Min Magnitude", 10.0, 40.0, 10.0)
    max_magnitude = st.sidebar.slider("Max Magnitude", 10.0, 40.0, 40.0)
    min_diameter = st.sidebar.slider("Min Estimated Diameter (km)", 0.0, 20.0, 0.0)
    max_diameter = st.sidebar.slider("Max Estimated Diameter (km)", 0.0, 20.0, 20.0)
    min_velocity = st.sidebar.slider("Relative Velocity (km/h) Range", 0, 200000, 0)
    max_velocity = st.sidebar.slider("Relative Velocity (km/h) Range", 0, 200000, 200000)
    min_au = st.sidebar.slider("Astronomical Unit", 0.0, 1.0, 0.0)
    max_au = st.sidebar.slider("Astronomical Unit", 0.0, 1.0, 1.0)
    only_hazardous = st.sidebar.selectbox("Only Show Potentially Hazardous", ["No", "Yes"])
    
    start_date = st.sidebar.date_input("Start Date", datetime(2024, 1, 1))
    end_date = st.sidebar.date_input("End Date", datetime(2025, 4, 13))
    
    # Display Query Results
    if query_name:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        df = pd.read_sql_query(QUERIES[query_name], conn)
        st.write(f"Results for: {query_name}")
        st.dataframe(df)
        conn.close()
    
    # Dynamic Filter Query
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    filter_query = '''
        SELECT a.id, a.name, a.absolute_magnitude_h, a.estimated_diameter_min_km, 
               a.estimated_diameter_max_km, a.is_potentially_hazardous_asteroid, c.relative_velocity_kmph
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        WHERE a.absolute_magnitude_h BETWEEN %s AND %s
        AND a.estimated_diameter_min_km >= %s
        AND a.estimated_diameter_max_km <= %s
        AND c.relative_velocity_kmph BETWEEN %s AND %s
        AND c.astronomical BETWEEN %s AND %s
        AND c.close_approach_date BETWEEN %s AND %s
    '''
    params = (min_magnitude, max_magnitude, min_diameter, max_diameter, 
              min_velocity, max_velocity, min_au, max_au, start_date, end_date)
    
    if only_hazardous == "Yes":
        filter_query += " AND a.is_potentially_hazardous_asteroid = 1"
    
    filtered_df = pd.read_sql_query(filter_query, conn, params=params)
    st.subheader("Filtered Asteroids")
    st.dataframe(filtered_df)
    conn.close()

if __name__ == "__main__":
    # Fetch and store data
    asteroids, close_approaches = extract_asteroid_data()
    insert_data(asteroids, close_approaches)
    
    # Run Streamlit
    run_streamlit()