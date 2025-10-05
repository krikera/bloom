# Bloom

Bloom is an open-source transparency tool for monitoring desert wildflower bloom conditions with NASA Earth observation data. It retrieves Landsat 8/9 and Sentinel-2 surface reflectance scenes from the Microsoft Planetary Computer, extracts vegetation indices, and reports whether results come from real pixels or simulated fallback data so field teams can interpret alerts with appropriate caution.

## Features

- **Satellite ingestion** using the STAC API to locate Landsat 8/9 Collection 2 Level-2 and Sentinel-2 Level-2A scenes within a configurable buffer around a point of interest.
- **Vegetation analytics** including NDVI and EVI calculations, bloom event detection, trend scoring, and ecological context summaries.
- **Regional scanning** that sweeps a larger bounding box for hotspots and tallies how many points relied on verified pixels versus demo data.
- **Data provenance reporting** surfaced across API responses and the web UI so users always know the origin and reliability of each result.

## Architecture

```
frontend (vanilla JS)  <-- Flask static serving -->  backend/app.py
                                               |--> SatelliteDataFetcher
                                               |--> BloomDetector, BloomPredictor
                                               |--> VegetationIndexCalculator
                                               |--> SpeciesIdentifier
                                               |--> RegionalScanner
```

- The Flask backend (`backend/app.py`) serves API endpoints and the static frontend (`frontend/`).
- `backend/data_fetcher.py` interacts with the Microsoft Planetary Computer and applies NDVI/EVI calculations with Rasterio, NumPy, and SciPy.
- `backend/bloom_detector.py`, `backend/bloom_predictor.py`, and `backend/species_identifier.py` derive bloom events, forecast signals, and species context.
- `frontend/index.html` and `frontend/app.js` provide a map-driven interface that calls the API and displays provenance status banners.

## Prerequisites

- Python 3.11 or later
- `pip` for dependency management
- Optional (recommended) access to the Microsoft Planetary Computer (MPC) account for higher request limits
- Optional NASA Earthdata credentials (only required if you extend the fetcher to use services beyond MPC)

## Setup

```bash
# Clone the repository
git clone https://github.com/krikera/bloom.git
cd bloom

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file in the project root if you need to override defaults:

```
EARTHDATA_USERNAME=your_username      # optional; not required for MPC data
EARTHDATA_PASSWORD=your_password      # optional
CACHE_DIR=./data/cache                # location for cached STAC responses
```

The fetcher defaults to demo mode when real imagery cannot be retrieved. Provenance summaries in API responses explain whether results relied on real pixels.

## Running the application

```bash
# From the project root with the virtual environment active
cd backend
python app.py
```

This starts the Flask server on `http://127.0.0.1:5000/` and serves both the API and the frontend UI. Satellite requests may take several seconds while scenes download and process.

## Running tests

```bash
# With the virtual environment active
python -m pytest tests
```

The test suite exercises vegetation index calculations, bloom detection logic, provenance helpers, and basic fetcher initialization.

## Data sources

| Dataset | Description | Link |
|---------|-------------|------|
| Landsat Collection 2 Level-2 Surface Reflectance | Landsat 8/9 optical measurements used for NDVI/EVI | https://planetarycomputer.microsoft.com/dataset/landsat-c2-l2 |
| Sentinel-2 Level-2A | Harmonized Sentinel-2 imagery providing higher temporal resolution | https://planetarycomputer.microsoft.com/dataset/sentinel-2-l2a |
| Microsoft Planetary Computer | Hosting platform that signs data URLs and provides STAC search | https://planetarycomputer.microsoft.com/ |

## Known limitations

- Real imagery processing requires Rasterio and access to MPC signed URLs. When those dependencies fail, the system falls back to curated demo NDVI values and labels the output accordingly.
- Cloud cover and water masking are basic; dense clouds can still reduce valid pixel counts.
- Notebook-based analyses in `notebooks/` are optional and not part of the production API pipeline.

## Contributing

Pull requests are welcome. Please include tests for new backend logic and keep documentation consistent with the current behaviour, especially around data provenance and fallback modes.
