# 🌸 BloomWatch - Global Vegetation Bloom Monitoring Tool

## NASA Space Apps Challenge 2025 - Track the Bloom!

### Overview
BloomWatch is an interactive visualization tool that harnesses NASA Earth observation data to monitor, predict, and visualize plant blooming events across the globe. The tool combines satellite imagery from multiple NASA missions (Landsat, MODIS, VIIRS) with advanced vegetation indices to track bloom dynamics from deserts to agricultural lands.

### 🎯 Key Features

1. **Interactive Global Bloom Map**
   - Real-time visualization of vegetation changes
   - Multi-scale analysis (global to local)
   - Time-series comparison across seasons and years

2. **Bloom Detection Algorithm**
   - NDVI (Normalized Difference Vegetation Index) analysis
   - EVI (Enhanced Vegetation Index) tracking
   - Spectral signature analysis for species identification

3. **Temporal Tracking**
   - Historical trend analysis using Landsat archive (40+ years)
   - Season-by-season bloom progression
   - Anomaly detection for superblooms

4. **Practical Applications**
   - Agricultural crop monitoring
   - Pollen forecasting for public health
   - Invasive species detection
   - Conservation planning support

### 🛰️ Data Sources

- **Landsat 8/9**: 30m resolution, 16-day revisit
- **MODIS (Terra/Aqua)**: 250m-1km resolution, daily coverage
- **VIIRS**: 375m-750m resolution, daily coverage
- **Sentinel-2**: 10m resolution (via Copernicus)
- **GLOBE Observer**: Ground truth validation data

### 🏗️ Architecture

```
BloomWatch/
├── backend/          # Python API for data processing
├── frontend/         # Interactive web interface
├── data/            # Satellite data processing
├── models/          # ML models for prediction
├── notebooks/       # Analysis and visualization notebooks
└── docs/            # Documentation
```

### 🚀 Quick Start

1. **Setup Python Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/Mac
   pip install -r requirements.txt
   ```

2. **Configure NASA Earthdata Credentials**
   - Register at: https://urs.earthdata.nasa.gov/
   - Add credentials to `.env` file

3. **Run the Application**
   ```bash
   # Start backend API
   cd backend
   python app.py
   
   # Start frontend (in another terminal)
   cd frontend
   npm install
   npm start
   ```

4. **Access the Tool**
   - Open browser: http://localhost:3000

### 📊 Use Cases

#### 1. California Superbloom Monitoring
- Track spring wildflower blooms in deserts
- Compare bloom intensity across years
- Predict optimal viewing times for tourism

#### 2. Agricultural Crop Management
- Monitor flowering stages in cotton, canola, sunflowers
- Optimize harvest timing
- Detect crop stress early

#### 3. Pollen Forecasting
- Track tree bloom progression (oak, birch, grass)
- Generate regional pollen alerts
- Support allergy management

#### 4. Ecosystem Health Assessment
- Monitor phenological shifts due to climate change
- Track invasive species spread
- Support conservation decisions

### 🔬 Technical Approach

**Vegetation Index Calculation:**
- NDVI = (NIR - Red) / (NIR + Red)
- EVI = 2.5 × ((NIR - Red) / (NIR + 6 × Red - 7.5 × Blue + 1))

**Bloom Detection:**
1. Calculate baseline NDVI from historical data
2. Detect rapid increases (>0.2 NDVI change in 2 weeks)
3. Identify peak bloom (maximum NDVI)
4. Track bloom duration and spatial extent

**Predictive Modeling:**
- Random Forest for bloom timing prediction
- Climate variables (temperature, precipitation, soil moisture)
- Historical phenology patterns

### 📈 Future Enhancements

- [ ] Integration with EMIT hyperspectral data for species ID
- [ ] Mobile app with AR visualization
- [ ] API for third-party integrations
- [ ] Real-time alerts and notifications
- [ ] Citizen science data integration (GLOBE Observer)

### 🌍 Impact

BloomWatch enables:
- **Scientists**: Study climate impacts on plant phenology
- **Farmers**: Optimize planting and harvesting decisions
- **Public Health Officials**: Forecast pollen seasons
- **Conservationists**: Monitor ecosystem changes
- **Citizens**: Connect with nature's rhythms

### 📝 License

MIT License - Open source for environmental good!

### 🤝 Contributors

Built with passion for NASA Space Apps Challenge 2025

### 📚 References

- NASA Earthdata: https://earthdata.nasa.gov/
- Landsat Science: https://landsat.gsfc.nasa.gov/
- MODIS Vegetation Indices: https://modis.gsfc.nasa.gov/data/dataprod/mod13.php
- GLOBE Observer: https://observer.globe.gov/
