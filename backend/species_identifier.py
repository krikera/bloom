"""
Species Identifier and Ecological Context Provider
Provides intelligent hints about vegetation type and ecological significance
"""

import numpy as np
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SpeciesIdentifier:
    """Identify likely vegetation types and provide ecological context"""
    
    def __init__(self):
        """Initialize species identifier with knowledge base"""
        self.vegetation_types = self._load_vegetation_knowledge()
        self.regional_ecology = self._load_regional_ecology()
    
    def _load_vegetation_knowledge(self) -> Dict:
        """Load vegetation type signatures and characteristics"""
        return {
            'desert_wildflowers': {
                'ndvi_range': (0.3, 0.6),
                'evi_range': (0.35, 0.65),
                'peak_duration_days': (14, 45),
                'typical_months': [3, 4, 5],  # Spring
                'rapid_onset': True,
                'indicators': {
                    'rapid_increase': 0.15,  # NDVI increase per week
                    'peak_sharpness': 0.8,
                    'coverage_pattern': 'patchy'
                },
                'common_species': [
                    'California Poppy (Eschscholzia californica)',
                    'Desert Sunflower (Geraea canescens)',
                    'Chia (Salvia columbariae)',
                    'Lupine (Lupinus spp.)',
                    'Phacelia (Phacelia spp.)'
                ],
                'confidence_factors': {
                    'location_desert': 0.3,
                    'spring_timing': 0.25,
                    'rapid_onset': 0.25,
                    'ndvi_match': 0.2
                }
            },
            'tree_blossoms': {
                'ndvi_range': (0.4, 0.7),
                'evi_range': (0.45, 0.75),
                'peak_duration_days': (7, 21),
                'typical_months': [3, 4],  # Early spring
                'rapid_onset': True,
                'indicators': {
                    'rapid_increase': 0.2,
                    'peak_sharpness': 0.9,
                    'coverage_pattern': 'localized'
                },
                'common_species': [
                    'Cherry (Prunus spp.)',
                    'Apple (Malus spp.)',
                    'Magnolia (Magnolia spp.)',
                    'Dogwood (Cornus spp.)',
                    'Redbud (Cercis spp.)'
                ],
                'confidence_factors': {
                    'urban_proximity': 0.3,
                    'spring_timing': 0.3,
                    'short_duration': 0.25,
                    'ndvi_match': 0.15
                }
            },
            'agricultural_crops': {
                'ndvi_range': (0.5, 0.85),
                'evi_range': (0.55, 0.9),
                'peak_duration_days': (30, 90),
                'typical_months': [5, 6, 7, 8],  # Growing season
                'rapid_onset': False,
                'indicators': {
                    'rapid_increase': 0.1,
                    'peak_sharpness': 0.5,
                    'coverage_pattern': 'uniform'
                },
                'common_species': [
                    'Corn/Maize (Zea mays)',
                    'Soybeans (Glycine max)',
                    'Wheat (Triticum spp.)',
                    'Cotton (Gossypium spp.)',
                    'Canola/Rapeseed (Brassica napus)'
                ],
                'confidence_factors': {
                    'agricultural_area': 0.35,
                    'uniform_coverage': 0.25,
                    'sustained_high_ndvi': 0.25,
                    'timing': 0.15
                }
            },
            'grassland_prairie': {
                'ndvi_range': (0.35, 0.65),
                'evi_range': (0.4, 0.7),
                'peak_duration_days': (45, 120),
                'typical_months': [5, 6, 7, 8],
                'rapid_onset': False,
                'indicators': {
                    'rapid_increase': 0.08,
                    'peak_sharpness': 0.4,
                    'coverage_pattern': 'extensive'
                },
                'common_species': [
                    'Big Bluestem (Andropogon gerardii)',
                    'Indian Grass (Sorghastrum nutans)',
                    'Switchgrass (Panicum virgatum)',
                    'Prairie Wildflowers (various)',
                    'Tallgrass species'
                ],
                'confidence_factors': {
                    'grassland_location': 0.35,
                    'gradual_greening': 0.3,
                    'sustained_moderate': 0.2,
                    'timing': 0.15
                }
            },
            'forest_canopy': {
                'ndvi_range': (0.6, 0.9),
                'evi_range': (0.65, 0.95),
                'peak_duration_days': (120, 180),
                'typical_months': [5, 6, 7, 8, 9],
                'rapid_onset': False,
                'indicators': {
                    'rapid_increase': 0.05,
                    'peak_sharpness': 0.3,
                    'coverage_pattern': 'dense'
                },
                'common_species': [
                    'Deciduous trees (Oak, Maple, etc.)',
                    'Mixed forest understory',
                    'Evergreen undergrowth'
                ],
                'confidence_factors': {
                    'forest_location': 0.4,
                    'high_ndvi': 0.3,
                    'sustained_green': 0.2,
                    'timing': 0.1
                }
            }
        }
    
    def _load_regional_ecology(self) -> Dict:
        """Load regional ecological context"""
        return {
            'california_desert': {
                'lat_range': (32.5, 37.0),
                'lon_range': (-121.0, -114.0),
                'primary_bloom_type': 'desert_wildflowers',
                'bloom_triggers': [
                    'Winter rainfall > 3 inches',
                    'Timing: October-March rain',
                    'Temperature: Warm spring days'
                ],
                'ecological_significance': [
                    'Critical pollinator food source',
                    'Seed bank germination event',
                    'Indicator of climate variability',
                    'Tourism and economic impact',
                    'Soil stabilization and erosion control'
                ],
                'conservation_concerns': [
                    'Off-road vehicle damage',
                    'Trampling by visitors',
                    'Climate change affecting rainfall patterns',
                    'Invasive species competition'
                ],
                'management_recommendations': {
                    'pre_bloom': [
                        'Monitor rainfall patterns',
                        'Prepare visitor infrastructure',
                        'Coordinate with tourism boards',
                        'Set up protective barriers'
                    ],
                    'during_bloom': [
                        'Enforce stay-on-trail policies',
                        'Limit vehicle access',
                        'Educational signage',
                        'Monitor visitor impact'
                    ],
                    'post_bloom': [
                        'Assess soil damage',
                        'Reseed damaged areas',
                        'Document seed production',
                        'Plan for next season'
                    ]
                }
            },
            'washington_dc': {
                'lat_range': (38.8, 39.0),
                'lon_range': (-77.1, -76.9),
                'primary_bloom_type': 'tree_blossoms',
                'bloom_triggers': [
                    'Cumulative heat units > 1,000',
                    'Timing: Late March-Early April',
                    'Temperature: 5-7 consecutive warm days'
                ],
                'ecological_significance': [
                    'Cultural and historical importance',
                    'Early-season pollinator resource',
                    'Phenology indicator species',
                    'Urban heat island mitigation',
                    'Economic impact from tourism'
                ],
                'conservation_concerns': [
                    'Climate change shifting bloom dates',
                    'Late frost damage risk',
                    'Urban development pressure',
                    'Disease and pest management'
                ],
                'management_recommendations': {
                    'pre_bloom': [
                        'Monitor temperature forecasts',
                        'Issue peak bloom predictions',
                        'Coordinate event planning',
                        'Tree health assessments'
                    ],
                    'during_bloom': [
                        'Traffic and crowd management',
                        'Protect tree root zones',
                        'Document bloom progression',
                        'Public education programs'
                    ],
                    'post_bloom': [
                        'Assess tree health',
                        'Disease monitoring',
                        'Document timing for trends',
                        'Plan maintenance activities'
                    ]
                }
            },
            'great_plains': {
                'lat_range': (36.0, 49.0),
                'lon_range': (-104.0, -96.0),
                'primary_bloom_type': 'grassland_prairie',
                'bloom_triggers': [
                    'Spring moisture availability',
                    'Temperature > 60°F sustained',
                    'Fire history (promotes flowering)'
                ],
                'ecological_significance': [
                    'Carbon sequestration',
                    'Pollinator diversity hotspot',
                    'Grazing land productivity',
                    'Soil health indicator',
                    'Watershed protection'
                ],
                'conservation_concerns': [
                    'Agricultural conversion',
                    'Overgrazing',
                    'Invasive species (e.g., smooth brome)',
                    'Fire suppression impacts',
                    'Climate variability'
                ],
                'management_recommendations': {
                    'pre_bloom': [
                        'Plan prescribed burns',
                        'Assess forage availability',
                        'Monitor soil moisture',
                        'Control invasive species'
                    ],
                    'during_bloom': [
                        'Adjust grazing timing',
                        'Document species diversity',
                        'Pollinator surveys',
                        'Seed collection for restoration'
                    ],
                    'post_bloom': [
                        'Evaluate grazing impact',
                        'Assess seed production',
                        'Plan restoration activities',
                        'Document for baseline data'
                    ]
                }
            }
        }
    
    def identify_vegetation_type(
        self,
        ndvi_values: np.ndarray,
        evi_values: np.ndarray,
        bloom_events: List[Dict],
        location: Dict,
        dates: Optional[List[str]] = None
    ) -> Dict:
        """
        Identify likely vegetation type based on bloom characteristics
        
        Args:
            ndvi_values: NDVI time series
            evi_values: EVI time series
            bloom_events: Detected bloom events
            location: Dict with 'lat' and 'lon'
            dates: Optional list of observation dates
        
        Returns:
            Dict with vegetation type, confidence, and species hints
        """
        try:
            if len(bloom_events) == 0:
                return {
                    'vegetation_type': 'unknown',
                    'confidence': 0.0,
                    'reason': 'No bloom events detected'
                }
            
            # Extract characteristics
            peak_ndvi = float(np.max(ndvi_values)) if len(ndvi_values) > 0 else 0
            mean_ndvi = float(np.mean(ndvi_values)) if len(ndvi_values) > 0 else 0
            peak_evi = float(np.max(evi_values)) if len(evi_values) > 0 else 0
            
            # Analyze bloom pattern
            primary_bloom = max(bloom_events, key=lambda x: x.get('peak_ndvi', 0))
            duration = primary_bloom.get('duration_observations', 0) * 16  # Assume 16-day intervals
            
            # Extract month if dates available
            bloom_month = None
            if dates and len(dates) > 0 and primary_bloom.get('peak_date'):
                try:
                    bloom_month = datetime.strptime(primary_bloom['peak_date'], '%Y-%m-%d').month
                except:
                    pass
            
            # Calculate scores for each vegetation type
            scores = {}
            for veg_type, characteristics in self.vegetation_types.items():
                score = 0.0
                reasons = []
                
                # NDVI range match
                ndvi_min, ndvi_max = characteristics['ndvi_range']
                if ndvi_min <= peak_ndvi <= ndvi_max:
                    score += 0.3
                    reasons.append(f"NDVI matches {veg_type} range")
                
                # Duration match
                dur_min, dur_max = characteristics['peak_duration_days']
                if dur_min <= duration <= dur_max:
                    score += 0.25
                    reasons.append(f"Bloom duration typical for {veg_type}")
                
                # Month match
                if bloom_month and bloom_month in characteristics['typical_months']:
                    score += 0.25
                    reasons.append(f"Timing matches {veg_type} season")
                
                # Onset pattern
                increase_rate = primary_bloom.get('increase_rate', 0)
                if characteristics['rapid_onset'] and increase_rate > 0.1:
                    score += 0.2
                    reasons.append(f"Rapid onset typical for {veg_type}")
                elif not characteristics['rapid_onset'] and increase_rate < 0.1:
                    score += 0.2
                    reasons.append(f"Gradual greening typical for {veg_type}")
                
                scores[veg_type] = {'score': score, 'reasons': reasons}
            
            # Find best match
            best_type = max(scores.items(), key=lambda x: x[1]['score'])
            vegetation_type = best_type[0]
            confidence = best_type[1]['score']
            
            result = {
                'vegetation_type': vegetation_type,
                'vegetation_type_display': vegetation_type.replace('_', ' ').title(),
                'confidence': confidence,
                'confidence_level': self._confidence_level(confidence),
                'likely_species': self.vegetation_types[vegetation_type]['common_species'],
                'characteristics': {
                    'peak_ndvi': peak_ndvi,
                    'mean_ndvi': mean_ndvi,
                    'peak_evi': peak_evi,
                    'bloom_duration_days': duration,
                    'bloom_month': bloom_month
                },
                'reasoning': best_type[1]['reasons'],
                'alternative_types': sorted(
                    [(k, v['score']) for k, v in scores.items() if k != vegetation_type],
                    key=lambda x: x[1],
                    reverse=True
                )[:2]
            }
            
            logger.info(f"Identified vegetation type: {vegetation_type} (confidence: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error identifying vegetation type: {str(e)}")
            return {
                'vegetation_type': 'unknown',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def get_ecological_context(
        self,
        location: Dict,
        vegetation_type: str,
        bloom_characteristics: Dict
    ) -> Dict:
        """
        Provide ecological context and conservation implications
        
        Args:
            location: Dict with 'lat' and 'lon'
            vegetation_type: Identified vegetation type
            bloom_characteristics: Bloom analysis results
        
        Returns:
            Dict with ecological context and management recommendations
        """
        try:
            lat = location['lat']
            lon = location['lon']
            
            # Find matching region
            matching_region = None
            region_name = None
            
            for region, info in self.regional_ecology.items():
                lat_range = info['lat_range']
                lon_range = info['lon_range']
                if lat_range[0] <= lat <= lat_range[1] and lon_range[0] <= lon <= lon_range[1]:
                    matching_region = info
                    region_name = region
                    break
            
            if not matching_region:
                return self._generic_ecological_context(vegetation_type)
            
            # Build context
            context = {
                'region': region_name.replace('_', ' ').title(),
                'location': {
                    'latitude': lat,
                    'longitude': lon
                },
                'primary_vegetation': matching_region['primary_bloom_type'].replace('_', ' ').title(),
                'bloom_triggers': matching_region['bloom_triggers'],
                'ecological_significance': matching_region['ecological_significance'],
                'conservation_concerns': matching_region['conservation_concerns'],
                'management_recommendations': matching_region['management_recommendations'],
                'interpretation': self._interpret_bloom_significance(
                    bloom_characteristics,
                    vegetation_type,
                    matching_region
                )
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting ecological context: {str(e)}")
            return {'error': str(e)}
    
    def _confidence_level(self, score: float) -> str:
        """Convert confidence score to level"""
        if score >= 0.75:
            return 'High'
        elif score >= 0.5:
            return 'Moderate'
        elif score >= 0.25:
            return 'Low'
        else:
            return 'Very Low'
    
    def _interpret_bloom_significance(
        self,
        bloom_chars: Dict,
        veg_type: str,
        region_info: Dict
    ) -> Dict:
        """Interpret the significance of detected bloom"""
        peak_ndvi = bloom_chars.get('peak_ndvi', 0)
        
        interpretation = {
            'bloom_strength': 'unknown',
            'compared_to_typical': 'unknown',
            'ecological_impact': [],
            'timing_assessment': 'normal'
        }
        
        # Assess bloom strength
        if peak_ndvi > 0.7:
            interpretation['bloom_strength'] = 'Exceptional - very strong bloom'
            interpretation['ecological_impact'].append('High nectar and pollen production')
            interpretation['ecological_impact'].append('Excellent pollinator support')
        elif peak_ndvi > 0.5:
            interpretation['bloom_strength'] = 'Strong - good bloom conditions'
            interpretation['ecological_impact'].append('Good pollinator resources')
        elif peak_ndvi > 0.3:
            interpretation['bloom_strength'] = 'Moderate - typical bloom'
            interpretation['ecological_impact'].append('Moderate ecological benefit')
        else:
            interpretation['bloom_strength'] = 'Weak - limited bloom'
            interpretation['ecological_impact'].append('Limited ecological impact')
        
        # Add context-specific impacts
        if veg_type == 'desert_wildflowers':
            interpretation['ecological_impact'].append('Seed bank replenishment')
            interpretation['ecological_impact'].append('Desert ecosystem pulse event')
        elif veg_type == 'tree_blossoms':
            interpretation['ecological_impact'].append('Early-season pollinator food')
            interpretation['ecological_impact'].append('Urban ecosystem services')
        elif veg_type == 'agricultural_crops':
            interpretation['ecological_impact'].append('Crop productivity indicator')
            interpretation['ecological_impact'].append('Yield potential assessment')
        
        return interpretation
    
    def _generic_ecological_context(self, veg_type: str) -> Dict:
        """Provide generic ecological context when region not matched"""
        return {
            'region': 'Unknown Region',
            'primary_vegetation': veg_type.replace('_', ' ').title(),
            'ecological_significance': [
                'Vegetation greenup detected',
                'Seasonal change indicator',
                'Ecosystem productivity pulse'
            ],
            'interpretation': {
                'bloom_strength': 'Analysis complete',
                'ecological_impact': ['Vegetation growth detected']
            }
        }
