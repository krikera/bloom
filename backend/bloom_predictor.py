"""
Bloom Prediction Engine
Predicts future bloom events based on historical patterns and environmental factors
"""

import numpy as np
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from scipy.stats import linregress

logger = logging.getLogger(__name__)


class BloomPredictor:
    """Predict future bloom events using statistical and pattern-based methods"""
    
    def __init__(self):
        """Initialize bloom predictor"""
        self.prediction_models = {
            'statistical': self._statistical_prediction,
            'pattern_based': self._pattern_based_prediction,
            'trend_adjusted': self._trend_adjusted_prediction
        }
    
    def predict_next_bloom(
        self,
        historical_blooms: List[Dict],
        location: Dict,
        vegetation_type: Optional[str] = None,
        current_date: Optional[str] = None
    ) -> Dict:
        """
        Predict the next bloom event
        
        Args:
            historical_blooms: List of historical bloom analysis results
            location: Dict with 'lat' and 'lon'
            vegetation_type: Identified vegetation type
            current_date: Current date (YYYY-MM-DD), defaults to today
        
        Returns:
            Dict with prediction results
        """
        try:
            if not current_date:
                current_date = datetime.now().strftime('%Y-%m-%d')
            
            current = datetime.strptime(current_date, '%Y-%m-%d')
            
            if len(historical_blooms) == 0:
                return {
                    'status': 'insufficient_data',
                    'message': 'No historical bloom data available for prediction',
                    'confidence': 0.0
                }
            
            # Extract bloom timing patterns
            bloom_dates = []
            peak_ndvi_values = []
            
            for bloom_data in historical_blooms:
                events = bloom_data.get('bloom_events', [])
                year = bloom_data.get('year')
                
                for event in events:
                    peak_date = event.get('peak_date')
                    if peak_date:
                        try:
                            dt = datetime.strptime(peak_date, '%Y-%m-%d')
                            bloom_dates.append(dt)
                            peak_ndvi_values.append(event.get('peak_ndvi', 0))
                        except:
                            pass
            
            if len(bloom_dates) < 2:
                return {
                    'status': 'insufficient_data',
                    'message': 'Need at least 2 years of historical data for prediction',
                    'confidence': 0.0
                }
            
            # Run multiple prediction methods
            predictions = {}
            
            # Statistical prediction (average)
            stat_pred = self._statistical_prediction(bloom_dates, peak_ndvi_values, current)
            predictions['statistical'] = stat_pred
            
            # Pattern-based prediction
            pattern_pred = self._pattern_based_prediction(bloom_dates, peak_ndvi_values, current, vegetation_type)
            predictions['pattern_based'] = pattern_pred
            
            # Trend-adjusted prediction
            trend_pred = self._trend_adjusted_prediction(bloom_dates, peak_ndvi_values, current)
            predictions['trend_adjusted'] = trend_pred
            
            # Combine predictions (weighted ensemble)
            final_prediction = self._ensemble_prediction(predictions, len(historical_blooms))
            
            # Add metadata
            final_prediction['based_on_years'] = len(historical_blooms)
            final_prediction['historical_bloom_dates'] = [d.strftime('%Y-%m-%d') for d in bloom_dates[-5:]]
            final_prediction['current_date'] = current_date
            final_prediction['location'] = location
            
            logger.info(f"Bloom prediction: {final_prediction['predicted_date']} (confidence: {final_prediction['confidence']:.2f})")
            
            return final_prediction
            
        except Exception as e:
            logger.error(f"Error predicting bloom: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'confidence': 0.0
            }
    
    def _statistical_prediction(
        self,
        bloom_dates: List[datetime],
        peak_ndvi_values: List[float],
        current_date: datetime
    ) -> Dict:
        """Simple statistical prediction based on historical averages"""
        # Calculate average day of year for blooms
        days_of_year = [d.timetuple().tm_yday for d in bloom_dates]
        avg_doy = int(np.mean(days_of_year))
        std_doy = int(np.std(days_of_year)) if len(days_of_year) > 1 else 14
        
        # Calculate average peak NDVI
        avg_peak_ndvi = float(np.mean(peak_ndvi_values))
        
        # Determine next year
        avg_month = int(np.mean([d.month for d in bloom_dates]))
        next_year = current_date.year if current_date.month < avg_month else current_date.year + 1
        
        # Create prediction date
        predicted_date = datetime(next_year, 1, 1) + timedelta(days=avg_doy - 1)
        
        return {
            'method': 'statistical_average',
            'predicted_date': predicted_date.strftime('%Y-%m-%d'),
            'predicted_peak_ndvi': avg_peak_ndvi,
            'uncertainty_days': std_doy,
            'confidence': min(0.6 + (len(bloom_dates) * 0.05), 0.85),
            'date_range': {
                'earliest': (predicted_date - timedelta(days=std_doy)).strftime('%Y-%m-%d'),
                'latest': (predicted_date + timedelta(days=std_doy)).strftime('%Y-%m-%d')
            }
        }
    
    def _pattern_based_prediction(
        self,
        bloom_dates: List[datetime],
        peak_ndvi_values: List[float],
        current_date: datetime,
        vegetation_type: Optional[str]
    ) -> Dict:
        """Prediction based on vegetation type patterns"""
        # Group blooms by year and find primary bloom
        yearly_blooms = {}
        for date, ndvi in zip(bloom_dates, peak_ndvi_values):
            year = date.year
            if year not in yearly_blooms:
                yearly_blooms[year] = []
            yearly_blooms[year].append((date, ndvi))
        
        # Find peak bloom for each year
        primary_blooms = []
        for year, blooms in yearly_blooms.items():
            peak_bloom = max(blooms, key=lambda x: x[1])
            primary_blooms.append(peak_bloom[0])
        
        # Calculate pattern
        days_of_year = [d.timetuple().tm_yday for d in primary_blooms]
        median_doy = int(np.median(days_of_year))
        
        # Adjust based on vegetation type
        adjustment = 0
        if vegetation_type:
            if 'desert' in vegetation_type:
                adjustment = -5  # Desert blooms trending earlier
            elif 'tree' in vegetation_type:
                adjustment = -7  # Tree blooms shifting earlier due to climate
        
        predicted_doy = median_doy + adjustment
        
        # Determine next year
        avg_month = int(np.median([d.month for d in primary_blooms]))
        next_year = current_date.year if current_date.month < avg_month else current_date.year + 1
        
        predicted_date = datetime(next_year, 1, 1) + timedelta(days=predicted_doy - 1)
        
        return {
            'method': 'pattern_based',
            'predicted_date': predicted_date.strftime('%Y-%m-%d'),
            'predicted_peak_ndvi': float(np.median(peak_ndvi_values)),
            'uncertainty_days': int(np.std(days_of_year)) if len(days_of_year) > 1 else 10,
            'confidence': min(0.65 + (len(primary_blooms) * 0.05), 0.88),
            'adjustment_applied': adjustment,
            'adjustment_reason': f'Climate trend adjustment for {vegetation_type}' if vegetation_type else 'None'
        }
    
    def _trend_adjusted_prediction(
        self,
        bloom_dates: List[datetime],
        peak_ndvi_values: List[float],
        current_date: datetime
    ) -> Dict:
        """Prediction adjusted for temporal trends"""
        if len(bloom_dates) < 3:
            return self._statistical_prediction(bloom_dates, peak_ndvi_values, current_date)
        
        # Calculate trend in bloom timing
        years = [d.year for d in bloom_dates]
        days_of_year = [d.timetuple().tm_yday for d in bloom_dates]
        
        # Linear regression on bloom timing
        if len(set(years)) >= 3:
            slope, intercept, r_value, _, _ = linregress(years, days_of_year)
            
            # Predict for next year
            avg_month = int(np.mean([d.month for d in bloom_dates]))
            next_year = current_date.year if current_date.month < avg_month else current_date.year + 1
            
            predicted_doy = int(slope * next_year + intercept)
            predicted_date = datetime(next_year, 1, 1) + timedelta(days=predicted_doy - 1)
            
            # Assess trend
            days_per_year = slope
            trend_direction = 'earlier' if days_per_year < 0 else 'later'
            trend_magnitude = abs(days_per_year)
            
            confidence = min(0.7 + (abs(r_value) * 0.2), 0.92)
            
            return {
                'method': 'trend_adjusted',
                'predicted_date': predicted_date.strftime('%Y-%m-%d'),
                'predicted_peak_ndvi': float(np.mean(peak_ndvi_values)),
                'uncertainty_days': int(np.std(days_of_year)),
                'confidence': confidence,
                'trend': {
                    'direction': trend_direction,
                    'rate_days_per_year': float(days_per_year),
                    'magnitude': 'strong' if trend_magnitude > 2 else 'moderate' if trend_magnitude > 0.5 else 'weak',
                    'r_squared': float(r_value ** 2)
                },
                'interpretation': self._interpret_trend(days_per_year, r_value ** 2)
            }
        
        return self._statistical_prediction(bloom_dates, peak_ndvi_values, current_date)
    
    def _ensemble_prediction(
        self,
        predictions: Dict[str, Dict],
        n_years: int
    ) -> Dict:
        """Combine multiple prediction methods into ensemble"""
        # Weight predictions based on data availability and confidence
        weights = {
            'statistical': 0.4,
            'pattern_based': 0.35,
            'trend_adjusted': 0.25
        }
        
        # Adjust weights based on data quantity
        if n_years >= 5:
            weights['trend_adjusted'] = 0.35
            weights['statistical'] = 0.30
        
        # Extract dates and convert to days
        reference_date = datetime(2025, 1, 1)
        predicted_days = []
        confidences = []
        
        for method, weight in weights.items():
            if method in predictions and predictions[method].get('predicted_date'):
                pred_date = datetime.strptime(predictions[method]['predicted_date'], '%Y-%m-%d')
                days_from_ref = (pred_date - reference_date).days
                predicted_days.append(days_from_ref * weight)
                confidences.append(predictions[method].get('confidence', 0.5) * weight)
        
        # Calculate weighted average
        avg_days = sum(predicted_days)
        avg_confidence = sum(confidences)
        
        final_date = reference_date + timedelta(days=int(avg_days))
        
        # Calculate uncertainty (max spread)
        all_dates = [datetime.strptime(p['predicted_date'], '%Y-%m-%d') 
                     for p in predictions.values() if p.get('predicted_date')]
        if len(all_dates) > 1:
            date_diff = [(d - min(all_dates)).days for d in all_dates]
            uncertainty = int(np.std(date_diff)) + 7
        else:
            uncertainty = 14
        
        # Build final prediction
        result = {
            'status': 'success',
            'predicted_date': final_date.strftime('%Y-%m-%d'),
            'confidence': avg_confidence,
            'confidence_level': self._confidence_level(avg_confidence),
            'uncertainty_days': uncertainty,
            'date_range': {
                'earliest': (final_date - timedelta(days=uncertainty)).strftime('%Y-%m-%d'),
                'most_likely': final_date.strftime('%Y-%m-%d'),
                'latest': (final_date + timedelta(days=uncertainty)).strftime('%Y-%m-%d')
            },
            'prediction_methods': {
                method: {
                    'date': pred['predicted_date'],
                    'confidence': pred.get('confidence', 0),
                    'weight': weights[method]
                }
                for method, pred in predictions.items()
            },
            'recommendations': self._generate_recommendations(final_date, avg_confidence, uncertainty)
        }
        
        return result
    
    def _confidence_level(self, score: float) -> str:
        """Convert confidence score to level"""
        if score >= 0.80:
            return 'Very High'
        elif score >= 0.65:
            return 'High'
        elif score >= 0.50:
            return 'Moderate'
        elif score >= 0.35:
            return 'Low'
        else:
            return 'Very Low'
    
    def _interpret_trend(self, days_per_year: float, r_squared: float) -> str:
        """Interpret bloom timing trend"""
        if r_squared < 0.3:
            return "No clear trend - blooms occur at variable times each year"
        
        if abs(days_per_year) < 0.5:
            return "Stable bloom timing - no significant shift detected"
        elif days_per_year < -2:
            return "Strong trend: Blooms occurring significantly earlier each year (likely climate impact)"
        elif days_per_year < 0:
            return "Moderate trend: Blooms shifting slightly earlier (possible climate signal)"
        elif days_per_year > 2:
            return "Blooms occurring significantly later each year (investigate cause)"
        else:
            return "Slight trend toward later blooms"
    
    def _generate_recommendations(
        self,
        predicted_date: datetime,
        confidence: float,
        uncertainty: int
    ) -> List[str]:
        """Generate actionable recommendations based on prediction"""
        recommendations = []
        
        # Monitoring recommendations
        monitoring_start = predicted_date - timedelta(days=uncertainty + 14)
        recommendations.append(
            f"Begin monitoring from {monitoring_start.strftime('%Y-%m-%d')} "
            f"({uncertainty + 14} days before predicted bloom)"
        )
        
        # Confidence-based recommendations
        if confidence >= 0.75:
            recommendations.append("High confidence prediction - suitable for planning activities")
            recommendations.append("Consider advance logistics preparation")
        elif confidence >= 0.55:
            recommendations.append("Moderate confidence - maintain flexible planning")
            recommendations.append("Monitor weather conditions closely")
        else:
            recommendations.append("Low confidence - use as rough estimate only")
            recommendations.append("Require real-time monitoring for confirmation")
        
        # Uncertainty recommendations
        if uncertainty > 21:
            recommendations.append(f"High uncertainty (±{uncertainty} days) - check weekly")
        elif uncertainty > 14:
            recommendations.append(f"Moderate uncertainty (±{uncertainty} days) - check bi-weekly")
        else:
            recommendations.append(f"Low uncertainty (±{uncertainty} days) - reliable timeframe")
        
        # General recommendations
        recommendations.append("Validate prediction with ground observations")
        recommendations.append("Update prediction as season approaches")
        
        return recommendations
