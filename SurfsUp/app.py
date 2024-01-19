# Import the dependencies.
import numpy as np
import flask 
print(flask.__version__)
import sqlalchemy
print(sqlalchemy.__version__)
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from datetime import datetime as dt, timedelta

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///hawaii.sqlite", echo=True)

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################

# Create an app instance
app = Flask(__name__)

# Define the home route
@app.route('/')
def home():
    return (
        f"Welcome to the Climate App!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end"
    )

#################################################
# Flask Routes
#################################################

# Define the precipitation route
@app.route('/api/v1.0/precipitation')
def precipitation():
    date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]
    date = dt.strptime(date, "%Y-%m-%d")
    year_to_date = date - timedelta(days=365)

    prcp_results = session.query(measurement.date, measurement.prcp).\
        filter(measurement.date >= year_to_date).all()

    # Convert results to a dictionary
    precipitation_data = []
    for date, prcp in prcp_results:
        prcp_dict = {"date": date,
                     "precipitation": prcp}
        precipitation_data.append(prcp_dict)

    return jsonify(precipitation_data)

# Define the stations route
@app.route('/api/v1.0/stations')
def stations():
    stations_results = session.query(station.name).all()

    # Convert results to a dictionary
    stations_data = []
    for result in stations_results:
        station_name = result[0]
        stations_dict = {"station name": station_name}
        stations_data.append(stations_dict)

    return jsonify(stations_data)

# Define the tobs route
@app.route('/api/v1.0/tobs')
def tobs():
    date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]
    date = dt.strptime(date, "%Y-%m-%d")
    year_to_date = date - timedelta(days=365)

    # Get the most active station and its count
    most_active_station = session.query(measurement.station, func.count(measurement.station).label('station_count')).\
        group_by(measurement.station).\
        order_by(func.count(measurement.station).desc()).first()
    # If statement code from chatGPT
    if most_active_station:
        most_active_station_id = most_active_station[0]

        # Query tobs data for the most active station
        tobs_results = session.query(measurement.date, measurement.tobs).\
            filter(measurement.station == most_active_station_id).\
            filter(measurement.date >= year_to_date).all()
        
        # Convert results to a dictionary
        tobs_data = []
        for result in tobs_results:
            most_active_tobs = result[1]
            most_active_tobs_dict = {"TOBS at Most Active Station": most_active_tobs}
            tobs_data.append(most_active_tobs_dict)

        return jsonify(tobs_data)

# Define the start route
@app.route('/api/v1.0/<start>')
def start(start):
    start_results = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start).all()
    
    # Convert results to a dictionary
    start_data = []
    for result in start_results:
        start_min = result[0]
        start_avg = result[1]
        start_max = result[2]
        start_dict = {"TMIN": start_min,
                      "TAVG": start_avg,
                      "TMAX": start_max}
        start_data.append(start_dict)

    return jsonify(start_data)

# Define the start and end route
@app.route('/api/v1.0/<start>/<end>')
def start_end(start, end):
    # dt.strptime suggested by chatGPT
    start_date = dt.strptime(start, "%Y-%m-%d")
    end_date = dt.strptime(end, "%Y-%m-%d")

# Query all data between start_date and end_date
    date_range_results = session.query(measurement.date, measurement.tobs).\
        filter(measurement.date >= start_date).\
        filter(measurement.date <= end_date).all()

    # Calculate min, avg, and max values (provided by chatGPT)
    min_temp = min(date_range_results, key=lambda x: x[1])[1]
    avg_temp = sum([x[1] for x in date_range_results]) / len(date_range_results)
    max_temp = max(date_range_results, key=lambda x: x[1])[1]

    start_end_dict = {
        "TMIN": min_temp,
        "TAVG": avg_temp,
        "TMAX": max_temp
    }

    return jsonify(start_end_dict)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)