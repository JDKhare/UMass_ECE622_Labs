import sys
import re
from collections import deque

# ─────────────────────────────────────────
# Step 1: Parse the Verilog file
# ─────────────────────────────────────────

def parse_verilog(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # Extract input ports (these are the primary inputs / free variables)
    # There may be multiple "input ...;" lines
    input_matches = re.findall(r'input\s+(.*?);', content, re.DOTALL)
    inputs = []
    for match in input_matches:
        raw = match.replace('\n', ' ')
        ports = [p.strip() for p in raw.split(',')]
        for p in ports:
            if p and p != 'clock':
                inputs.append(p)

    # Extract flip-flop (state) names from always block
    # Pattern: S0<=NS0; S1<=NS1; etc.
    ff_names = re.findall(r'(\w+)\s*<=\s*NS\w+', content)
    # Also try: NS_name <= something
    if not ff_names:
        ff_names = re.findall(r'(\w+)\s*<=', content)

    # Extract register declarations to confirm FF names
    reg_match = re.search(r'reg\s+(.*?);', content, re.DOTALL)
    reg_names = []
    if reg_match:
        raw = reg_match.group(1).replace('\n', ' ')
        reg_names = [r.strip() for r in raw.split(',') if r.strip()]

    # FF names are the reg names (state registers)
    state_regs = reg_names

    # Extract gates: "not gX(out, in);" and "and gX(out, in1, in2);"
    not_gates = re.findall(r'not\s+\w+\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)', content)
    and_gates = re.findall(r'and\s+\w+\s*\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\)', content)

    # Extract next state assignments: which NS variable maps to which state reg
    # always block: S0 <= NS0; means state[S0] gets NS0
    ns_assignments = re.findall(r'(\w+)\s*<=\s*(\w+)', content)
    # ns_assignments: list of (state_reg, ns_wire)

    return {
        'inputs': inputs,
        'state_regs': state_regs,
        'not_gates': not_gates,   # list of (out, in)
        'and_gates': and_gates,   # list of (out, in1, in2)
        'ns_assignments': ns_assignments  # list of (state_reg, ns_wire)
    }


# ─────────────────────────────────────────
# Step 2: Build a signal evaluator
# ─────────────────────────────────────────

def build_evaluator(circuit):
    """
    Returns a function: evaluate(state_dict, input_dict) -> next_state_dict
    
    state_dict:  {reg_name: 0/1}  e.g. {'S0':0, 'S1':0}
    input_dict:  {input_name: 0/1}
    """
    not_gates   = circuit['not_gates']
    and_gates   = circuit['and_gates']
    ns_assignments = circuit['ns_assignments']  # (state_reg, ns_wire)

    def evaluate(state_dict, input_dict):
        # Start with known signal values
        signals = {}
        signals.update(state_dict)
        signals.update(input_dict)

        # Iteratively evaluate gates until stable (handles dependency ordering)
        max_iterations = len(not_gates) + len(and_gates) + 10
        for _ in range(max_iterations):
            changed = False
            for (out, inp) in not_gates:
                if inp in signals:
                    val = 1 - signals[inp]
                    if out not in signals or signals[out] != val:
                        signals[out] = val
                        changed = True
            for (out, in1, in2) in and_gates:
                if in1 in signals and in2 in signals:
                    val = signals[in1] & signals[in2]
                    if out not in signals or signals[out] != val:
                        signals[out] = val
                        changed = True
            if not changed:
                break

        # Read next state
        next_state = {}
        for (state_reg, ns_wire) in ns_assignments:
            if ns_wire in signals:
                next_state[state_reg] = signals[ns_wire]
            else:
                next_state[state_reg] = 0  # default

        return next_state

    return evaluate


# ─────────────────────────────────────────
# Step 3: BFS to count reachable states
# ─────────────────────────────────────────

def bfs_reachable(circuit, max_steps=20):
    state_regs = circuit['state_regs']
    inputs     = circuit['inputs']
    evaluate   = build_evaluator(circuit)

    # Initial state: all FFs = 0
    init_state = tuple([0] * len(state_regs))

    # All possible input combinations
    num_inputs = len(inputs)
    input_combos = []
    for mask in range(2 ** num_inputs):
        combo = {}
        for i, inp in enumerate(inputs):
            combo[inp] = (mask >> i) & 1
        input_combos.append(combo)

    # BFS
    # visited: set of state tuples already reached
    visited = set()
    visited.add(init_state)

    # frontier: states reached at current step
    frontier = {init_state}

    # Table: reachable[i] = cumulative count after i transitions
    reachable_counts = []

    for step in range(1, max_steps + 1):
        new_frontier = set()

        for state_tuple in frontier:
            state_dict = {reg: state_tuple[j] for j, reg in enumerate(state_regs)}

            for input_combo in input_combos:
                next_state_dict = evaluate(state_dict, input_combo)
                next_tuple = tuple(next_state_dict.get(reg, 0) for reg in state_regs)

                if next_tuple not in visited:
                    visited.add(next_tuple)
                    new_frontier.add(next_tuple)

        frontier = new_frontier
        # Cumulative count excludes initial state (count only newly reachable)
        reachable_counts.append(len(visited) - 1)  # subtract initial state

        print(f"  i={step:2d}: cumulative reachable states = {len(visited)-1}")

    return reachable_counts


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 partC.py <verilog_file>")
        sys.exit(1)

    filename = sys.argv[1]
    print(f"\nParsing {filename}...")
    circuit = parse_verilog(filename)

    print(f"  State registers ({len(circuit['state_regs'])}): {circuit['state_regs']}")
    print(f"  Primary inputs  ({len(circuit['inputs'])}): {circuit['inputs']}")
    print(f"  NOT gates: {len(circuit['not_gates'])}")
    print(f"  AND gates: {len(circuit['and_gates'])}")
    print(f"  Total possible states: 2^{len(circuit['state_regs'])} = {2**len(circuit['state_regs'])}")
    print()

    print("Running BFS (i = 1 to 20)...")
    counts = bfs_reachable(circuit, max_steps=20)

    print()
    print("=" * 35)
    print(f"{'i':>4} | {'Cumulative Reachable States':>26}")
    print("-" * 35)
    for i, c in enumerate(counts, 1):
        print(f"{i:>4} | {c:>26}")
    print("=" * 35)


if __name__ == '__main__':
    main()