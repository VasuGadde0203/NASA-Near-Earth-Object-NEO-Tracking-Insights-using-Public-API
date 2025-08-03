# NASA Asteroid Tracker

## Overview

**NASA Near-Earth Object (NEO) Tracking & Insights using Public API** is a project that leverages the **NASA NEO API** to collect, store, and analyze data on near-Earth asteroids. It features:

- Data extraction with pagination
- MySQL database integration
- A Streamlit-based interactive dashboard for visualization and filtering of asteroid data

---

## Features

- **Data Extraction**: Fetches up to 10,000 asteroid records from NASA's NEO API using pagination.
- **Data Cleaning**: Converts JSON data into structured formats with proper data types.
- **Database Management**: Stores data in a MySQL database with `asteroids` and `close_approach` tables.
- **Interactive Dashboard**:
  - Filter asteroids by:
    - Magnitude
    - Estimated diameter
    - Relative velocity
    - Astronomical units
    - Hazardous status
    - Date range
  - Execute **15 predefined SQL queries** for analytical insights.
- **User Interface**: Built with Streamlit, featuring a sidebar for toggling between filtering and querying.

---

## Skills Gained

- API Integration and JSON Parsing  
- Data Transformation  
- MySQL Table Creation and Data Insertion  
- SQL Query Writing for Insights  
- Streamlit Dashboard Development  
- Filter-Based Data Interaction  

---

## Prerequisites

- Python 3.x  
- MySQL Server (with a database named `neo_data`)  
- Required Python packages:
  - `requests`
  - `pandas`
  - `streamlit`
  - `mysql-connector-python`
- **NASA API Key** (obtain from [https://api.nasa.gov](https://api.nasa.gov))

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd nasa-asteroid-tracker
```

### 2. Set Up MySQL

```bash
CREATE DATABASE neo_data;
CREATE USER 'your_username'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON neo_data.* TO 'your_username'@'localhost';
FLUSH PRIVILEGES;
```
Update MYSQL_CONFIG in neo_tracking_mysql_ui_adjusted.py with your MySQL host, username, password, and database.

### 3. Install Dependencies
```bash
pip install requests pandas streamlit mysql-connector-python
```

### 4. Obtain NASA API Key
- Register at: https://api.nasa.gov
- Replace YOUR_API_KEY in the script with your actual key.

## ⚙️ Usage
Run the Script
To fetch and store data:
- python neo_tracking_mysql_ui_adjusted.py
To launch the Streamlit dashboard:
- streamlit run neo_tracking_mysql_ui_adjusted.py

### Interact with the Dashboard
- Open your browser and go to: http://localhost:8501
- Use the left sidebar to:
  - Switch between "Filter Criteria" and "Queries"
  - Apply filters or select queries to visualize asteroid data in tables

## Project Structure
- neo_tracking_mysql_ui_adjusted.py: Main Python script for:
  - Data extraction
  - MySQL database creation/insertion
  - Streamlit-based UI for interaction

## Configuration
- Edit MYSQL_CONFIG in the script with your MySQL credentials
- Replace YOUR_API_KEY with your NASA API key

## Sample Outputs
- Filtered Asteroids: Displays asteroids matching selected filters
- Query Results: Shows insights such as:
  - Top 10 fastest asteroids
  - Count of hazardous asteroids
  - And 13 more queries
