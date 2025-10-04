"""
Bloom Detector
Detect and analyze plant blooming events from time series vegetation data
"""

import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from scipy import signal
from scipy.stats import linregress

logger = logging.getLogger(__name__)


class BloomDetector:
    """Detect blooming events from vegetation index time series"""
    
    def __init__(
        self,
        bloom_threshold: float = 0.4,
        change_threshold: float = 0.2,
        min_duration_days: int = 14
    ):
        """
        Initialize bloom detector
        
        Args:
            bloom_threshold: Minimum NDVI value to consider blooming
            change_threshold: Minimum NDVI increase to detect bloom start
            min_duration_days: Minimum bloom duration in days
        """
        self.bloom_threshold = bloom_threshold
        self.change_threshold = change_threshold
        self.min_duration_days = min_duration_days
    
    def detect_blooms(
        self,
        ndvi_data: np.ndarray,
        evi_data: Optional[np.ndarray] = None,
        threshold: Optional[float] = None,
        dates: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Detect bloom events from NDVI time series
        
        Args:
            ndvi_data: NDVI values (time series or single value)
            evi_data: Optional EVI values for additional validation
            threshold: Custom bloom threshold (overrides default)
            dates: Optional list of date strings corresponding to NDVI values
        
        Returns:
            List of detected bloom events with metadata
        """
        try:
            logger.info(f"🔍 BLOOM DETECTION INPUT:")
            logger.info(f"   - NDVI data shape: {np.array(ndvi_data).shape}")
            logger.info(f"   - NDVI values: {ndvi_data}")
            logger.info(f"   - Dates provided: {dates}")
            logger.info(f"   - Threshold: {threshold if threshold else self.bloom_threshold}")
            
            if len(ndvi_data) == 0:
                return []
            
            threshold = threshold if threshold is not None else self.bloom_threshold
            
            # Convert to array if not already
            ndvi_array = np.array(ndvi_data)
            
            # If single value, check if it exceeds threshold
            if ndvi_array.ndim == 0 or len(ndvi_array) == 1:
                value = float(ndvi_array)
                if value >= threshold:
                    return [{
                        'type': 'single_observation',
                        'ndvi': value,
                        'is_blooming': True,
                        'confidence': self._calculate_confidence(value)
                    }]
                return []
            
            # Time series analysis
            bloom_events = []
            
            # Detect peaks in NDVI
            peaks, properties = signal.find_peaks(
                ndvi_array,
                height=threshold,
                distance=2,  # Minimum 2 observations between peaks
                prominence=0.1
            )
            
            if len(peaks) == 0:
                # Check if sustained high NDVI (continuous bloom)
                high_ndvi_mask = ndvi_array >= threshold
                if np.sum(high_ndvi_mask) >= 2:
                    bloom_events.append({
                        'type': 'sustained_bloom',
                        'peak_ndvi': float(ndvi_array.max()),
                        'mean_ndvi': float(ndvi_array[high_ndvi_mask].mean()),
                        'duration_observations': int(np.sum(high_ndvi_mask)),
                        'confidence': 0.7
                    })
                return bloom_events
            
            # Analyze each peak
            for i, peak_idx in enumerate(peaks):
                peak_value = ndvi_array[peak_idx]
                
                # Find bloom start (where NDVI increases rapidly)
                start_idx = self._find_bloom_start(ndvi_array, peak_idx)
                
                # Find bloom end (where NDVI decreases)
                end_idx = self._find_bloom_end(ndvi_array, peak_idx)
                
                # Calculate bloom characteristics
                duration = end_idx - start_idx + 1
                increase_rate = (ndvi_array[peak_idx] - ndvi_array[start_idx]) / max(peak_idx - start_idx, 1)
                
                bloom_event = {
                    'type': 'peak_bloom',
                    'peak_index': int(peak_idx),
                    'start_index': int(start_idx),
                    'end_index': int(end_idx),
                    'peak_ndvi': float(peak_value),
                    'start_ndvi': float(ndvi_array[start_idx]),
                    'end_ndvi': float(ndvi_array[end_idx]),
                    'duration_observations': int(duration),
                    'increase_rate': float(increase_rate),
                    'confidence': self._calculate_confidence(peak_value),
                    'intensity': self._calculate_intensity(
                        ndvi_array[start_idx:end_idx+1]
                    )
                }
                
                # Add dates if available
                if dates and len(dates) > max(peak_idx, end_idx, start_idx):
                    bloom_event['start_date'] = dates[start_idx]
                    bloom_event['peak_date'] = dates[peak_idx]
                    bloom_event['end_date'] = dates[end_idx]
                    logger.info(f"📅 Bloom Event #{i+1}: {dates[start_idx]} to {dates[end_idx]}, peak on {dates[peak_idx]} (NDVI: {peak_value:.3f})")
                
                # Add EVI data if available
                if evi_data is not None and len(evi_data) > peak_idx:
                    bloom_event['peak_evi'] = float(evi_data[peak_idx])
                
                bloom_events.append(bloom_event)
            
            logger.info(f"Detected {len(bloom_events)} bloom events")
            return bloom_events
            
        except Exception as e:
            logger.error(f"Error detecting blooms: {str(e)}")
            return []
    
    def _find_bloom_start(self, ndvi_array: np.ndarray, peak_idx: int) -> int:
        """Find the start of bloom (where NDVI begins rapid increase)"""
        if peak_idx == 0:
            return 0
        
        # Look backwards for significant increase
        for i in range(peak_idx - 1, -1, -1):
            if i == 0:
                return 0
            
            # Check if this is where rapid increase begins
            change = ndvi_array[i + 1] - ndvi_array[i]
            if change < 0.05:  # Slow change, likely pre-bloom
                return i + 1
        
        return 0
    
    def _find_bloom_end(self, ndvi_array: np.ndarray, peak_idx: int) -> int:
        """Find the end of bloom (where NDVI decreases significantly)"""
        if peak_idx >= len(ndvi_array) - 1:
            return len(ndvi_array) - 1
        
        # Look forward for significant decrease
        for i in range(peak_idx + 1, len(ndvi_array)):
            if i == len(ndvi_array) - 1:
                return i
            
            # Check if NDVI is decreasing
            change = ndvi_array[i] - ndvi_array[i - 1]
            if change < -0.05:  # Significant decrease
                # Continue to find bottom
                continue
            elif ndvi_array[i] < self.bloom_threshold:
                return i
        
        return len(ndvi_array) - 1
    
    def _calculate_confidence(self, ndvi_value: float) -> float:
        """Calculate confidence that this is a bloom event"""
        if ndvi_value < self.bloom_threshold:
            return 0.0
        elif ndvi_value < 0.5:
            return 0.5
        elif ndvi_value < 0.6:
            return 0.7
        elif ndvi_value < 0.7:
            return 0.85
        else:
            return 0.95
    
    def _calculate_intensity(self, ndvi_segment: np.ndarray) -> str:
        """Calculate bloom intensity classification"""
        mean_ndvi = ndvi_segment.mean()
        
        if mean_ndvi < 0.4:
            return 'low'
        elif mean_ndvi < 0.6:
            return 'moderate'
        elif mean_ndvi < 0.75:
            return 'high'
        else:
            return 'very_high'
    
    def get_peak_bloom_date(self, bloom_events: List[Dict]) -> Optional[str]:
        """Get the date of peak bloom from events"""
        if not bloom_events:
            return None
        
        # Find event with highest NDVI
        peak_event = max(bloom_events, key=lambda x: x.get('peak_ndvi', 0))
        
        # Would normally convert index to actual date
        # For now, return index
        return f"Observation {peak_event.get('peak_index', 'N/A')}"
    
    def calculate_bloom_intensity(self, bloom_events: List[Dict]) -> float:
        """Calculate overall bloom intensity score (0-1)"""
        if not bloom_events:
            return 0.0
        
        # Average the peak NDVI values
        peak_ndvis = [event.get('peak_ndvi', 0) for event in bloom_events]
        
        if not peak_ndvis:
            return 0.0
        
        # Normalize to 0-1 scale (0.4 = 0, 1.0 = 1)
        avg_ndvi = np.mean(peak_ndvis)
        intensity = (avg_ndvi - 0.4) / 0.6
        
        return float(np.clip(intensity, 0, 1))
    
    def analyze_trends(self, timeseries_data: List[Dict]) -> Dict:
        """
        Analyze trends in blooming across multiple years
        
        Args:
            timeseries_data: List of yearly bloom data
        
        Returns:
            Dictionary with trend analysis
        """
        try:
            if not timeseries_data:
                return {'status': 'no_data'}
            
            years = [data['year'] for data in timeseries_data]
            peak_ndvis = [data.get('peak_ndvi', 0) for data in timeseries_data]
            avg_ndvis = [data.get('average_ndvi', 0) for data in timeseries_data]
            
            # Calculate trends
            trends = {}
            
            if len(years) >= 2:
                # Peak NDVI trend
                slope_peak, intercept_peak, r_value_peak, _, _ = linregress(years, peak_ndvis)
                trends['peak_ndvi_trend'] = {
                    'slope': float(slope_peak),
                    'direction': 'increasing' if slope_peak > 0 else 'decreasing',
                    'r_squared': float(r_value_peak ** 2),
                    'interpretation': self._interpret_trend(slope_peak, r_value_peak ** 2)
                }
                
                # Average NDVI trend
                slope_avg, intercept_avg, r_value_avg, _, _ = linregress(years, avg_ndvis)
                trends['average_ndvi_trend'] = {
                    'slope': float(slope_avg),
                    'direction': 'increasing' if slope_avg > 0 else 'decreasing',
                    'r_squared': float(r_value_avg ** 2)
                }
                
                # Bloom event frequency
                event_counts = [len(data.get('bloom_events', [])) for data in timeseries_data]
                if event_counts:
                    trends['bloom_frequency'] = {
                        'average': float(np.mean(event_counts)),
                        'min': int(np.min(event_counts)),
                        'max': int(np.max(event_counts))
                    }
            
            # Year-over-year changes
            if len(timeseries_data) >= 2:
                changes = []
                for i in range(1, len(peak_ndvis)):
                    change = ((peak_ndvis[i] - peak_ndvis[i-1]) / peak_ndvis[i-1]) * 100
                    changes.append({
                        'from_year': years[i-1],
                        'to_year': years[i],
                        'percent_change': float(change)
                    })
                trends['year_over_year_changes'] = changes
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _interpret_trend(self, slope: float, r_squared: float) -> str:
        """Interpret the trend based on slope and R²"""
        if r_squared < 0.3:
            return "No clear trend (low correlation)"
        
        if abs(slope) < 0.01:
            return "Stable bloom intensity"
        elif slope > 0:
            if slope > 0.05:
                return "Strong increase in bloom intensity - may indicate favorable conditions"
            else:
                return "Moderate increase in bloom intensity"
        else:
            if slope < -0.05:
                return "Strong decrease in bloom intensity - may indicate stress or climate change"
            else:
                return "Moderate decrease in bloom intensity"
    
    def predict_next_bloom(
        self,
        historical_data: List[Dict],
        current_date: str
    ) -> Dict:
        """
        Predict the next bloom event based on historical patterns
        
        Args:
            historical_data: Historical bloom data
            current_date: Current date (YYYY-MM-DD)
        
        Returns:
            Prediction dictionary
        """
        try:
            if not historical_data:
                return {'status': 'insufficient_data'}
            
            # Extract bloom timing from historical data
            bloom_months = []
            bloom_days = []
            
            for data in historical_data:
                events = data.get('bloom_events', [])
                for event in events:
                    # Would parse actual dates here
                    # For now, use mock data
                    bloom_months.append(4)  # April (spring bloom)
                    bloom_days.append(15)
            
            if not bloom_months:
                return {'status': 'no_historical_blooms'}
            
            # Calculate average bloom timing
            avg_month = int(np.mean(bloom_months))
            avg_day = int(np.mean(bloom_days))
            std_days = int(np.std(bloom_days)) if len(bloom_days) > 1 else 7
            
            # Parse current date
            current = datetime.strptime(current_date, '%Y-%m-%d')
            
            # Predict next bloom
            next_year = current.year if current.month < avg_month else current.year + 1
            predicted_date = datetime(next_year, avg_month, avg_day)
            
            # Calculate confidence
            confidence = 0.8 if len(historical_data) >= 3 else 0.6
            
            return {
                'status': 'success',
                'predicted_date': predicted_date.strftime('%Y-%m-%d'),
                'confidence': confidence,
                'uncertainty_days': std_days,
                'date_range': {
                    'earliest': (predicted_date - timedelta(days=std_days)).strftime('%Y-%m-%d'),
                    'latest': (predicted_date + timedelta(days=std_days)).strftime('%Y-%m-%d')
                },
                'based_on_years': len(historical_data)
            }
            
        except Exception as e:
            logger.error(f"Error predicting bloom: {str(e)}")
            return {'status': 'error', 'message': str(e)}
