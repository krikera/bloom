"""
Vegetation Index Calculator
Calculate NDVI, EVI, and other vegetation indices from satellite data
"""

import numpy as np
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class VegetationIndexCalculator:
    """Calculate vegetation indices from satellite imagery"""
    
    def __init__(self):
        """Initialize calculator"""
        pass
    
    def calculate_ndvi(self, satellite_data: Dict) -> np.ndarray:
        """
        Calculate Normalized Difference Vegetation Index
        
        NDVI = (NIR - Red) / (NIR + Red)
        
        Values range from -1 to 1:
        - < 0: Water, snow, clouds
        - 0 - 0.2: Bare soil, rock
        - 0.2 - 0.4: Sparse vegetation
        - 0.4 - 0.6: Moderate vegetation
        - > 0.6: Dense vegetation
        
        Args:
            satellite_data: Dictionary containing satellite band data
        
        Returns:
            NDVI array or time series
        """
        try:
            # Check if demo mode
            if satellite_data.get('demo_mode'):
                return np.array(satellite_data.get('ndvi_values', []))
            
            # Check if NDVI data already calculated (from scene metadata)
            if 'ndvi_data' in satellite_data and satellite_data['ndvi_data']:
                ndvi_dict = satellite_data['ndvi_data']
                values = ndvi_dict.get('values', [])
                if values:
                    logger.info(f"Using pre-calculated NDVI data: {len(values)} values")
                    return np.array(values)
            
            # Extract bands
            red = self._extract_band_data(satellite_data, 'red')
            nir = self._extract_band_data(satellite_data, 'nir')
            
            if red is None or nir is None:
                logger.warning("Missing required bands for NDVI calculation")
                return np.array([])
            
            # Calculate NDVI with safe division
            with np.errstate(divide='ignore', invalid='ignore'):
                ndvi = (nir - red) / (nir + red)
                # Replace inf and nan with 0
                ndvi = np.nan_to_num(ndvi, nan=0.0, posinf=0.0, neginf=0.0)
                # Clip to valid range
                ndvi = np.clip(ndvi, -1, 1)
            
            logger.info(f"NDVI calculated: mean={ndvi.mean():.3f}, max={ndvi.max():.3f}")
            
            return ndvi
            
        except Exception as e:
            logger.error(f"Error calculating NDVI: {str(e)}")
            return np.array([])
    
    def calculate_evi(self, satellite_data: Dict) -> np.ndarray:
        """
        Calculate Enhanced Vegetation Index
        
        EVI = 2.5 × ((NIR - Red) / (NIR + 6 × Red - 7.5 × Blue + 1))
        
        EVI is more sensitive to canopy structure and reduces atmospheric effects
        
        Args:
            satellite_data: Dictionary containing satellite band data
        
        Returns:
            EVI array or time series
        """
        try:
            # Check if demo mode
            if satellite_data.get('demo_mode'):
                # Generate EVI from NDVI (approximate)
                ndvi = np.array(satellite_data.get('ndvi_values', []))
                return ndvi * 1.1  # EVI is typically slightly higher
            
            # Check if NDVI data already calculated - derive EVI from it
            if 'ndvi_data' in satellite_data and satellite_data['ndvi_data']:
                ndvi_dict = satellite_data['ndvi_data']
                values = ndvi_dict.get('values', [])
                if values:
                    # Approximate EVI from NDVI (EVI is typically slightly higher and more sensitive)
                    evi = np.array(values) * 1.15
                    logger.info(f"Using derived EVI from NDVI data: {len(evi)} values")
                    return evi
            
            # Extract bands
            red = self._extract_band_data(satellite_data, 'red')
            nir = self._extract_band_data(satellite_data, 'nir')
            blue = self._extract_band_data(satellite_data, 'blue')
            
            if red is None or nir is None or blue is None:
                logger.warning("Missing required bands for EVI calculation")
                return np.array([])
            
            # Calculate EVI with coefficients
            G = 2.5  # Gain factor
            C1 = 6   # Coefficient for aerosol resistance term (red)
            C2 = 7.5 # Coefficient for aerosol resistance term (blue)
            L = 1    # Canopy background adjustment
            
            with np.errstate(divide='ignore', invalid='ignore'):
                evi = G * ((nir - red) / (nir + C1 * red - C2 * blue + L))
                # Replace inf and nan with 0
                evi = np.nan_to_num(evi, nan=0.0, posinf=0.0, neginf=0.0)
                # Clip to valid range (-1 to 1)
                evi = np.clip(evi, -1, 1)
            
            logger.info(f"EVI calculated: mean={evi.mean():.3f}, max={evi.max():.3f}")
            
            return evi
            
        except Exception as e:
            logger.error(f"Error calculating EVI: {str(e)}")
            return np.array([])
    
    def calculate_savi(
        self,
        satellite_data: Dict,
        soil_brightness_factor: float = 0.5
    ) -> np.ndarray:
        """
        Calculate Soil-Adjusted Vegetation Index
        
        SAVI = ((NIR - Red) / (NIR + Red + L)) × (1 + L)
        
        Where L is the soil brightness correction factor (0.5 is typical)
        
        Useful in areas with exposed soil
        """
        try:
            red = self._extract_band_data(satellite_data, 'red')
            nir = self._extract_band_data(satellite_data, 'nir')
            
            if red is None or nir is None:
                return np.array([])
            
            L = soil_brightness_factor
            
            with np.errstate(divide='ignore', invalid='ignore'):
                savi = ((nir - red) / (nir + red + L)) * (1 + L)
                savi = np.nan_to_num(savi, nan=0.0, posinf=0.0, neginf=0.0)
                savi = np.clip(savi, -1, 1)
            
            return savi
            
        except Exception as e:
            logger.error(f"Error calculating SAVI: {str(e)}")
            return np.array([])
    
    def calculate_gndvi(self, satellite_data: Dict) -> np.ndarray:
        """
        Calculate Green Normalized Difference Vegetation Index
        
        GNDVI = (NIR - Green) / (NIR + Green)
        
        More sensitive to chlorophyll than NDVI
        """
        try:
            green = self._extract_band_data(satellite_data, 'green')
            nir = self._extract_band_data(satellite_data, 'nir')
            
            if green is None or nir is None:
                return np.array([])
            
            with np.errstate(divide='ignore', invalid='ignore'):
                gndvi = (nir - green) / (nir + green)
                gndvi = np.nan_to_num(gndvi, nan=0.0, posinf=0.0, neginf=0.0)
                gndvi = np.clip(gndvi, -1, 1)
            
            return gndvi
            
        except Exception as e:
            logger.error(f"Error calculating GNDVI: {str(e)}")
            return np.array([])
    
    def _extract_band_data(self, satellite_data: Dict, band: str) -> Optional[np.ndarray]:
        """
        Extract band data from satellite data dictionary
        
        Args:
            satellite_data: Dictionary containing band information
            band: Band name ('red', 'nir', 'blue', 'green')
        
        Returns:
            Band data as numpy array or None
        """
        try:
            bands = satellite_data.get('bands', {})
            band_asset = bands.get(band)
            
            if band_asset is None:
                return None
            
            # For demo mode, generate synthetic band data
            if satellite_data.get('demo_mode'):
                # Generate realistic-ish band values
                if band == 'red':
                    return np.random.uniform(0.05, 0.15, (100, 100))
                elif band in ['nir', 'nir08']:
                    return np.random.uniform(0.3, 0.8, (100, 100))
                elif band == 'blue':
                    return np.random.uniform(0.03, 0.10, (100, 100))
                elif band == 'green':
                    return np.random.uniform(0.04, 0.12, (100, 100))
            
            # For real data, this would load the actual raster
            # Implementation depends on data format (COG, HDF, NetCDF)
            # Placeholder for actual implementation
            logger.info(f"Would load {band} band data from: {band_asset}")
            
            # Return dummy data for now
            return np.random.uniform(0.1, 0.8, (100, 100))
            
        except Exception as e:
            logger.error(f"Error extracting band data: {str(e)}")
            return None
    
    def classify_vegetation(self, ndvi: np.ndarray) -> Dict[str, float]:
        """
        Classify vegetation based on NDVI values
        
        Returns:
            Dictionary with percentage of each class
        """
        try:
            total_pixels = ndvi.size
            
            if total_pixels == 0:
                return {}
            
            classification = {
                'water': (ndvi < 0).sum() / total_pixels * 100,
                'bare_soil': ((ndvi >= 0) & (ndvi < 0.2)).sum() / total_pixels * 100,
                'sparse_vegetation': ((ndvi >= 0.2) & (ndvi < 0.4)).sum() / total_pixels * 100,
                'moderate_vegetation': ((ndvi >= 0.4) & (ndvi < 0.6)).sum() / total_pixels * 100,
                'dense_vegetation': (ndvi >= 0.6).sum() / total_pixels * 100
            }
            
            return classification
            
        except Exception as e:
            logger.error(f"Error classifying vegetation: {str(e)}")
            return {}
    
    def detect_bloom_spectral_signature(
        self,
        satellite_data: Dict
    ) -> Tuple[bool, float]:
        """
        Detect bloom based on spectral signatures
        
        Flowering plants often show:
        - High NIR reflectance (healthy vegetation)
        - Increased visible light reflectance (flower colors)
        - Specific spectral patterns in RGB
        
        Returns:
            (is_blooming, confidence)
        """
        try:
            ndvi = self.calculate_ndvi(satellite_data)
            
            if len(ndvi) == 0:
                return False, 0.0
            
            # Calculate statistics
            mean_ndvi = ndvi.mean()
            max_ndvi = ndvi.max()
            std_ndvi = ndvi.std()
            
            # Bloom indicators:
            # 1. High NDVI (healthy vegetation)
            # 2. High variance (mix of flowers and greenery)
            # 3. Rapid increase over time (if time series available)
            
            confidence = 0.0
            
            if mean_ndvi > 0.5:
                confidence += 0.4
            elif mean_ndvi > 0.4:
                confidence += 0.2
            
            if std_ndvi > 0.15:  # High variation suggests flowers
                confidence += 0.3
            
            if max_ndvi > 0.7:  # Peak vegetation health
                confidence += 0.3
            
            is_blooming = confidence > 0.5
            
            return is_blooming, confidence
            
        except Exception as e:
            logger.error(f"Error detecting bloom signature: {str(e)}")
            return False, 0.0
