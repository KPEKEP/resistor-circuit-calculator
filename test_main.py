import unittest
from typing import List, Tuple
from itertools import chain

# Import all functions from the main module
# Assuming the main code is in a file called resistor_circuit.py
from main import (
    format_resistance,
    parallel_resistance,
    series_resistance,
    generate_resistor_combinations,
    generate_circuits,
    find_best_circuits,
    Circuit,
    ConnectionType,
)

class TestResistorCircuit(unittest.TestCase):
    def test_format_resistance(self):
        """Test resistance formatting for different scales"""
        test_cases = [
            (0.0000042, "4.20µ"),
            (0.047, "47.00m"),
            (1.0, "1.00"),
            (4.7, "4.70"),
            (47, "47.00"),
            (470, "470"),
            (4700, "4.70k"),
            (47000, "47.00k"),
            (470000, "470.00k"),
            (4700000, "4.70M"),
            (4700000000, "4.70G"),
        ]
        
        for value, expected in test_cases:
            with self.subTest(value=value):
                result = format_resistance(value)
                self.assertEqual(result, expected)

    def test_parallel_resistance(self):
        """Test parallel resistance calculations"""
        test_cases = [
            ([100, 100], 50),  # Two equal resistors
            ([100, 200, 400], 57.14285714285714),  # Three different resistors
            ([1000], 1000),  # Single resistor
            ([100, 100, 100, 100], 25),  # Four equal resistors
        ]
        
        for resistors, expected in test_cases:
            with self.subTest(resistors=resistors):
                result = parallel_resistance(resistors)
                self.assertAlmostEqual(result, expected, places=2)

    def test_series_resistance(self):
        """Test series resistance calculations"""
        test_cases = [
            ([100, 100], 200),  # Two equal resistors
            ([100, 200, 300], 600),  # Three different resistors
            ([1000], 1000),  # Single resistor
            ([250, 250, 250, 250], 1000),  # Four equal resistors
        ]
        
        for resistors, expected in test_cases:
            with self.subTest(resistors=resistors):
                result = series_resistance(resistors)
                self.assertEqual(result, expected)

    def test_generate_resistor_combinations(self):
        """Test generation of resistor combinations"""
        available_resistors = [(100, 2), (200, 1)]  # Two 100Ω and one 200Ω
        combinations = generate_resistor_combinations(available_resistors)
        
        # Expected combinations:
        expected = [
            [100],          # Single 100Ω
            [100, 100],     # Two 100Ω in series
            [200],          # Single 200Ω
            [100, 200],     # 100Ω and 200Ω in series
        ]
        
        self.assertEqual(len(combinations), len(expected))
        for combo in expected:
            self.assertIn(combo, combinations)

    def test_generate_circuits(self):
        """Test circuit generation with various configurations"""
        resistor_combinations = [[100], [200], [100, 100]]
        circuits = generate_circuits(resistor_combinations, max_parallel_branches=2)
        
        # Check if we have all expected circuit types
        series_circuits = [c for c in circuits if c.connection_type == ConnectionType.SERIES]
        parallel_circuits = [c for c in circuits if c.connection_type == ConnectionType.PARALLEL]
        
        # Verify series circuits
        self.assertGreaterEqual(len(series_circuits), 3)  # Should have at least 3 series configurations
        
        # Verify parallel circuits
        self.assertGreater(len(parallel_circuits), 0)  # Should have some parallel configurations
        
        # Check resistance calculations
        for circuit in circuits:
            if circuit.connection_type == ConnectionType.SERIES:
                expected = sum(chain(*circuit.resistors))
                self.assertEqual(circuit.total_resistance, expected)
            elif circuit.connection_type == ConnectionType.PARALLEL:
                branches = [sum(branch) for branch in circuit.resistors]
                expected = parallel_resistance(branches)
                self.assertAlmostEqual(circuit.total_resistance, expected, places=2)

    def test_find_best_circuits(self):
        """Test finding best circuits for given target resistance"""
        available_resistors = [(100, 3), (220, 2)]  # Three 100Ω and two 220Ω
        target_resistance = 150
        tolerance_percent = 10
        
        # Test with fewer components priority
        circuits_fewer = find_best_circuits(
            available_resistors,
            target_resistance,
            tolerance_percent,
            max_results=5,
            prioritize_fewer_components=True
        )
        
        # Test with accuracy priority
        circuits_accurate = find_best_circuits(
            available_resistors,
            target_resistance,
            tolerance_percent,
            max_results=5,
            prioritize_fewer_components=False
        )
        
        for circuit_list in [circuits_fewer, circuits_accurate]:
            self.assertGreater(len(circuit_list), 0)  # Should find some circuits
            
            # Check if all circuits are within tolerance
            for circuit, deviation in circuit_list:
                self.assertLessEqual(
                    deviation,
                    target_resistance * (tolerance_percent / 100)
                )
                
                # Check component counts
                total_components = sum(len(branch) for branch in circuit.resistors)
                available_count = sum(count for _, count in available_resistors)
                self.assertLessEqual(total_components, available_count)
                
                # Verify each resistor value is valid
                valid_values = {value for value, _ in available_resistors}
                for branch in circuit.resistors:
                    for resistor in branch:
                        self.assertIn(resistor, valid_values)

    def test_edge_cases(self):
        """Test edge cases and potential error conditions"""
        # Test empty resistor list
        self.assertEqual(parallel_resistance([]), 0)
        self.assertEqual(series_resistance([]), 0)
        
        # Test single resistor
        self.assertEqual(parallel_resistance([100]), 100)
        self.assertEqual(series_resistance([100]), 100)
        
        # Test very small and very large values
        self.assertTrue(format_resistance(1e-12).endswith('p'))
        self.assertTrue(format_resistance(1e12).endswith('T'))
        
        # Test with no available resistors
        empty_circuits = find_best_circuits([], 100, 10)
        self.assertEqual(len(empty_circuits), 0)

    def test_component_counts(self):
        """Test that circuits don't use more components than available"""
        available_resistors = [(100, 2), (220, 1)]  # Two 100Ω and one 220Ω
        target_resistance = 150
        
        circuits = find_best_circuits(
            available_resistors,
            target_resistance,
            tolerance_percent=20,
            max_results=10
        )
        
        for circuit, _ in circuits:
            # Count usage of each resistor value
            usage = {}
            for branch in circuit.resistors:
                for r in branch:
                    usage[r] = usage.get(r, 0) + 1
            
            # Verify against available counts
            for value, count in available_resistors:
                self.assertLessEqual(
                    usage.get(value, 0),
                    count,
                    f"Circuit uses more {value}Ω resistors than available"
                )

if __name__ == '__main__':
    unittest.main()