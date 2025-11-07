#!/usr/bin/env python3
"""
Test script for the stimulus order management feature.
This script tests the functionality without requiring the full GUI environment.
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eeg_stimulus_project.assets.asset_handler import Display


class TestStimulusOrderManagement(unittest.TestCase):
    """Test cases for the stimulus order management feature."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear any existing custom orders
        Display.custom_orders = {}
        
        # Mock image objects
        self.mock_beer = Mock()
        self.mock_beer.filename = "Beer.jpg"
        
        self.mock_stella = Mock()
        self.mock_stella.filename = "Stella.jpg"
        
        self.mock_corona = Mock()
        self.mock_corona.filename = "Corona.jpg"
        
        self.mock_miller = Mock()
        self.mock_miller.filename = "Miller.jpg"
    
    def test_set_and_get_custom_orders(self):
        """Test setting and getting custom orders."""
        custom_orders = {
            'Unisensory Neutral Visual': [self.mock_corona, self.mock_miller],
            'Unisensory Alcohol Visual': [self.mock_stella, self.mock_beer]
        }
        
        Display.set_custom_orders(custom_orders)
        retrieved_orders = Display.get_custom_orders()
        
        self.assertEqual(len(retrieved_orders), 2)
        self.assertIn('Unisensory Neutral Visual', retrieved_orders)
        self.assertIn('Unisensory Alcohol Visual', retrieved_orders)
        self.assertEqual(len(retrieved_orders['Unisensory Neutral Visual']), 2)
        self.assertEqual(len(retrieved_orders['Unisensory Alcohol Visual']), 2)
    
    def test_custom_order_priority(self):
        """Test that custom orders take priority over randomization."""
        # Set a custom order
        custom_orders = {
            'Unisensory Neutral Visual': [self.mock_corona, self.mock_miller]
        }
        Display.set_custom_orders(custom_orders)
        
        # Mock the image loading to avoid file system dependencies
        with unittest.mock.patch('eeg_stimulus_project.assets.asset_handler.load_images_from_folder') as mock_load:
            mock_load.return_value = [self.mock_beer, self.mock_stella]
            
            with unittest.mock.patch('eeg_stimulus_project.assets.asset_handler.personalized_images', [self.mock_corona, self.mock_miller]):
                # Get assets with randomization enabled
                assets = Display.get_assets(randomize_cues=True, seed=42)
                
                # Check that custom order is used instead of randomization
                self.assertIn('Unisensory Neutral Visual', assets)
                neutral_images = assets['Unisensory Neutral Visual']
                self.assertEqual(len(neutral_images), 2)
                self.assertEqual(neutral_images[0], self.mock_corona)
                self.assertEqual(neutral_images[1], self.mock_miller)
    
    def test_no_custom_order_uses_default(self):
        """Test that without custom orders, default behavior is used."""
        # Clear any custom orders
        Display.custom_orders = {}
        
        # Mock the image loading
        with unittest.mock.patch('eeg_stimulus_project.assets.asset_handler.load_images_from_folder') as mock_load:
            mock_load.return_value = [self.mock_beer, self.mock_stella]
            
            with unittest.mock.patch('eeg_stimulus_project.assets.asset_handler.personalized_images', [self.mock_corona, self.mock_miller]):
                # Get assets without randomization
                assets = Display.get_assets(randomize_cues=False, seed=None)
                
                # Check that default order is used
                self.assertIn('Unisensory Neutral Visual', assets)
                neutral_images = assets['Unisensory Neutral Visual']
                self.assertEqual(len(neutral_images), 2)
    
    def test_empty_custom_orders(self):
        """Test behavior with empty custom orders."""
        Display.set_custom_orders({})
        retrieved_orders = Display.get_custom_orders()
        
        self.assertEqual(len(retrieved_orders), 0)
        self.assertEqual(retrieved_orders, {})


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)