"""
Bay Mapping System for Turntable

This module manages the mapping between stimulus objects and turntable bays.
It provides a default mapping and allows for customization based on object names.
"""

import os
import re


class BayMapper:
    """
    Maps stimulus objects to specific turntable bays (0-15).
    Provides intelligent mapping based on object names and allows customization.
    """
    
    def __init__(self):
        # Default mapping for common object names (bay numbers are 0-based)
        self.default_mapping = {
            # Alcohol-related objects
            'beer': 0,
            'wine': 1,
            'vodka': 2,
            'whiskey': 3,
            'stella': 4,
            'heineken': 5,
            'budweiser': 6,
            'corona': 7,
            
            # Neutral objects
            'water': 8,
            'soda': 9,
            'juice': 10,
            'coffee': 11,
            'tea': 12,
            'milk': 13,
            'cup': 14,
            'bottle': 15
        }
        
        # Custom mappings can be added at runtime
        self.custom_mapping = {}
        
    def normalize_name(self, name):
        """Normalize object name for matching."""
        if not name:
            return ""
        
        # Get base filename without extension
        base_name = os.path.splitext(os.path.basename(name))[0]
        
        # Convert to lowercase and remove common separators
        normalized = base_name.lower()
        normalized = re.sub(r'[_\-\s]+', '', normalized)
        
        return normalized
    
    def get_bay_for_object(self, object_name):
        """
        Get the bay number (0-15) for a given object name.
        
        Args:
            object_name (str): Name of the object (can be filename or object name)
            
        Returns:
            int: Bay number (0-15), or None if no mapping found
        """
        if not object_name:
            return None
            
        normalized = self.normalize_name(object_name)
        
        # Check custom mapping first
        if normalized in self.custom_mapping:
            return self.custom_mapping[normalized]
            
        # Check default mapping
        if normalized in self.default_mapping:
            return self.default_mapping[normalized]
            
        # Try partial matches
        for key, bay in self.default_mapping.items():
            if key in normalized or normalized in key:
                return bay
                
        return None
    
    def set_custom_mapping(self, object_name, bay_number):
        """
        Set a custom mapping for an object to a specific bay.
        
        Args:
            object_name (str): Name of the object
            bay_number (int): Bay number (0-15)
        """
        if 0 <= bay_number <= 15:
            normalized = self.normalize_name(object_name)
            self.custom_mapping[normalized] = bay_number
        else:
            raise ValueError("Bay number must be between 0 and 15")
    
    def get_bay_sequence_for_assets(self, assets):
        """
        Get a sequence of bay numbers for a list of asset objects.
        
        Args:
            assets (list): List of asset objects with filename attributes
            
        Returns:
            list: List of bay numbers corresponding to each asset
        """
        bay_sequence = []
        
        for asset in assets:
            # Skip craving rating assets or other non-physical objects
            if hasattr(asset, 'asset_type') and asset.asset_type == 'craving_rating':
                continue
                
            # Get object name from filename
            if hasattr(asset, 'filename') and asset.filename:
                bay = self.get_bay_for_object(asset.filename)
                if bay is not None:
                    bay_sequence.append(bay)
                else:
                    # Default to bay 0 if no mapping found
                    bay_sequence.append(0)
            else:
                # Default to bay 0 for unknown objects
                bay_sequence.append(0)
                
        return bay_sequence
    
    def get_all_mappings(self):
        """Get all current mappings (default + custom)."""
        all_mappings = self.default_mapping.copy()
        all_mappings.update(self.custom_mapping)
        return all_mappings
    
    def clear_custom_mappings(self):
        """Clear all custom mappings."""
        self.custom_mapping.clear()


# Global instance for easy access
bay_mapper = BayMapper()