from itertools import combinations, chain
from typing import List, Tuple, Dict, Union
import math
from dataclasses import dataclass
from enum import Enum
from collections import Counter
import argparse

def format_resistance(value: float) -> str:
    """Convert resistance value to human readable format with proper scale"""
    scales = [
        (1e12, 'T'), (1e9, 'G'), (1e6, 'M'), (1e3, 'k'),
        (1, ''), (1e-3, 'm'), (1e-6, 'µ'), (1e-9, 'n'), (1e-12, 'p')
    ]
    
    for scale, prefix in scales:
        if value >= scale or scale == 1e-12:
            scaled = value / scale
            if abs(scaled) >= 100:
                # For values >= 100, still show decimals for k/M/G/T scales
                if prefix in ['k', 'M', 'G', 'T']:
                    return f"{scaled:.2f}{prefix}"
                return f"{scaled:.0f}{prefix}" if scaled.is_integer() else f"{scaled:.2f}{prefix}"
            else:
                return f"{scaled:.2f}{prefix}"
    
    return f"{value:.2f}"

class ConnectionType(Enum):
    SERIES = "series"
    PARALLEL = "parallel"
    MIXED = "mixed"

@dataclass
class Circuit:
    resistors: List[List[int]]  # List of resistor chains
    total_resistance: float
    connection_type: ConnectionType
    
    def __str__(self):
        return f"Circuit(R={format_resistance(self.total_resistance)}Ω, type={self.connection_type.value})"
    
    def __eq__(self, other):
        if not isinstance(other, Circuit):
            return False
        
        if self.connection_type != other.connection_type:
            return False
        
        if abs(self.total_resistance - other.total_resistance) > 1e-10:
            return False
        
        # Sort branches internally and then sort all branches for comparison
        self_branches = [sorted(branch) for branch in self.resistors]
        other_branches = [sorted(branch) for branch in other.resistors]
        
        return sorted(self_branches) == sorted(other_branches)
    
    def __hash__(self):
        # Create a hashable representation of the circuit
        branches = tuple(tuple(sorted(branch)) for branch in sorted(self.resistors))
        return hash((branches, self.connection_type))

def parallel_resistance(resistances: List[float]) -> float:
    """Calculate equivalent resistance for parallel connection."""
    if not resistances:
        return 0
    return 1 / sum(1/r for r in resistances)

def series_resistance(resistances: List[float]) -> float:
    """Calculate equivalent resistance for series connection."""
    return sum(resistances)

def generate_resistor_combinations(available_resistors: List[Tuple[int, int]]) -> List[List[int]]:
    """
    Generate all possible resistor combinations from available resistors.
    
    Args:
        available_resistors: List of tuples (resistance_value, count)
    Returns:
        List of unique resistor combinations
    """
    result = []
    
    def is_valid_combination(combo: List[int]) -> bool:
        """Check if combination uses allowed number of each resistor value"""
        counts = Counter(combo)
        for value, max_count in available_resistors:
            if counts[value] > max_count:
                return False
        return True
    
    # First, generate single-value combinations
    for value, count in available_resistors:
        for i in range(1, count + 1):
            combo = [value] * i
            if combo not in result:
                result.append(combo)
    
    # Generate mixed combinations (only combine pairs of single resistors)
    base_combinations = []
    for value, _ in available_resistors:
        base_combinations.append([value])
    
    for i in range(len(base_combinations)):
        for j in range(i + 1, len(base_combinations)):
            combined = sorted(base_combinations[i] + base_combinations[j])
            if is_valid_combination(combined) and combined not in result:
                result.append(combined)
    
    return sorted(result)

def generate_circuits(resistor_combinations: List[List[int]], max_parallel_branches: int = 4) -> List[Circuit]:
    """Generate all possible circuit configurations."""
    circuits = []
    
    # Generate series circuits
    for combo in resistor_combinations:
        total_r = series_resistance(combo)
        circuits.append(Circuit([combo], total_r, ConnectionType.SERIES))
    
    # Generate parallel circuits
    for n in range(2, max_parallel_branches + 1):
        for combo in combinations(resistor_combinations, n):
            if len(combo) <= max_parallel_branches:
                total_r = parallel_resistance([series_resistance(branch) for branch in combo])
                circuits.append(Circuit(list(combo), total_r, ConnectionType.PARALLEL))
    
    return circuits

class CircuitAsciiDrawer:
    def __init__(self, width=120):
        self.width = width
        self.lines = []
        self.resistor_counter = 0
    
    def next_resistor_number(self) -> int:
        self.resistor_counter += 1
        return self.resistor_counter
    
    def format_resistor_value(self, value: float) -> str:
        """Special formatting for resistor values in the circuit diagram"""
        if value >= 100 and value.is_integer():
            return f"{int(value)}"  # No decimal places for large whole numbers
        else:
            return format_resistance(value)  # Use standard formatting for other cases
    
    def create_resistor_string(self, value: float) -> str:
        """Creates a resistor representation with unique number and scaled value"""
        r_num = self.next_resistor_number()
        value_str = self.format_resistor_value(value)
        return f"[R{r_num} {value_str}Ω]"

    def add_line(self, content: str, y: int, x: int = 0):
        while len(self.lines) <= y:
            self.lines.append(" " * self.width)
        current = list(self.lines[y])
        for i, char in enumerate(content):
            pos = x + i
            if pos < self.width:
                current[pos] = char
        self.lines[y] = "".join(current)

    def draw_parallel(self, branches: List[List[int]], start_x: int, y: int) -> int:
        branch_count = len(branches)
        branch_height = 2 * (branch_count - 1)
        start_y = y - branch_height//2
        
        # Draw starting junction
        if branch_count == 2:
            self.add_line("┌", start_y, start_x)
            self.add_line("│", y, start_x)  # Add vertical line
            self.add_line("└", start_y + 2, start_x)
        else:
            for i in range(branch_count):
                current_y = start_y + i*2
                if i == 0:
                    self.add_line("┌", current_y, start_x)
                elif i == branch_count - 1:
                    self.add_line("└", current_y, start_x)
                else:
                    self.add_line("┼", current_y, start_x)  # Use cross for middle junctions
                # Add vertical lines between junctions
                if i > 0:
                    for y_pos in range(current_y - 1, current_y):
                        self.add_line("│", y_pos, start_x)

        # Calculate max branch length
        max_end_x = start_x
        branch_ends = []
        
        # Draw each branch
        for i, branch in enumerate(branches):
            branch_y = start_y + i*2
            current_x = start_x + 1
            
            # Draw resistors in series for this branch
            for j, resistor in enumerate(branch):
                r_str = self.create_resistor_string(float(resistor))
                self.add_line("─" + r_str + "─", branch_y, current_x)
                current_x += len(r_str) + 2
                
                if j < len(branch) - 1:
                    self.add_line("─", branch_y, current_x)
                    current_x += 1
            
            branch_ends.append((current_x, branch_y))
            max_end_x = max(max_end_x, current_x)

        # Draw ending junction and vertical lines
        for i in range(branch_count):
            current_y = start_y + i*2
            if i == 0:
                self.add_line("┐", current_y, max_end_x)
            elif i == branch_count - 1:
                self.add_line("┘", current_y, max_end_x)
            else:
                self.add_line("┼", current_y, max_end_x)
            # Add vertical lines between all rows
            if i < branch_count - 1:
                self.add_line("│", current_y + 1, max_end_x)

        # Draw horizontal wires to align all branches
        for end_x, branch_y in branch_ends:
            if end_x < max_end_x:
                self.add_line("─" * (max_end_x - end_x), branch_y, end_x)

        return max_end_x + 1

    def draw_series(self, resistors: List[int], start_x: int, y: int) -> int:
        current_x = start_x
        
        for i, resistor in enumerate(resistors):
            r_str = self.create_resistor_string(float(resistor))
            self.add_line("─" + r_str + "─", y, current_x)
            current_x += len(r_str) + 2
            
            if i < len(resistors) - 1:
                self.add_line("─", y, current_x)
                current_x += 1
        
        return current_x

    def draw_circuit(self, circuit: Circuit) -> str:
        self.lines = []
        self.resistor_counter = 0
        
        max_height = 3 if circuit.connection_type == ConnectionType.SERIES else 2 * len(circuit.resistors) + 1
        center_y = max_height // 2
        
        # Draw input wire with arrow
        self.add_line("input >───", center_y, 0)
        current_x = 10
        
        # Draw main circuit
        if circuit.connection_type == ConnectionType.SERIES:
            end_x = self.draw_series(circuit.resistors[0], current_x, center_y)
        else:  # PARALLEL
            end_x = self.draw_parallel(circuit.resistors, current_x, center_y)
        
        # Draw output wire with arrow
        self.add_line("───> output", center_y, end_x)
        
        # Add empty lines above and below
        final_art = [" " * self.width] * 2 + self.lines + [" " * self.width] * 2
        return "\n".join(line.rstrip() for line in final_art)

def draw_circuit(circuit: Circuit) -> str:
    """Create ASCII art representation of the circuit."""
    drawer = CircuitAsciiDrawer()
    return drawer.draw_circuit(circuit)

def find_best_circuits(available_resistors: List[Tuple[int, int]], 
                      target_resistance: float,
                      tolerance_percent: float = 5.0,
                      max_results: int = 5,
                      prioritize_fewer_components: bool = False) -> List[Tuple[Circuit, float]]:
    """
    Find the best circuits that match the target resistance within tolerance.
    """
    resistor_combinations = generate_resistor_combinations(available_resistors)
    all_circuits = set()  # Use a set to automatically remove duplicates
    
    # Generate circuits with component count validation
    for combo in resistor_combinations:
        # Validate series circuits
        circuit = Circuit([combo], series_resistance(combo), ConnectionType.SERIES)
        all_circuits.add(circuit)
        
        # Generate parallel combinations that respect component limits
        for n in range(2, min(5, len(resistor_combinations) + 1)):
            for parallel_combo in combinations(resistor_combinations, n):
                # Check if the total component count is valid
                total_used = Counter(chain(*parallel_combo))
                valid = True
                for value, count in available_resistors:
                    if total_used[value] > count:
                        valid = False
                        break
                
                if valid:
                    total_r = parallel_resistance([series_resistance(branch) for branch in parallel_combo])
                    circuit = Circuit(list(parallel_combo), total_r, ConnectionType.PARALLEL)
                    all_circuits.add(circuit)
    
    tolerance = target_resistance * (tolerance_percent / 100)
    matching_circuits = []
    
    for circuit in all_circuits:
        deviation = abs(circuit.total_resistance - target_resistance)
        if deviation <= tolerance:
            total_components = sum(len(branch) for branch in circuit.resistors)
            matching_circuits.append((circuit, deviation, total_components))
    
    if prioritize_fewer_components:
        matching_circuits.sort(key=lambda x: (x[2], x[1]))
    else:
        matching_circuits.sort(key=lambda x: x[1])
    
    return [(circuit, deviation) for circuit, deviation, _ in matching_circuits[:max_results]]

def main():
    parser = argparse.ArgumentParser(description="Find optimal resistor circuits for a target resistance.")
    parser.add_argument("target", type=float, help="Target resistance in ohms")
    parser.add_argument("resistors", nargs="+", type=str, help="Available resistors in format 'value:count', e.g., '100:2 200:3'")
    parser.add_argument("-t", "--tolerance", type=float, default=5.0, help="Tolerance percentage (default: 5.0)")
    parser.add_argument("-m", "--max-results", type=int, default=5, help="Maximum number of results to display (default: 5)")
    parser.add_argument("-p", "--prioritize-fewer", action="store_true", help="Prioritize circuits with fewer components")
    parser.add_argument("-o", "--output-dir", type=str, help="Directory to save output files")
    
    args = parser.parse_args()

    # Parse resistor input
    try:
        available_resistors = [tuple(map(int, r.split(':'))) for r in args.resistors]
    except ValueError:
        parser.error("Invalid resistor format. Use 'value:count', e.g., '100:2 200:3'")

    target_resistance = args.target
    tolerance_percent = args.tolerance
    prioritize_fewer_components = args.prioritize_fewer
    
    print(f"Finding circuits closest to {target_resistance}Ω (±{tolerance_percent}%)")
    print(f"Available resistors: {available_resistors}")
    print(f"Prioritizing fewer components: {prioritize_fewer_components}")
    print()
    
    best_circuits = find_best_circuits(
        available_resistors, 
        target_resistance, 
        tolerance_percent,
        max_results=args.max_results,
        prioritize_fewer_components=prioritize_fewer_components
    )
    
    if not best_circuits:
        print("No circuits found within the specified tolerance.")
        return
    
    print(f"Found {len(best_circuits)} circuits within tolerance:")
    print()
    
    if args.output_dir:
        import os
        os.makedirs(args.output_dir, exist_ok=True)
    
    for i, (circuit, deviation) in enumerate(best_circuits, 1):
        component_count = sum(len(branch) for branch in circuit.resistors)
        output = []
        output.append(f"Circuit {i}:")
        output.append(f"Equivalent resistance: {format_resistance(circuit.total_resistance)}Ω")
        output.append(f"Deviation from target: {format_resistance(deviation)}Ω ({(deviation/target_resistance*100):.1f}%)")
        output.append(f"Configuration: {circuit.connection_type.value}")
        output.append(f"Total components: {component_count}")
        output.append("Circuit diagram:")
        output.append(draw_circuit(circuit))
        output.append("")
        
        # Print to console
        print("\n".join(output))
        
        # Save to file if output directory is specified
        if args.output_dir:
            filename = os.path.join(args.output_dir, f"circuit_{i}.txt")
            with open(filename, 'w') as f:
                f.write("\n".join(output))
            print(f"Saved circuit {i} to {filename}")

    if args.output_dir:
        print(f"\nAll circuits have been saved to the directory: {args.output_dir}")

if __name__ == "__main__":
    main()
