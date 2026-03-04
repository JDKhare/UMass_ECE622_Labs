# Reachability Analysis Tool (`reachsat`)

`reachsat` is a unified Linux command-line tool for SAT-based reachability analysis of Verilog FSMs. It translates structural Verilog into a CNF formula, runs a SAT solver (`minisat` or `picosat`), and checks if target states are reachable within `k` transitions.

## Prerequisites
- A modern C++ compiler (`g++`)
- A SAT solver in your path (`minisat` or `picosat`)
- Bash and basic UNIX utilities (`bc`, `grep`)

## Usage

The `reachsat` script manages compilation automatically and offers three operation modes.

```bash
./reachsat [OPTIONS]
```

### Modes

1. **`--check`**: Run a single reachability check for a target state at a specific depth.
   ```bash
   ./reachsat --check -v top.v -t 1010 -d 5 
   ```

2. **`--sweep`**: Check if a target state is reachable at *any* depth from 1 to `N`.
   ```bash
   ./reachsat --sweep -v top.v -t 1010 -d 10
   ```
   *(This checks depth 1, then depth 2, ..., up to depth 10).*

3. **`--find`**: Enumerate all possible $2^n$ states and report exactly which states are reachable at a specific depth `k`.
   *(This lists all 4-bit reachable states dynamically).*

---

## Lab 1 Guide: Solving Parts B.2 through B.5

The following examples demonstrate how to use `reachsat` to verify reachability properties for the circuits provided in Lab 1.

### Part B.1: Specific Reachability at $k=2$ (ex1)
Check all 4 possible states of `ex1` to see if they are reachable exactly at transition $k=2$.

```bash
./reachsat --check -v ./verilog_src/ex1.v -t 00 -d 2 -i 00 -l logs_reachability -s minisat
./reachsat --check -v ./verilog_src/ex1.v -t 01 -d 2 -i 00 -l logs_reachability -s minisat
./reachsat --check -v ./verilog_src/ex1.v -t 10 -d 2 -i 00 -l logs_reachability -s minisat
./reachsat --check -v ./verilog_src/ex1.v -t 11 -d 2 -i 00 -l logs_reachability -s minisat
```

### Part B.2: Target Reachability at $k = 15$
Check if the specific target states are reachable right at exactly 15 transitions.

```bash
# ex1.v
./reachsat --check -v ./verilog_src/ex1.v -t 11 -d 15 -i 00 -l logs_reachability -s minisat

# ex2.v
./reachsat --check -v ./verilog_src/ex2.v -t 111111111111111 -d 15 -i 000000000000000 -l logs_reachability -s minisat

# ex3.v
./reachsat --check -v ./verilog_src/ex3.v -t 00000000010110110000011000001 -d 15 -i 00000000000000000000000000000 -l logs_reachability -s minisat

# ex4.v
./reachsat --check -v ./verilog_src/ex4.v -t 00000000000000000000000010000000 -d 15 -i 00000000000000000000000000000000 -l logs_reachability -s minisat

# ex5.v
./reachsat --check -v ./verilog_src/ex5.v -t 000110111 -d 15 -i 000000000 -l logs_reachability -s minisat

# stoplight1.v
./reachsat --check -v ./verilog_src/stoplight1.v -t 0100 -d 15 -i 0000 -l logs_reachability -s minisat

# stoplight2.v
./reachsat --check -v ./verilog_src/stoplight2.v -t 01000 -d 15 -i 00000 -l logs_reachability -s minisat
```
*(Note for ECE622 students: You must re-check these same problems using a different solver and report the runtimes. You can simply run these exact same tests but with the `-s picosat` switch and `--verbose` flag enabled to capture and print the native solver execution time into the `logs_reachability_picosat` folder!)*

```bash
# ex1.v
./reachsat --check -v ./verilog_src/ex1.v -t 11 -d 15 -i 00 -l logs_reachability_picosat -s picosat --verbose

# ex2.v
./reachsat --check -v ./verilog_src/ex2.v -t 111111111111111 -d 15 -i 000000000000000 -l logs_reachability_picosat -s picosat --verbose

# ex3.v
./reachsat --check -v ./verilog_src/ex3.v -t 00000000010110110000011000001 -d 15 -i 00000000000000000000000000000 -l logs_reachability_picosat -s picosat --verbose

# ex4.v
./reachsat --check -v ./verilog_src/ex4.v -t 00000000000000000000000010000000 -d 15 -i 00000000000000000000000000000000 -l logs_reachability_picosat -s picosat --verbose

# ex5.v
./reachsat --check -v ./verilog_src/ex5.v -t 000110111 -d 15 -i 000000000 -l logs_reachability_picosat -s picosat --verbose

# stoplight1.v
./reachsat --check -v ./verilog_src/stoplight1.v -t 0100 -d 15 -i 0000 -l logs_reachability_picosat -s picosat --verbose

# stoplight2.v
./reachsat --check -v ./verilog_src/stoplight2.v -t 01000 -d 15 -i 00000 -l logs_reachability_picosat -s picosat --verbose
```

### Part B.3: Target Distance for `stoplight1`
Sweep from $k=1$ to $k=32$ to find exactly when the target state is met for `stoplight1`.

```bash
./reachsat --sweep -v ./verilog_src/stoplight1.v -t 0100 -d 32 -i 0000 -l logs_reachability -s minisat
```

### Part B.4: Target Distance for `stoplight2`
Sweep from $k=1$ to $k=32$ to find exactly when the target state is met for `stoplight2` (compare it with your random simulation).

```bash
./reachsat --sweep -v ./verilog_src/stoplight2.v -t 01000 -d 32 -i 00000 -l logs_reachability -s minisat
```

### Part B.5: All Reachable States at $k=17$ for `stoplight2`
Enumerate all 5-bit ($2^5=32$) states and find exactly which ones are reachable at transition 17.

```bash
./reachsat --find -v ./verilog_src/stoplight2.v -b 5 -d 17 -i 00000 -l logs_reachability -s minisat
```

### Additional Options

- `-i, --init <bits>`: Use an explicit initial state sequence (defaults to all `0`s equivalent to target length).

- `-s, --solver <minisat|picosat>`: Choose the backend SAT solver (default is minisat).
- `--verbose`: Print detailed, verbose outputs from the SAT solver (e.g., `picosat -v`).
- `-l, --logdir <dir>`: Directory to dump the generated DIMACS CNF formulas, `.nodes` variables mapping, and raw solver `.log`/`.sat` files (defaults to current directory).

## How it works under the hood

The bash script calls a high-performance C++ program (`v2dimacs.cpp`) that:
1. Parses structural Verilog gates (AND, NOT) and state transition registers.
2. Unrolls the transition logic by $k$ transition cycles.
3. Maps variables and builds a CNF constraints DIMACS file along with a `.nodes` lookup text file.

Then, the bash wrapper automatically passes the `.dimacs` file to `minisat` or `picosat`, timing the execution, reading the raw output, and verbosely printing the findings to the terminal. You get a clean `SAT | Target: 1010 | Depth: 5 | Time: 0.012s` interface while keeping all deep technical files preserved in your optional logging directory.
