"""
Regional Bloom Scanner
Scans larger regions to detect bloom hotspots and patterns
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = logging.getLogger(__name__)


class RegionalScanner:
    """Scan regions for bloom detection and create spatial bloom maps"""
    
    def __init__(self, data_fetcher, bloom_detector, vi_calculator):
        """
        Initialize regional scanner
        
        Args:
            data_fetcher: SatelliteDataFetcher instance
            bloom_detector: BloomDetector instance
            vi_calculator: VegetationIndexCalculator instance
        """
        self.data_fetcher = data_fetcher
        self.bloom_detector = bloom_detector
        self.vi_calculator = vi_calculator
        self.max_workers = 3  # Limit parallel requests
    
    def _summarize_data_source(self, data: Optional[Dict]) -> Dict:
        """Summarize satellite data provenance for regional outputs"""
        if not data:
            return {
                'real_data': False,
                'demo_mode': True,
                'satellite': None,
                'notes': 'No satellite data returned.'
            }

        summary = {
            'real_data': bool(data.get('real_data')),
            'demo_mode': bool(data.get('demo_mode')),
            'satellite': data.get('satellite'),
            'notes': data.get('notes')
        }

        ndvi_data = data.get('ndvi_data')
        if isinstance(ndvi_data, dict) and not summary['notes']:
            summary['notes'] = ndvi_data.get('note')

        for nested_key in ('landsat', 'sentinel'):
            nested = data.get(nested_key)
            if nested:
                nested_summary = self._summarize_data_source(nested)
                summary['real_data'] = summary['real_data'] or nested_summary['real_data']
                summary['demo_mode'] = summary['demo_mode'] and nested_summary['demo_mode']
                if nested_summary['notes']:
                    if summary['notes']:
                        summary['notes'] = f"{summary['notes']} {nested_summary['notes']}"
                    else:
                        summary['notes'] = nested_summary['notes']

        if summary['real_data'] and summary['demo_mode']:
            summary['demo_mode'] = False

        return summary

    def scan_region(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: str,
        end_date: str,
        grid_resolution: float = 0.25,
        satellite: str = 'combined'
    ) -> Dict:
        """
        Scan a bounding box region for blooms
        
        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            grid_resolution: Grid spacing in degrees (~25km at equator)
            satellite: Satellite source
        
        Returns:
            Dict with regional bloom analysis
        """
        try:
            min_lon, min_lat, max_lon, max_lat = bbox
            
            logger.info(f"Scanning region: {bbox} from {start_date} to {end_date}")
            
            # Generate grid points
            lons = np.arange(min_lon, max_lon, grid_resolution)
            lats = np.arange(min_lat, max_lat, grid_resolution)
            
            grid_points = [(lat, lon) for lat in lats for lon in lons]
            total_points = len(grid_points)
            
            logger.info(f"Generated {total_points} grid points for analysis")
            
            if total_points > 100:
                return {
                    'status': 'error',
                    'message': f'Region too large ({total_points} points). Please use smaller area or coarser resolution.',
                    'recommendation': 'Try grid_resolution >= 0.5 degrees or smaller bbox'
                }
            
            # Analyze grid points in parallel
            bloom_results = []
            analyzed_count = 0
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_point = {
                    executor.submit(
                        self._analyze_point,
                        lat, lon,
                        start_date, end_date,
                        satellite
                    ): (lat, lon)
                    for lat, lon in grid_points
                }
                
                for future in as_completed(future_to_point):
                    lat, lon = future_to_point[future]
                    analyzed_count += 1
                    
                    try:
                        result = future.result(timeout=30)
                        if result and result.get('has_bloom'):
                            bloom_results.append(result)
                        
                        # Rate limiting
                        if analyzed_count % 5 == 0:
                            logger.info(f"Progress: {analyzed_count}/{total_points} points analyzed")
                            time.sleep(1)  # Brief pause
                            
                    except Exception as e:
                        logger.warning(f"Error analyzing point ({lat}, {lon}): {str(e)}")
            
            # Aggregate results
            regional_summary = self._aggregate_results(
                bloom_results,
                bbox,
                start_date,
                end_date
            )
            
            logger.info(f"Regional scan complete: {len(bloom_results)} bloom locations found")
            
            return regional_summary
            
        except Exception as e:
            logger.error(f"Error in regional scan: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def scan_predefined_region(
        self,
        region_name: str,
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Scan a predefined region by name
        
        Args:
            region_name: Name of predefined region
            start_date: Start date
            end_date: End date
        
        Returns:
            Regional bloom analysis
        """
        predefined_regions = {
            'california_desert': {
                'bbox': (-120.0, 33.0, -115.0, 37.0),
                'name': 'California Desert Region',
                'grid_resolution': 0.3
            },
            'antelope_valley': {
                'bbox': (-118.6, 34.5, -117.9, 34.95),
                'name': 'Antelope Valley',
                'grid_resolution': 0.1
            },
            'death_valley': {
                'bbox': (-117.5, 36.0, -116.5, 37.0),
                'name': 'Death Valley Region',
                'grid_resolution': 0.2
            },
            'carrizo_plain': {
                'bbox': (-120.2, 35.0, -119.6, 35.4),
                'name': 'Carrizo Plain',
                'grid_resolution': 0.1
            },
            'washington_dc': {
                'bbox': (-77.2, 38.8, -76.9, 39.0),
                'name': 'Washington DC Metro',
                'grid_resolution': 0.05
            },
            'great_plains_kansas': {
                'bbox': (-97.5, 37.5, -96.0, 39.0),
                'name': 'Kansas Great Plains',
                'grid_resolution': 0.25
            }
        }
        
        if region_name not in predefined_regions:
            return {
                'status': 'error',
                'message': f'Unknown region: {region_name}',
                'available_regions': list(predefined_regions.keys())
            }
        
        region = predefined_regions[region_name]
        
        result = self.scan_region(
            region['bbox'],
            start_date,
            end_date,
            region['grid_resolution']
        )
        
        if result.get('status') == 'success':
            result['region_name'] = region['name']
        
        return result
    
    def _analyze_point(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        satellite: str
    ) -> Optional[Dict]:
        """Analyze a single point for blooms"""
        try:
            # Fetch data
            satellite_data = self.data_fetcher.fetch_data(
                lat=lat,
                lon=lon,
                start_date=start_date,
                end_date=end_date,
                buffer_km=5,
                satellite=satellite,
                combine_sources=False  # Faster without combination
            )
            
            if not satellite_data:
                return None
            
            # Calculate indices
            ndvi_data = self.vi_calculator.calculate_ndvi(satellite_data)
            
            if len(ndvi_data) == 0:
                return None
            
            # Get dates if available
            dates = None
            if 'ndvi_data' in satellite_data and satellite_data['ndvi_data']:
                dates = satellite_data['ndvi_data'].get('dates', None)
            
            data_source = self._summarize_data_source(satellite_data)
            if not data_source['real_data']:
                logger.debug(f"Point ({lat}, {lon}) using synthesized NDVI")
                
            # Detect blooms
            bloom_events = self.bloom_detector.detect_blooms(
                ndvi_data=ndvi_data,
                dates=dates
            )
            
            if len(bloom_events) == 0:
                return None
            
            # Found bloom!
            peak_bloom = max(bloom_events, key=lambda x: x.get('peak_ndvi', 0))
            
            return {
                'lat': lat,
                'lon': lon,
                'has_bloom': True,
                'bloom_count': len(bloom_events),
                'peak_ndvi': peak_bloom.get('peak_ndvi', 0),
                'peak_date': peak_bloom.get('peak_date', 'unknown'),
                'intensity': self.bloom_detector._calculate_intensity(ndvi_data),
                'average_ndvi': float(ndvi_data.mean()),
                'data_source': data_source
            }
            
        except Exception as e:
            logger.debug(f"Point analysis failed ({lat}, {lon}): {str(e)}")
            return None
    
    def _aggregate_results(
        self,
        bloom_results: List[Dict],
        bbox: Tuple,
        start_date: str,
        end_date: str
    ) -> Dict:
        """Aggregate individual point results into regional summary"""
        if len(bloom_results) == 0:
            return {
                'status': 'success',
                'bloom_detected': False,
                'message': 'No significant blooms detected in this region',
                'bbox': bbox,
                'date_range': {'start': start_date, 'end': end_date}
            }
        
        # Extract metrics
        peak_ndvis = [r['peak_ndvi'] for r in bloom_results]
        intensities = [r['intensity'] for r in bloom_results]
        
        # Find hotspots (top NDVI locations)
        sorted_results = sorted(bloom_results, key=lambda x: x['peak_ndvi'], reverse=True)
        hotspots = sorted_results[:10]  # Top 10 locations
        
        # Spatial distribution
        lats = [r['lat'] for r in bloom_results]
        lons = [r['lon'] for r in bloom_results]
        
        # Intensity distribution
        intensity_counts = {}
        for intensity in intensities:
            intensity_counts[intensity] = intensity_counts.get(intensity, 0) + 1
        
        # Calculate regional statistics
        summary = {
            'status': 'success',
            'bloom_detected': True,
            'bbox': bbox,
            'date_range': {'start': start_date, 'end': end_date},
            'statistics': {
                'total_bloom_locations': len(bloom_results),
                'average_peak_ndvi': float(np.mean(peak_ndvis)),
                'max_peak_ndvi': float(np.max(peak_ndvis)),
                'min_peak_ndvi': float(np.min(peak_ndvis)),
                'std_peak_ndvi': float(np.std(peak_ndvis))
            },
            'intensity_distribution': intensity_counts,
            'hotspots': hotspots,
            'spatial_extent': {
                'center_lat': float(np.mean(lats)),
                'center_lon': float(np.mean(lons)),
                'lat_range': (float(np.min(lats)), float(np.max(lats))),
                'lon_range': (float(np.min(lons)), float(np.max(lons)))
            },
            'bloom_coverage': {
                'percentage': len(bloom_results) / (
                    ((bbox[2] - bbox[0]) / 0.25) * ((bbox[3] - bbox[1]) / 0.25)
                ) * 100,
                'description': self._describe_coverage(len(bloom_results))
            },
            'all_bloom_locations': bloom_results  # Full dataset for mapping
        }
        
        data_sources = [result.get('data_source', {}) for result in bloom_results]
        if data_sources:
            summary['data_sources'] = {
                'total_points': len(data_sources),
                'real_data_points': sum(1 for source in data_sources if source.get('real_data')),
                'demo_data_points': sum(1 for source in data_sources if source.get('demo_mode')),
                'notes': [source.get('notes') for source in data_sources if source.get('notes')]
            }

        # Add interpretation
        summary['interpretation'] = self._interpret_regional_blooms(summary)
        
        return summary
    
    def _describe_coverage(self, bloom_count: int) -> str:
        """Describe bloom coverage extent"""
        if bloom_count > 50:
            return 'Extensive bloom - widespread across region'
        elif bloom_count > 20:
            return 'Significant bloom - covering large portions'
        elif bloom_count > 10:
            return 'Moderate bloom - scattered throughout region'
        elif bloom_count > 5:
            return 'Limited bloom - isolated pockets'
        else:
            return 'Sparse bloom - few locations detected'
    
    def _interpret_regional_blooms(self, summary: Dict) -> Dict:
        """Interpret regional bloom patterns"""
        stats = summary['statistics']
        avg_ndvi = stats['average_peak_ndvi']
        max_ndvi = stats['max_peak_ndvi']
        bloom_count = stats['total_bloom_locations']
        
        interpretation = {
            'overall_assessment': 'unknown',
            'bloom_quality': 'unknown',
            'spatial_pattern': 'unknown',
            'recommendations': []
        }
        
        # Overall assessment
        if avg_ndvi > 0.6 and bloom_count > 20:
            interpretation['overall_assessment'] = 'Exceptional regional bloom event'
            interpretation['bloom_quality'] = 'Very strong'
        elif avg_ndvi > 0.5 and bloom_count > 10:
            interpretation['overall_assessment'] = 'Strong regional bloom'
            interpretation['bloom_quality'] = 'Strong'
        elif avg_ndvi > 0.4 and bloom_count > 5:
            interpretation['overall_assessment'] = 'Moderate regional bloom'
            interpretation['bloom_quality'] = 'Moderate'
        else:
            interpretation['overall_assessment'] = 'Weak or patchy bloom'
            interpretation['bloom_quality'] = 'Limited'
        
        # Spatial pattern
        std_ndvi = stats['std_peak_ndvi']
        if std_ndvi < 0.1:
            interpretation['spatial_pattern'] = 'Uniform - consistent bloom across region'
        elif std_ndvi < 0.15:
            interpretation['spatial_pattern'] = 'Moderate variation - some areas stronger'
        else:
            interpretation['spatial_pattern'] = 'High variation - very patchy distribution'
        
        # Recommendations
        if bloom_count > 15:
            interpretation['recommendations'].append('Consider regional visitor management')
            interpretation['recommendations'].append('Multiple viewing locations available')
        
        if max_ndvi > 0.7:
            interpretation['recommendations'].append('Exceptional displays at hotspot locations')
            interpretation['recommendations'].append('Priority monitoring of top locations')
        
        if avg_ndvi > 0.5:
            interpretation['recommendations'].append('Good conditions for ecological surveys')
            interpretation['recommendations'].append('Excellent pollinator habitat currently')
        
        return interpretation
