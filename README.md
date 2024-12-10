RESISTOR CIRCUIT CALCULATOR

A Python tool for calculating optimal resistor combinations to achieve target resistance values using available components. This tool can generate both series and parallel circuit configurations while optimizing for either component count or accuracy.

FEATURES
--------
* Calculate series and parallel resistor combinations
* Find optimal circuits for a target resistance within specified tolerance
* Support for multiple resistor values and quantities
* Intelligent circuit generation with customizable parameters
* Resistance formatting in standard engineering notation (pΩ to TΩ)
* Prioritization options for fewer components or better accuracy

USAGE
-----
Example code:

from main import find_best_circuits

# Define available resistors as (value, quantity) tuples
available_resistors = [(100, 3), (220, 2)]  # Three 100Ω and two 220Ω resistors
target_resistance = 150  # Target resistance in ohms
tolerance = 10  # Tolerance in percentage

# Find circuits prioritizing fewer components
circuits = find_best_circuits(
    available_resistors,
    target_resistance,
    tolerance_percent=tolerance,
    max_results=5,
    prioritize_fewer_components=True
)

# Print results
for circuit, deviation in circuits:
    print(f"Circuit: {circuit}")
    print(f"Total Resistance: {circuit.total_resistance}Ω")
    print(f"Deviation: {deviation}Ω")

FUNCTIONS
---------
format_resistance(value): Formats resistance values in engineering notation
parallel_resistance(resistors): Calculates total resistance for parallel configuration
series_resistance(resistors): Calculates total resistance for series configuration
generate_resistor_combinations(available_resistors): Generates valid resistor combinations
generate_circuits(resistor_combinations, max_parallel_branches): Creates possible circuit configurations
find_best_circuits(available_resistors, target_resistance, tolerance_percent): Finds optimal circuits

INSTALLATION
------------
1. Clone the repository:
   git clone https://github.com/KPEKEP/resistor-circuit-calculator.git

2. Navigate to the project directory:
   cd resistor-circuit-calculator

3. Run the tests:
   python -m unittest test_main.py

REQUIREMENTS
-----------
- Python 3.6 or higher
- No external dependencies required

TESTING
-------
The project includes comprehensive unit tests covering:
* Resistance calculations
* Circuit generation
* Component count validation
* Edge cases
* Formatting functions

Run the tests using:
python -m unittest test_main.py

LICENSE
-------
This project is licensed under the MIT License - see the LICENSE file for details.