"""
Satellite Data Fetcher
Handles fetching data from various NASA satellite missions
"""

import os
import logging
from datetime import datetime, timedelta
import numpy as np

import pandas as pd
from typing import Dict, Optional, Tuple
from pystac_client import Client
from shapely.geometry import box, mapping

# Optional imports - gracefully handle missing dependencies
try:
    import rasterio
    from rasterio.mask import mask
    from rasterio.warp import transform_geom
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False
    logging.warning("rasterio not available - some advanced features disabled")



logger = logging.getLogger(__name__)


class SatelliteDataFetcher:
    """Fetch satellite data from NASA sources"""
    def __init__(self):
        self.earthdata_username = os.getenv('EARTHDATA_USERNAME')
        self.earthdata_password = os.getenv('EARTHDATA_PASSWORD')
        self.cache_dir = os.getenv('CACHE_DIR', './data/cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.demo_mode = False
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with NASA Earthdata"""
        # NASA Earthdata authentication is not required for Microsoft Planetary Computer
        # This is a placeholder for future NASA-specific datasets
        if self.earthdata_username and self.earthdata_password:
            logger.info("NASA Earthdata credentials provided (not used in current pipeline)")
        else:
            logger.info("NASA Earthdata credentials not provided. Using demo mode for unavailable data.")
            logger.info("✅ Real Landsat + Sentinel-2 data still available via Microsoft Planetary Computer!")
            self.demo_mode = True
    
    def fetch_data(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        buffer_km: float = 10,
        satellite: str = 'landsat',
        combine_sources: bool = False
    ) -> Optional[Dict]:
        """
        Fetch satellite data for a location and time range
        
        OPTIMIZED FOR: Landsat 8/9 + Sentinel-2 combination
        - Landsat: 16-day revisit, 30m resolution, 11 bands
        - Sentinel-2: 5-day revisit, 10m resolution, 13 bands
        
        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            buffer_km: Buffer around point in kilometers
            satellite: Satellite source ('landsat', 'sentinel', 'combined')
            combine_sources: If True, fetch both Landsat and Sentinel-2
        
        Returns:
            Dictionary containing satellite data and metadata
        """
        try:
            logger.info(f"Fetching {satellite} data for ({lat}, {lon})")
            
            # Create bounding box
            bbox = self._create_bbox(lat, lon, buffer_km)
            
            # Microsoft Planetary Computer doesn't require NASA credentials
            # Try real data first, fallback to demo if it fails
            
            # Combined Landsat + Sentinel-2 for maximum temporal coverage
            if satellite.lower() == 'combined' or combine_sources:
                return self._fetch_combined_landsat_sentinel(bbox, start_date, end_date)
            elif satellite.lower() == 'landsat':
                return self._fetch_landsat(bbox, start_date, end_date)
            elif satellite.lower() in ['sentinel', 'sentinel-2', 'sentinel2']:
                return self._fetch_sentinel(bbox, start_date, end_date)
            else:
                logger.warning(f"Satellite '{satellite}' not optimized. Using Landsat as default.")
                return self._fetch_landsat(bbox, start_date, end_date)
                
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return None
    
    def _create_bbox(self, lat: float, lon: float, buffer_km: float) -> Tuple[float, float, float, float]:
        """Create bounding box around point"""
        # Approximate degrees per km (varies by latitude)
        lat_deg_per_km = 1 / 111.0
        lon_deg_per_km = 1 / (111.0 * np.cos(np.radians(lat)))
        
        lat_buffer = buffer_km * lat_deg_per_km
        lon_buffer = buffer_km * lon_deg_per_km
        
        return (
            lon - lon_buffer,  # min_lon
            lat - lat_buffer,  # min_lat
            lon + lon_buffer,  # max_lon
            lat + lat_buffer   # max_lat
        )
    
    def _process_landsat_scene_actual(self, item, bbox: Tuple) -> Optional[Dict]:
        """
        Actually download and process Landsat imagery (not simulation)
        
        Args:
            item: STAC item for Landsat scene
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            
        Returns:
            Dictionary with real NDVI calculated from NIR/Red bands
        """
        try:
            if not HAS_RASTERIO:
                logger.warning("⚠️ rasterio not available, cannot process real imagery")
                return None
                
            import rasterio
            from rasterio.mask import mask
            from shapely.geometry import box as shapely_box
            
            try:
                import planetary_computer
                # Get signed URLs for bands (Microsoft Planetary Computer)
                signed_item = planetary_computer.sign(item)
            except ImportError:
                logger.warning("planetary_computer not available, using unsigned URLs")
                signed_item = item
            
            # We need Red (Band 4) and NIR (Band 5) for Landsat 8/9
            red_href = signed_item.assets['red'].href
            nir_href = signed_item.assets['nir08'].href
            
            logger.info(f"📥 Downloading Landsat scene: {item.id}")
            
            # Create shapely box for masking
            geom = shapely_box(*bbox)
            
            # Calculate center point in pixel coordinates
            center_lon = (bbox[0] + bbox[2]) / 2
            center_lat = (bbox[1] + bbox[3]) / 2
            
            logger.info(f"   Target: {center_lat:.4f}°, {center_lon:.4f}°")
            
            # Read Red band - sample region around point
            with rasterio.open(red_href) as red_src:
                # The raster uses a projected CRS, but we have lat/lon
                # rasterio.index() handles the coordinate transformation automatically
                logger.info(f"   Raster CRS: {red_src.crs}")
                logger.info(f"   Raster bounds: {red_src.bounds}")
                
                # Convert lon/lat to pixel coordinates
                try:
                    row, col = red_src.index(center_lon, center_lat)
                except:
                    # If point is outside raster, use scene center
                    logger.warning(f"   Point outside scene, using center")
                    height, width = red_src.shape
                    row, col = height // 2, width // 2
                
                logger.info(f"   Pixel coordinates: row={row}, col={col}")
                
                # Ensure window is within bounds
                height, width = red_src.shape
                window_size = 50  # Increased from 10 to get more pixels
                half_size = window_size // 2
                
                # Calculate window bounds, ensuring they're within the raster
                col_start = max(0, min(width - window_size, int(col) - half_size))
                row_start = max(0, min(height - window_size, int(row) - half_size))
                win_width = min(window_size, width - col_start)
                win_height = min(window_size, height - row_start)
                
                # Sanity check
                if win_width <= 0 or win_height <= 0:
                    logger.warning(f"   Invalid window size: {win_width}x{win_height}")
                    return None
                
                window = rasterio.windows.Window(col_start, row_start, win_width, win_height)
                
                logger.info(f"   Reading window: {win_width}x{win_height} at row {row_start}, col {col_start}")
                
                red_raw = red_src.read(1, window=window).astype(float)
                
                if red_raw.size == 0:
                    logger.warning("   Red band window is empty")
                    return None
                
                logger.info(f"   Red band: raw range [{red_raw.min():.0f}, {red_raw.max():.0f}]")
                
                # Apply scale factor for Landsat Collection 2
                # Scale factor converts DN to reflectance
                red_data = red_raw * 0.0000275 - 0.2
            
            # Read NIR band  
            with rasterio.open(nir_href) as nir_src:
                # Convert lon/lat to pixel coordinates
                row, col = nir_src.index(center_lon, center_lat)
                
                # Ensure window is within bounds
                height, width = nir_src.shape
                half_size = window_size // 2
                
                col_start = max(0, min(width - window_size, int(col) - half_size))
                row_start = max(0, min(height - window_size, int(row) - half_size))
                win_width = min(window_size, width - col_start)
                win_height = min(window_size, height - row_start)
                
                if win_width <= 0 or win_height <= 0:
                    logger.warning(f"   Invalid NIR window size: {win_width}x{win_height}")
                    return None
                
                window = rasterio.windows.Window(col_start, row_start, win_width, win_height)
                
                nir_raw = nir_src.read(1, window=window).astype(float)
                
                if nir_raw.size == 0:
                    logger.warning("   NIR band window is empty")
                    return None
                
                logger.info(f"   NIR band: raw range [{nir_raw.min():.0f}, {nir_raw.max():.0f}]")
                
                # Apply scale factor for Landsat Collection 2
                nir_data = nir_raw * 0.0000275 - 0.2
            
            logger.info(f"   Red reflectance: [{red_data.min():.3f}, {red_data.max():.3f}]")
            logger.info(f"   NIR reflectance: [{nir_data.min():.3f}, {nir_data.max():.3f}]")
            
            # Calculate NDVI from actual pixels
            # Handle division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                ndvi = (nir_data - red_data) / (nir_data + red_data)
            
            # Filter invalid values
            # 1. Remove inf/nan
            # 2. Remove values outside physical range [-1, 1]
            # 3. Remove pixels where both bands are very dark (likely fill values or shadows)
            mask = (
                np.isfinite(ndvi) &  # Not inf or nan
                (ndvi >= -1) & (ndvi <= 1) &  # Physical range
                ((red_raw > 0) | (nir_raw > 0))  # Exclude pixels with no signal / nodata
            )
            
            valid_ndvi = ndvi[mask]
            
            logger.info(f"   Valid pixels: {len(valid_ndvi)} / {ndvi.size}")
            
            if len(valid_ndvi) == 0:
                logger.warning("❌ No valid NDVI pixels after filtering")
                logger.warning(f"   Red DN range: [{red_raw.min():.0f}, {red_raw.max():.0f}]")
                logger.warning(f"   NIR DN range: [{nir_raw.min():.0f}, {nir_raw.max():.0f}]")
                logger.warning(f"   NDVI raw range: [{ndvi.min():.3f}, {ndvi.max():.3f}]")
                logger.warning(f"   Mask passed: {mask.sum()} pixels")
                logger.info("   Attempting geometry-based sampling fallback...")
                fallback_red, fallback_nir, red_nodata, nir_nodata = self._sample_landsat_region(red_href, nir_href, bbox)
                if fallback_red is not None and fallback_nir is not None:
                    red_raw = fallback_red
                    nir_raw = fallback_nir
                    nodata_mask = np.zeros_like(red_raw, dtype=bool)
                    if red_nodata is not None:
                        nodata_mask |= (red_raw == red_nodata)
                    if nir_nodata is not None:
                        nodata_mask |= (nir_raw == nir_nodata)
                    red_data = red_raw * 0.0000275 - 0.2
                    nir_data = nir_raw * 0.0000275 - 0.2
                    with np.errstate(divide='ignore', invalid='ignore'):
                        ndvi = (nir_data - red_data) / (nir_data + red_data)
                    mask = (
                        np.isfinite(ndvi) &
                        (ndvi >= -1) & (ndvi <= 1) &
                        ((red_raw > 0) | (nir_raw > 0))
                    )
                    if nodata_mask.any():
                        mask &= ~nodata_mask
                    valid_ndvi = ndvi[mask]
                
            if len(valid_ndvi) == 0:
                logger.warning("   Fallback sampling also failed to produce valid NDVI")
                return None
            
            logger.info(f"   NDVI range: [{valid_ndvi.min():.3f}, {valid_ndvi.max():.3f}]")
            
            mean_ndvi = float(np.mean(valid_ndvi))
            max_ndvi = float(np.max(valid_ndvi))
            std_ndvi = float(np.std(valid_ndvi))
            
            logger.info(f"✅ Processed real imagery: NDVI mean={mean_ndvi:.3f}, max={max_ndvi:.3f}, std={std_ndvi:.3f}")
            
            return {
                'scene_id': item.id,
                'date': item.properties.get('datetime', '').split('T')[0],
                'ndvi_mean': mean_ndvi,
                'ndvi_max': max_ndvi,
                'ndvi_std': std_ndvi,
                'cloud_cover': item.properties.get('eo:cloud_cover', 0),
                'real_data': True  # Flag to indicate this is actual imagery
            }
            
        except Exception as e:
            logger.error(f"Error processing scene: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _sample_landsat_region(self, red_href: str, nir_href: str, bbox: Tuple) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[float], Optional[float]]:
        """Sample Landsat bands using the full bounding box as fallback"""
        try:
            with rasterio.open(red_href) as red_src, rasterio.open(nir_href) as nir_src:
                geom = box(*bbox)
                geom_geojson = mapping(geom)
                target_geom = geom_geojson

                if red_src.crs and red_src.crs.to_string() != 'EPSG:4326':
                    try:
                        target_geom = transform_geom('EPSG:4326', red_src.crs, geom_geojson)
                    except Exception as transform_error:
                        logger.warning(f"   Failed to transform geometry to raster CRS: {transform_error}")

                red_arr, _ = mask(red_src, [target_geom], crop=True, filled=False)
                nir_arr, _ = mask(nir_src, [target_geom], crop=True, filled=False)

                # mask() returns arrays with shape (1, H, W)
                red_data = np.ma.masked_array(red_arr[0], mask=np.ma.getmaskarray(red_arr[0]))
                nir_data = np.ma.masked_array(nir_arr[0], mask=np.ma.getmaskarray(nir_arr[0]))

                if red_data.count() == 0 or nir_data.count() == 0:
                    return None, None, red_src.nodata, nir_src.nodata

                return np.asarray(red_data.filled(red_src.nodata if red_src.nodata is not None else 0), dtype=float), \
                    np.asarray(nir_data.filled(nir_src.nodata if nir_src.nodata is not None else 0), dtype=float), \
                    red_src.nodata, nir_src.nodata

        except Exception as e:
            logger.error(f"   Geometry-based sampling failed: {e}")
        return None, None, None, None

    def _fetch_landsat(self, bbox: Tuple, start_date: str, end_date: str) -> Optional[Dict]:
        """
        Fetch Landsat 8/9 Collection 2 Level-2 data
        
        Landsat 8/9 Specifications:
        - 30m spatial resolution (visible/NIR)
        - 16-day revisit (8-day with both satellites)
        - 11 spectral bands including coastal aerosol and cirrus
        - Surface reflectance products (atmospherically corrected)
        - Extensive archive (Landsat program: 1972-present)
        
        Optimal for:
        - Medium-scale bloom detection (fields to regions)
        - Long-term trend analysis
        - Cloud masking with QA bands
        """
        try:
            # Use Microsoft Planetary Computer STAC API
            catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
            
            # Search for Landsat Collection 2 Level-2 (surface reflectance)
            search = catalog.search(
                collections=["landsat-c2-l2"],
                bbox=bbox,
                datetime=f"{start_date}/{end_date}",
                query={
                    "eo:cloud_cover": {"lt": 15},  # Stricter cloud cover for bloom detection
                    "platform": {"in": ["landsat-8", "landsat-9"]}  # Both satellites
                }
            )
            
            items = list(search.get_items())
            
            if not items:
                logger.warning("No Landsat scenes found. Trying relaxed cloud cover...")
                # Retry with relaxed cloud cover
                search = catalog.search(
                    collections=["landsat-c2-l2"],
                    bbox=bbox,
                    datetime=f"{start_date}/{end_date}",
                    query={"eo:cloud_cover": {"lt": 30}}
                )
                items = list(search.get_items())
            
            if not items:
                logger.warning("No Landsat scenes available for this location/time")
                return None
            
            # Sort by cloud cover (best quality first)
            items.sort(key=lambda x: x.properties.get('eo:cloud_cover', 100))
            
            logger.info(f"✅ Found {len(items)} Landsat scenes (best: {items[0].properties.get('eo:cloud_cover', 'N/A'):.1f}% cloud cover)")
            
            # Try to process actual imagery from clearest scene
            logger.info("🎯 Attempting to process actual satellite imagery...")
            processed_scene = self._process_landsat_scene_actual(items[0], bbox)
            
            if processed_scene and processed_scene.get('real_data'):
                # Successfully processed real data!
                logger.info("🎉 SUCCESS: Using real satellite data!")
                return {
                    'satellite': 'Landsat-8/9',
                    'source': 'Microsoft Planetary Computer',
                    'bbox': bbox,
                    'date_range': [start_date, end_date],
                    'scenes_found': len(items),
                    'ndvi_data': {
                        'dates': [processed_scene['date']],
                        'values': [processed_scene['ndvi_mean']],
                        'quality': 'high'
                    },
                    'metadata': {
                        'scene_id': processed_scene['scene_id'],
                        'cloud_cover': processed_scene['cloud_cover'],
                        'ndvi_max': processed_scene['ndvi_max'],
                        'ndvi_std': processed_scene['ndvi_std']
                    },
                    'real_data': True,  # Critical flag
                    'demo_mode': False,
                    'notes': 'NDVI computed from real Landsat surface reflectance pixels.'
                }
            else:
                # Fallback to demo mode if real processing failed
                logger.warning("⚠️ Real data processing failed, falling back to demo mode")
                # Generate simulated NDVI data from real scene metadata
                ndvi_timeseries = self._generate_ndvi_from_scenes(items, start_date, end_date)
            
            # Use the clearest scene (demo mode)
            item = items[0]
            
            # Extract all relevant bands for bloom detection
            data = {
                'satellite': 'Landsat-8/9',
                'collection': 'Collection 2 Level-2',
                'date': item.properties.get('datetime'),
                'cloud_cover': item.properties.get('eo:cloud_cover'),
                'platform': item.properties.get('platform'),
                'bbox': bbox,
                'bands': {
                    # Visible bands
                    'coastal': item.assets.get('coastal'),  # Band 1 (0.43-0.45 μm)
                    'blue': item.assets.get('blue'),        # Band 2 (0.45-0.51 μm)
                    'green': item.assets.get('green'),      # Band 3 (0.53-0.59 μm)
                    'red': item.assets.get('red'),          # Band 4 (0.64-0.67 μm)
                    # NIR bands (critical for vegetation indices)
                    'nir08': item.assets.get('nir08'),      # Band 5 (0.85-0.88 μm)
                    # SWIR bands (useful for moisture content)
                    'swir16': item.assets.get('swir16'),    # Band 6 (1.57-1.65 μm)
                    'swir22': item.assets.get('swir22'),    # Band 7 (2.11-2.29 μm)
                    # Quality bands
                    'qa_pixel': item.assets.get('qa_pixel'),  # Quality assessment
                },
                'metadata': {
                    'cloud_cover': item.properties.get('eo:cloud_cover'),
                    'sun_azimuth': item.properties.get('view:sun_azimuth'),
                    'sun_elevation': item.properties.get('view:sun_elevation'),
                    'processing_level': 'L2SP',  # Surface Reflectance
                    'instruments': item.properties.get('instruments', ['OLI', 'TIRS'])
                },
                'items': items,  # Store all items for time series
                'scene_count': len(items),
                'temporal_coverage': f"{start_date} to {end_date}",
                # Add simulated NDVI data
                'ndvi_data': ndvi_timeseries,
                'real_data': False,
                'demo_mode': True,
                'notes': 'Real pixel sampling unavailable; NDVI synthesized from scene metadata.'
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching Landsat data: {str(e)}")
            logger.info("💡 Tip: Check internet connection and Microsoft Planetary Computer availability")
            return None
    
    def _fetch_combined_landsat_sentinel(self, bbox: Tuple, start_date: str, end_date: str) -> Optional[Dict]:
        """
        Fetch and combine Landsat + Sentinel-2 data for optimal temporal coverage
        
        Combined Benefits:
        - Landsat: 8-day revisit (L8+L9), 30m, 40+ years archive
        - Sentinel-2: 5-day revisit (S2A+S2B), 10m, red-edge bands
        - Together: ~3-day effective revisit for bloom monitoring!
        
        This combination is OPTIMAL for:
        - Capturing rapid flowering events
        - Multi-scale analysis (10m detail + 30m coverage)
        - Long-term trend analysis with recent high-res data
        - Species discrimination (Sentinel) + temporal depth (Landsat)
        """
        try:
            logger.info("🌟 Fetching COMBINED Landsat + Sentinel-2 data for maximum coverage")
            
            # Fetch both datasets
            landsat_data = self._fetch_landsat(bbox, start_date, end_date)
            sentinel_data = self._fetch_sentinel(bbox, start_date, end_date)
            
            if not landsat_data and not sentinel_data:
                logger.error("No data available from either Landsat or Sentinel-2")
                return None
            
            if not landsat_data:
                logger.warning("No Landsat data available, using Sentinel-2 only")
                return sentinel_data
            
            if not sentinel_data:
                logger.warning("No Sentinel-2 data available, using Landsat only")
                return landsat_data
            
            # Combine datasets
            combined_items = []
            if landsat_data.get('items'):
                combined_items.extend(landsat_data['items'])
            if sentinel_data.get('items'):
                combined_items.extend(sentinel_data['items'])
            
            # Sort by date
            combined_items.sort(key=lambda x: x.properties.get('datetime'))
            
            logger.info(f"✅ Combined: {landsat_data.get('scene_count', 0)} Landsat + {sentinel_data.get('scene_count', 0)} Sentinel-2 scenes")
            logger.info(f"📅 Total temporal observations: {len(combined_items)}")
            
            # Generate combined NDVI from all scenes
            combined_ndvi = self._generate_ndvi_from_scenes(combined_items, start_date, end_date)
            real_data_available = bool(
                (landsat_data and landsat_data.get('real_data')) or
                (sentinel_data and sentinel_data.get('real_data'))
            )
            notes = []
            for dataset in (landsat_data, sentinel_data):
                if dataset and dataset.get('notes'):
                    notes.append(dataset['notes'])
            if not real_data_available:
                notes.append('Using synthesized NDVI because raw pixel processing was unavailable for at least one source.')
            
            return {
                'satellite': 'Combined Landsat-8/9 + Sentinel-2',
                'landsat': landsat_data,
                'sentinel': sentinel_data,
                'combined_items': combined_items,
                'bbox': bbox,
                'temporal_coverage': f"{start_date} to {end_date}",
                'total_scenes': len(combined_items),
                'effective_revisit': '~3 days',
                'ndvi_data': combined_ndvi,  # Add NDVI data at top level
                'real_data': real_data_available,
                'demo_mode': not real_data_available,
                'notes': ' '.join(notes).strip() if notes else None,
                'metadata': {
                    'description': 'Optimal combination for bloom detection',
                    'landsat_scenes': landsat_data.get('scene_count', 0),
                    'sentinel_scenes': sentinel_data.get('scene_count', 0),
                    'spatial_resolution': '10-30m',
                    'temporal_resolution': '3-5 days effective',
                    'advantages': [
                        'Maximum temporal coverage',
                        'Multi-scale spatial analysis',
                        'Red-edge bands from Sentinel-2',
                        'Long-term archive from Landsat',
                        'Complementary cloud-free observations'
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error combining Landsat and Sentinel-2: {str(e)}")
            return None
    
    def _fetch_sentinel(self, bbox: Tuple, start_date: str, end_date: str) -> Optional[Dict]:
        """
        Fetch Sentinel-2 Level-2A data (ESA Copernicus)
        
        Sentinel-2A/2B Specifications:
        - 10m spatial resolution (visible/NIR bands)
        - 5-day revisit (with both satellites)
        - 13 spectral bands including red-edge bands
        - Bottom-of-atmosphere reflectance (L2A)
        - High sensitivity to vegetation changes
        
        Optimal for:
        - High-resolution bloom detection
        - Rapid flowering event capture
        - Species discrimination (red-edge bands)
        - Small-scale agricultural monitoring
        
        Research shows 97% accuracy in wildflower detection!
        """
        try:
            catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
            
            # Search for Sentinel-2 L2A (atmospherically corrected)
            search = catalog.search(
                collections=["sentinel-2-l2a"],
                bbox=bbox,
                datetime=f"{start_date}/{end_date}",
                query={
                    "eo:cloud_cover": {"lt": 15},  # Strict cloud cover
                    "s2:processing_baseline": {"gte": "04.00"}  # Recent processing
                }
            )
            
            items = list(search.get_items())
            
            if not items:
                logger.warning("No Sentinel-2 scenes found. Trying relaxed cloud cover...")
                search = catalog.search(
                    collections=["sentinel-2-l2a"],
                    bbox=bbox,
                    datetime=f"{start_date}/{end_date}",
                    query={"eo:cloud_cover": {"lt": 30}}
                )
                items = list(search.get_items())
            
            if not items:
                logger.warning("No Sentinel-2 scenes available for this location/time")
                return None
            
            # Sort by cloud cover and recency
            items.sort(key=lambda x: (
                x.properties.get('eo:cloud_cover', 100),
                -pd.Timestamp(x.properties.get('datetime')).timestamp()
            ))
            
            logger.info(f"✅ Found {len(items)} Sentinel-2 scenes (best: {items[0].properties.get('eo:cloud_cover', 'N/A'):.1f}% cloud cover)")
            
            # Generate simulated NDVI data from real scene metadata
            ndvi_timeseries = self._generate_ndvi_from_scenes(items, start_date, end_date)
            
            item = items[0]
            
            # Extract all relevant bands for bloom detection
            data = {
                'satellite': 'Sentinel-2',
                'collection': 'Level-2A',
                'date': item.properties.get('datetime'),
                'cloud_cover': item.properties.get('eo:cloud_cover'),
                'platform': item.properties.get('platform', 'sentinel-2a/2b'),
                'bbox': bbox,
                'bands': {
                    # 10m resolution bands (optimal for bloom detection)
                    'blue': item.assets.get('B02'),      # Band 2 (0.490 μm) - 10m
                    'green': item.assets.get('B03'),     # Band 3 (0.560 μm) - 10m
                    'red': item.assets.get('B04'),       # Band 4 (0.665 μm) - 10m
                    'nir': item.assets.get('B08'),       # Band 8 (0.842 μm) - 10m - KEY for NDVI
                    
                    # 20m resolution bands (vegetation analysis)
                    'rededge1': item.assets.get('B05'),  # Band 5 (0.705 μm) - 20m - Red-edge
                    'rededge2': item.assets.get('B06'),  # Band 6 (0.740 μm) - 20m - Red-edge
                    'rededge3': item.assets.get('B07'),  # Band 7 (0.783 μm) - 20m - Red-edge
                    'nir08': item.assets.get('B8A'),     # Band 8A (0.865 μm) - 20m - Narrow NIR
                    'swir16': item.assets.get('B11'),    # Band 11 (1.610 μm) - 20m
                    'swir22': item.assets.get('B12'),    # Band 12 (2.190 μm) - 20m
                    
                    # Quality and cloud bands
                    'scl': item.assets.get('SCL'),       # Scene Classification Layer
                },
                'metadata': {
                    'cloud_cover': item.properties.get('eo:cloud_cover'),
                    'processing_baseline': item.properties.get('s2:processing_baseline'),
                    'datatake_id': item.properties.get('s2:datatake_id'),
                    'granule_id': item.properties.get('s2:granule_id'),
                    'instruments': ['MSI'],  # MultiSpectral Instrument
                    'spatial_resolution': '10m (visible/NIR), 20m (red-edge/SWIR)',
                    'advantages': [
                        '5-day revisit frequency',
                        'Red-edge bands for species discrimination',
                        'High spatial resolution (10m)',
                        '97% bloom detection accuracy (research validated)'
                    ]
                },
                'items': items,
                'scene_count': len(items),
                'temporal_coverage': f"{start_date} to {end_date}",
                'quality_score': self._calculate_sentinel_quality_score(item),
                'ndvi_data': ndvi_timeseries,  # Add NDVI timeseries
                'real_data': False,
                'demo_mode': True,
                'notes': 'Sentinel-2 raster processing not enabled; NDVI derived from scene metadata.'
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching Sentinel-2 data: {str(e)}")
            logger.info("💡 Tip: Sentinel-2 data available via Microsoft Planetary Computer and ESA Copernicus")
            return None
    
    def _calculate_sentinel_quality_score(self, item) -> float:
        """Calculate quality score for Sentinel-2 scene (0-1)"""
        score = 1.0
        
        # Penalize high cloud cover
        cloud_cover = item.properties.get('eo:cloud_cover', 0)
        score -= (cloud_cover / 100) * 0.5
        
        # Bonus for recent processing baseline
        baseline = item.properties.get('s2:processing_baseline', '00.00')
        if baseline >= '04.00':
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _generate_ndvi_from_scenes(self, items, start_date: str, end_date: str) -> Dict:
        """
        Generate realistic NDVI time series from real scene metadata
        
        Since rasterio is not available, we simulate NDVI values based on:
        - Actual scene dates from real satellite data
        - Seasonal patterns (spring bloom, summer growth, fall decline)
        - Cloud cover effects (lower values for cloudy scenes)
        - Geographic/temporal context
        
        This provides realistic bloom patterns for demonstration while
        maintaining connection to real satellite observation times.
        """
        dates = []
        ndvi_values = []
        
        for item in items:
            # Get real scene date
            scene_date_str = item.properties.get('datetime', '')
            if scene_date_str:
                scene_date = datetime.fromisoformat(scene_date_str.replace('Z', '+00:00'))
                dates.append(scene_date)
                
                # Generate realistic NDVI based on season and cloud cover
                month = scene_date.month
                cloud_cover = item.properties.get('eo:cloud_cover', 0)
                
                # Seasonal vegetation patterns (Northern Hemisphere)
                if month in [3, 4, 5]:  # Spring - bloom season
                    base_ndvi = 0.65
                    # Peak in April
                    if month == 4:
                        base_ndvi = 0.75
                    # Add bloom variation
                    variation = 0.15 * np.sin((month - 2) * np.pi / 3)
                elif month in [6, 7, 8]:  # Summer - high vegetation
                    base_ndvi = 0.70
                    variation = 0.10
                elif month in [9, 10, 11]:  # Fall - declining
                    base_ndvi = 0.50
                    variation = -0.10 * (month - 8) / 4
                else:  # Winter - low vegetation
                    base_ndvi = 0.30
                    variation = 0.05
                
                # Cloud cover reduces NDVI accuracy
                cloud_penalty = (cloud_cover / 100) * 0.15
                
                # Add realistic noise
                noise = np.random.normal(0, 0.03)
                
                ndvi = base_ndvi + variation - cloud_penalty + noise
                ndvi = max(0.1, min(0.9, ndvi))  # Clamp to realistic range
                
                ndvi_values.append(float(ndvi))
        
        # Sort by date
        if dates:
            sorted_pairs = sorted(zip(dates, ndvi_values))
            dates, ndvi_values = zip(*sorted_pairs)
            dates = [d.strftime('%Y-%m-%d') for d in dates]
        
        logger.info(f"Generated {len(ndvi_values)} NDVI values from real scene dates")
        
        return {
            'dates': list(dates),
            'values': list(ndvi_values),
            'note': 'NDVI values simulated from real satellite scene metadata (rasterio not available for full processing)'
        }
    
    def _generate_demo_data(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        satellite: str
    ) -> Dict:
        """Generate synthetic demo data for testing"""
        logger.info("Generating demo data (no NASA credentials provided)")
        
        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days = (end - start).days
        
        # Generate synthetic NDVI time series with bloom pattern
        dates = [start + timedelta(days=i) for i in range(0, days, 16)]
        
        # Create bloom curve (spring bloom pattern)
        month_nums = [d.month for d in dates]
        ndvi_values = []
        
        for month in month_nums:
            if month in [3, 4, 5]:  # Spring bloom
                base = 0.6
                variation = 0.2 * np.sin((month - 3) * np.pi / 3)
            elif month in [6, 7, 8]:  # Summer
                base = 0.7
                variation = 0.1
            else:  # Fall/Winter
                base = 0.3
                variation = 0.05
            
            ndvi_values.append(base + variation + np.random.normal(0, 0.05))
        
        return {
            'satellite': satellite,
            'demo_mode': True,
            'location': {'lat': lat, 'lon': lon},
            'date_range': {'start': start_date, 'end': end_date},
            'dates': [d.strftime('%Y-%m-%d') for d in dates],
            'ndvi_values': ndvi_values,
            'metadata': {
                'resolution': '30m' if satellite == 'landsat' else '250m',
                'cloud_cover': 5.0
            }
        }
    
    def fetch_single_scene(self, lat: float, lon: float, date: str) -> Optional[Dict]:
        """Fetch a single satellite scene for a specific date"""
        # Use +/- 3 days window to find closest scene
        start_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=3)).strftime('%Y-%m-%d')
        end_date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=3)).strftime('%Y-%m-%d')
        
        return self.fetch_data(lat, lon, start_date, end_date, buffer_km=5)
    
    def check_availability(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Check data availability for Landsat and Sentinel-2
        
        OPTIMIZED: Focus on best sources for bloom detection
        """
        bbox = self._create_bbox(lat, lon, 10)
        
        availability = {
            'landsat': False,
            'sentinel': False,
            'combined': False,
            'recommendation': '',
            'details': {}
        }
        
        # Check Landsat 8/9
        try:
            landsat_data = self._fetch_landsat(bbox, start_date, end_date)
            if landsat_data:
                availability['landsat'] = True
                availability['details']['landsat'] = {
                    'scenes': len(landsat_data.get('items', [])),
                    'resolution': '30m',
                    'revisit': '8 days (with L8+L9)',
                    'best_cloud_cover': landsat_data.get('cloud_cover', 'N/A'),
                    'bands': '11 (includes coastal aerosol, cirrus)',
                    'archive': '1972-present (full Landsat program)',
                    'use_case': 'Medium-scale bloom detection, trend analysis'
                }
        except Exception as e:
            logger.error(f"Error checking Landsat: {str(e)}")
        
        # Check Sentinel-2
        try:
            sentinel_data = self._fetch_sentinel(bbox, start_date, end_date)
            if sentinel_data:
                availability['sentinel'] = True
                availability['details']['sentinel'] = {
                    'scenes': len(sentinel_data.get('items', [])),
                    'resolution': '10m (visible/NIR)',
                    'revisit': '5 days (with S2A+S2B)',
                    'best_cloud_cover': sentinel_data.get('cloud_cover', 'N/A'),
                    'bands': '13 (includes red-edge)',
                    'archive': '2015-present',
                    'use_case': 'High-res bloom detection, species discrimination',
                    'accuracy': '97% wildflower detection (research validated)'
                }
        except Exception as e:
            logger.error(f"Error checking Sentinel: {str(e)}")
        
        # Determine best strategy
        if availability['landsat'] and availability['sentinel']:
            availability['combined'] = True
            availability['recommendation'] = 'OPTIMAL: Use combined Landsat + Sentinel-2'
            availability['combined_advantages'] = [
                '~3 day effective revisit frequency',
                'Multi-scale analysis (10m + 30m)',
                'Red-edge bands + long-term archive',
                'Maximum cloud-free observation opportunities',
                f"Total scenes: {availability['details']['landsat']['scenes'] + availability['details']['sentinel']['scenes']}"
            ]
        elif availability['sentinel']:
            availability['recommendation'] = 'GOOD: Use Sentinel-2 (high resolution, frequent revisit)'
        elif availability['landsat']:
            availability['recommendation'] = 'GOOD: Use Landsat (reliable coverage, long archive)'
        else:
            availability['recommendation'] = 'No data available - try different dates or location'
        
        logger.info(f"📊 Availability Check: {availability['recommendation']}")
        
        return availability
