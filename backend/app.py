"""
BloomWatch Backend API
NASA Space Apps Challenge 2025
Main Flask application for serving bloom detection and visualization data
"""

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta

# Import custom modules
from data_fetcher import SatelliteDataFetcher
from bloom_detector import BloomDetector
from vegetation_indices import VegetationIndexCalculator

# Load environment variables
load_dotenv()

# Get the project root directory (parent of backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

# Initialize Flask app
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)  # Enable CORS for frontend access

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
data_fetcher = SatelliteDataFetcher()
bloom_detector = BloomDetector()
vi_calculator = VegetationIndexCalculator()


@app.route('/')
def home():
    """Serve the main frontend page"""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/api')
def api_info():
    """API information endpoint"""
    return jsonify({
        'name': 'BloomWatch API',
        'version': '1.0.0',
        'description': 'NASA Earth observation bloom monitoring tool',
        'endpoints': {
            '/api/bloom/detect': 'Detect blooms in a region',
            '/api/bloom/timeseries': 'Get bloom time series data',
            '/api/ndvi/calculate': 'Calculate NDVI for a region',
            '/api/data/available': 'Check available satellite data',
            '/api/regions/suggest': 'Get suggested bloom regions'
        }
    })


@app.route('/api/bloom/detect', methods=['POST'])
def detect_bloom():
    """
    Detect bloom events in a specified region and time period
    
    Request body:
    {
        "lat": 36.778,
        "lon": -119.418,
        "start_date": "2024-03-01",
        "end_date": "2024-05-31",
        "buffer_km": 10,
        "satellite": "landsat"  // or "modis", "sentinel"
    }
    """
    try:
        data = request.get_json()
        
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        buffer_km = float(data.get('buffer_km', 10))
        satellite = data.get('satellite', 'landsat')
        
        logger.info(f"Bloom detection requested for ({lat}, {lon}) from {start_date} to {end_date}")
        
        # Optimize satellite selection
        if satellite == 'auto' or satellite == 'combined':
            logger.info("Using OPTIMAL combination: Landsat + Sentinel-2")
            satellite = 'combined'
        
        # Fetch satellite data
        satellite_data = data_fetcher.fetch_data(
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
            buffer_km=buffer_km,
            satellite=satellite,
            combine_sources=(satellite == 'combined')
        )
        
        if not satellite_data:
            return jsonify({
                'error': 'No satellite data available for specified parameters',
                'status': 'no_data'
            }), 404
        
        logger.info(f"📊 SATELLITE DATA RECEIVED:")
        logger.info(f"   - Satellite: {satellite_data.get('satellite', 'Unknown')}")
        logger.info(f"   - Has ndvi_data: {'ndvi_data' in satellite_data}")
        if 'ndvi_data' in satellite_data:
            logger.info(f"   - NDVI dates: {satellite_data['ndvi_data'].get('dates', [])}")
            logger.info(f"   - NDVI values: {satellite_data['ndvi_data'].get('values', [])}")
        
        # Calculate vegetation indices
        ndvi_data = vi_calculator.calculate_ndvi(satellite_data)
        evi_data = vi_calculator.calculate_evi(satellite_data)
        
        # Extract dates if available
        dates = None
        if 'ndvi_data' in satellite_data and satellite_data['ndvi_data']:
            dates = satellite_data['ndvi_data'].get('dates', None)
        
        logger.info(f"📈 VEGETATION INDICES CALCULATED:")
        logger.info(f"   - NDVI array shape: {ndvi_data.shape}")
        logger.info(f"   - NDVI values: {ndvi_data}")
        logger.info(f"   - EVI array shape: {evi_data.shape}")
        logger.info(f"   - Dates for time series: {dates}")
        
        # Detect bloom events
        bloom_events = bloom_detector.detect_blooms(
            ndvi_data=ndvi_data,
            evi_data=evi_data,
            threshold=float(os.getenv('NDVI_BLOOM_THRESHOLD', 0.4)),
            dates=dates
        )
        
        logger.info(f"🌸 BLOOM EVENTS DETECTED: {len(bloom_events)}")
        for i, event in enumerate(bloom_events):
            logger.info(f"   Event #{i+1}: {event}")
        
        response = {
            'status': 'success',
            'location': {'lat': lat, 'lon': lon},
            'date_range': {'start': start_date, 'end': end_date},
            'bloom_events': bloom_events,
            'statistics': {
                'total_events': len(bloom_events),
                'peak_bloom_date': bloom_detector.get_peak_bloom_date(bloom_events),
                'average_ndvi': float(ndvi_data.mean()) if len(ndvi_data) > 0 else 0,
                'bloom_intensity': bloom_detector.calculate_bloom_intensity(bloom_events)
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in bloom detection: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500


@app.route('/api/bloom/timeseries', methods=['POST'])
def get_bloom_timeseries():
    """
    Get time series data for bloom tracking over multiple years
    
    Request body:
    {
        "lat": 36.778,
        "lon": -119.418,
        "years": [2020, 2021, 2022, 2023, 2024],
        "season": "spring"  // or "summer", "fall", "winter", "all"
    }
    """
    try:
        data = request.get_json()
        
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
        years = data.get('years', [2024])
        season = data.get('season', 'spring')
        
        logger.info(f"Time series requested for ({lat}, {lon}), years: {years}")
        
        timeseries_data = []
        
        for year in years:
            # Define season dates
            season_dates = {
                'spring': (f"{year}-03-01", f"{year}-05-31"),
                'summer': (f"{year}-06-01", f"{year}-08-31"),
                'fall': (f"{year}-09-01", f"{year}-11-30"),
                'winter': (f"{year}-12-01", f"{year+1}-02-28"),
                'all': (f"{year}-01-01", f"{year}-12-31")
            }
            
            start_date, end_date = season_dates.get(season, season_dates['spring'])
            
            # Fetch and process data for this year
            satellite_data = data_fetcher.fetch_data(
                lat=lat,
                lon=lon,
                start_date=start_date,
                end_date=end_date,
                buffer_km=5,
                satellite='landsat'
            )
            
            if satellite_data:
                ndvi_data = vi_calculator.calculate_ndvi(satellite_data)
                bloom_events = bloom_detector.detect_blooms(ndvi_data)
                
                timeseries_data.append({
                    'year': year,
                    'season': season,
                    'bloom_events': bloom_events,
                    'peak_ndvi': float(ndvi_data.max()) if len(ndvi_data) > 0 else 0,
                    'average_ndvi': float(ndvi_data.mean()) if len(ndvi_data) > 0 else 0
                })
        
        return jsonify({
            'status': 'success',
            'location': {'lat': lat, 'lon': lon},
            'timeseries': timeseries_data,
            'trends': bloom_detector.analyze_trends(timeseries_data)
        })
        
    except Exception as e:
        logger.error(f"Error in timeseries analysis: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500


@app.route('/api/ndvi/calculate', methods=['POST'])
def calculate_ndvi():
    """Calculate NDVI for a specific date and location"""
    try:
        data = request.get_json()
        
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
        date = data.get('date')
        
        satellite_data = data_fetcher.fetch_single_scene(
            lat=lat,
            lon=lon,
            date=date
        )
        
        if not satellite_data:
            return jsonify({
                'error': 'No data available for specified date',
                'status': 'no_data'
            }), 404
        
        ndvi = vi_calculator.calculate_ndvi(satellite_data)
        evi = vi_calculator.calculate_evi(satellite_data)
        
        return jsonify({
            'status': 'success',
            'location': {'lat': lat, 'lon': lon},
            'date': date,
            'ndvi': float(ndvi.mean()),
            'evi': float(evi.mean()),
            'statistics': {
                'ndvi_min': float(ndvi.min()),
                'ndvi_max': float(ndvi.max()),
                'ndvi_std': float(ndvi.std())
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating NDVI: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500


@app.route('/api/regions/suggest', methods=['GET'])
def suggest_regions():
    """Get suggested regions known for bloom events"""
    
    suggested_regions = [
        {
            'name': 'Antelope Valley California Poppy Reserve',
            'lat': 34.745,
            'lon': -118.376,
            'country': 'USA',
            'state': 'California',
            'description': 'Famous for spring superbloom events with California poppies',
            'best_season': 'Spring (March-May)',
            'bloom_type': 'Wildflower superbloom'
        },
        {
            'name': 'Carrizo Plain National Monument',
            'lat': 35.193,
            'lon': -119.867,
            'country': 'USA',
            'state': 'California',
            'description': 'Spectacular wildflower displays in wet years',
            'best_season': 'Spring (March-May)',
            'bloom_type': 'Desert wildflowers'
        },
        {
            'name': 'Death Valley National Park',
            'lat': 36.505,
            'lon': -117.079,
            'country': 'USA',
            'state': 'California',
            'description': 'Rare desert superbloom phenomenon',
            'best_season': 'Spring (February-April)',
            'bloom_type': 'Desert wildflowers'
        },
        {
            'name': 'Cherry Blossom - Washington DC',
            'lat': 38.889,
            'lon': -77.050,
            'country': 'USA',
            'state': 'DC',
            'description': 'Iconic cherry blossom bloom around Tidal Basin',
            'best_season': 'Spring (late March-early April)',
            'bloom_type': 'Tree blossoms'
        },
        {
            'name': 'Namaqualand',
            'lat': -30.221,
            'lon': 17.902,
            'country': 'South Africa',
            'state': 'Northern Cape',
            'description': 'World-famous spring flower displays',
            'best_season': 'Spring (August-September)',
            'bloom_type': 'Wildflower carpet'
        },
        {
            'name': 'Great Plains - Kansas',
            'lat': 38.500,
            'lon': -96.800,
            'country': 'USA',
            'state': 'Kansas',
            'description': 'Tallgrass prairie blooms',
            'best_season': 'Summer (June-August)',
            'bloom_type': 'Prairie flowers'
        },
        {
            'name': 'Atacama Desert',
            'lat': -24.500,
            'lon': -69.250,
            'country': 'Chile',
            'state': 'Antofagasta',
            'description': 'Rare flowering desert (Desierto Florido)',
            'best_season': 'Spring (September-November)',
            'bloom_type': 'Desert bloom'
        }
    ]
    
    return jsonify({
        'status': 'success',
        'regions': suggested_regions,
        'count': len(suggested_regions)
    })


@app.route('/api/data/available', methods=['POST'])
def check_data_availability():
    """Check what satellite data is available for a location and time range"""
    try:
        data = request.get_json()
        
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        availability = data_fetcher.check_availability(
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            'status': 'success',
            'availability': availability
        })
        
    except Exception as e:
        logger.error(f"Error checking data availability: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting BloomWatch API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
