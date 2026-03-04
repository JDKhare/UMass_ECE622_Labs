// lab1_parser_jkhare.cpp
// Ubuntu 14: g++ -std=c++11 -O2 lab1_parser_jkhare.cpp -o lab1_parser_jkhare
//
// Usage:
//   ./lab1_parser <verilog.v> <target_bits> <unroll_k> <init_bits> <out_dir> <minisat_path>
//
// Produces:
//   <out_dir>/out.dimacs  (CNF reachability query)
//   <out_dir>/out.nodes   (varID:nodeName,timeframe)
//   <out_dir>/out.sat     (minisat output: SAT/UNSAT + model)
//
// Notes:
// - Designed for "stoplight-like" structural netlists with AND/NOT gates and
//   state regs updated from NS* in a posedge always block.
// - We treat the transition relation as: state(t), inputs(t) -> combinational -> NS(t),
//   then enforce state(t+1) == NS(t).
// - Initial state is constrained from <init_bits>.

#include <bits/stdc++.h>
#include <cstdlib>
using namespace std;

struct Gate {
  string type;       // "and" or "not"
  string out;
  vector<string> in; // for not: size=1
};

static inline string trim(const string &s) {
  size_t b = s.find_first_not_of(" \t\r\n");
  if (b == string::npos) return "";
  size_t e = s.find_last_not_of(" \t\r\n");
  return s.substr(b, e - b + 1);
}

static inline bool starts_with(const string& s, const string& p) {
  return s.size() >= p.size() && equal(p.begin(), p.end(), s.begin());
}

// Remove // comments and /* */ comments (simple, works for typical lab files)
string strip_comments(const string &src) {
  string out;
  out.reserve(src.size());
  bool in_block = false;
  for (size_t i = 0; i < src.size(); ) {
    if (!in_block && i + 1 < src.size() && src[i] == '/' && src[i+1] == '/') {
      while (i < src.size() && src[i] != '\n') i++;
      continue;
    }
    if (!in_block && i + 1 < src.size() && src[i] == '/' && src[i+1] == '*') {
      in_block = true;
      i += 2;
      continue;
    }
    if (in_block && i + 1 < src.size() && src[i] == '*' && src[i+1] == '/') {
      in_block = false;
      i += 2;
      continue;
    }
    if (!in_block) out.push_back(src[i]);
    i++;
  }
  return out;
}

// Split by commas, semicolons, spaces (for decl lists)
vector<string> split_names(const string& s) {
  vector<string> names;
  string cur;
  for (char c : s) {
    if (isalnum(c) || c == '_' ) cur.push_back(c);
    else {
      if (!cur.empty()) { names.push_back(cur); cur.clear(); }
    }
  }
  if (!cur.empty()) names.push_back(cur);
  return names;
}

// Parse gate line like: and g1(n14,S2,n13);
bool parse_gate_line(const string& line, Gate &g) {
  string t = trim(line);
  if (!(starts_with(t, "and ") || starts_with(t, "not "))) return false;

  // type
  size_t sp = t.find(' ');
  g.type = t.substr(0, sp);

  // find '(' and ')'
  size_t lp = t.find('(');
  size_t rp = t.rfind(')');
  if (lp == string::npos || rp == string::npos || rp <= lp) return false;

  string inside = t.substr(lp + 1, rp - lp - 1); // e.g. n14,S2,n13
  // but first token before '(' is instance name, we ignore it, so inside starts with out
  // Actually format: and g1(out,in1,in2,...)
  // So inside tokens split by commas
  vector<string> toks;
  string tmp;
  for (char c : inside) {
    if (c == ',') { toks.push_back(trim(tmp)); tmp.clear(); }
    else tmp.push_back(c);
  }
  toks.push_back(trim(tmp));

  if (toks.size() < 2) return false;

  g.out = toks[0];
  g.in.assign(toks.begin() + 1, toks.end());
  return true;
}

struct Netlist {
  vector<string> inputs;
  vector<string> outputs;
  vector<string> regs;   // state bits like S3,S2...
  vector<string> wires;  // internal wires, includes NS*
  vector<Gate> gates;

  // mapping state_reg -> ns_wire (from always block)
  // e.g. S3 <= NS3;
  vector<pair<string,string>> state_updates;

  // For this lab, we assume ONE state vector is the regs updated from NS regs.
};

struct CNF {
  int nvars = 0;
  vector<array<int,3>> clauses3; // not used heavily, but kept
  vector<vector<int>> clauses;
  void add_clause(const vector<int>& c) { clauses.push_back(c); }
};

struct VarMap {
  // varID -> (nodeName, timeframe)
  vector<pair<string,int>> id2node; // index 1-based, id2node[id] valid
  unordered_map<string,int> key2id; // key = node@t
  int next_id = 1;

  int get(const string& node, int t) {
    string key = node + "@" + to_string(t);
    auto it = key2id.find(key);
    if (it != key2id.end()) return it->second;
    int id = next_id++;
    key2id[key] = id;
    if ((int)id2node.size() <= id) id2node.resize(id+1);
    id2node[id] = {node, t};
    return id;
  }
};

static inline void add_equiv(CNF& cnf, int a, int b) {
  // a <-> b : (¬a ∨ b) ∧ (a ∨ ¬b)
  cnf.add_clause({-a, b});
  cnf.add_clause({ a,-b});
}

static inline void add_not(CNF& cnf, int y, int a) {
  // y <-> ¬a : (a ∨ y) ∧ (¬a ∨ ¬y)
  cnf.add_clause({ a,  y});
  cnf.add_clause({-a, -y});
}

static inline void add_and(CNF& cnf, int y, const vector<int>& xs) {
  // y <-> (x1 ∧ x2 ∧ ... ∧ xn)
  // (¬x1 ∨ ¬x2 ∨ ... ∨ y)
  vector<int> big;
  for (int x: xs) big.push_back(-x);
  big.push_back(y);
  cnf.add_clause(big);
  // (xi ∨ ¬y) for each i
  for (int x: xs) cnf.add_clause({x, -y});
}

Netlist parse_verilog_structural(const string& filename) {
  ifstream fin(filename.c_str());
  if (!fin) {
    cerr << "ERROR: cannot open file " << filename << "\n";
    exit(1);
  }
  string src((istreambuf_iterator<char>(fin)), istreambuf_iterator<char>());
  src = strip_comments(src);

  Netlist nl;

  // Crude line-based parsing; OK for lab netlists
  istringstream iss(src);
  string line;
  bool in_always = false;

  while (getline(iss, line)) {
    string t = trim(line);
    if (t.empty()) continue;

    if (t.find("always") != string::npos) {
      in_always = true;
      continue;
    }
    if (in_always) {
      if (t.find("end") != string::npos) { in_always = false; continue; }
      // parse "S3<=NS3;"
      // remove spaces
      string u;
      for (char c: t) if (!isspace((unsigned char)c)) u.push_back(c);
      size_t le = u.find("<=");
      if (le != string::npos) {
        string lhs = u.substr(0, le);
        string rhs = u.substr(le+2);
        // strip trailing ;
        if (!rhs.empty() && rhs.back() == ';') rhs.pop_back();
        nl.state_updates.push_back({lhs, rhs});
      }
      continue;
    }

    // Declarations
    if (starts_with(t, "input ")) {
      // e.g. input Ped,clock;
      auto names = split_names(t.substr(6));
      for (auto &n: names) nl.inputs.push_back(n);
      continue;
    }
    if (starts_with(t, "output ")) {
      auto names = split_names(t.substr(7));
      for (auto &n: names) nl.outputs.push_back(n);
      continue;
    }
    if (starts_with(t, "reg ")) {
      auto names = split_names(t.substr(4));
      for (auto &n: names) nl.regs.push_back(n);
      continue;
    }
    if (starts_with(t, "wire ")) {
      auto names = split_names(t.substr(5));
      for (auto &n: names) nl.wires.push_back(n);
      continue;
    }

    // Gates
    Gate g;
    if (parse_gate_line(t, g)) {
      nl.gates.push_back(g);
      continue;
    }
  }

  if (nl.state_updates.empty()) {
    cerr << "WARNING: no state updates found in always block. Unrolling may be meaningless.\n";
  }
  return nl;
}

int main(int argc, char** argv) {
  if (argc != 7) {
    cerr << "Usage: " << argv[0] << " <verilog.v> <target_bits> <unroll_k> <init_bits> <out_dir> <minisat_path>\n";
return 1;
  }

  string vfile = argv[1];
  string target = argv[2];
  int k = atoi(argv[3]);
  string init_bits = argv[4];
  string out_dir = argv[5];
  string minisat_path = argv[6];
  if (k < 0) { cerr << "ERROR: unroll_k must be >= 0\n"; return 1; }

  Netlist nl = parse_verilog_structural(vfile);

  // Identify "state regs" as those appearing on LHS of state_updates
  vector<string> state_regs;
  vector<string> ns_wires;
  {
    unordered_set<string> sset;
    for (auto &p : nl.state_updates) {
      state_regs.push_back(p.first);
      ns_wires.push_back(p.second);
      sset.insert(p.first);
    }
    if ((int)state_regs.size() == 0) {
      cerr << "ERROR: no state regs found from always block.\n";
      return 1;
    }
  }

  // target bits must match number of state regs
  if ((int)target.size() != (int)state_regs.size()) {
    cerr << "ERROR: target_bits length (" << target.size()
         << ") must equal number of state regs (" << state_regs.size() << ")\n";
    cerr << "State regs inferred (in LHS order): ";
    for (auto &s: state_regs) cerr << s << " ";
    cerr << "\n";
    return 1;
  }

  // init bits must match number of state regs
  if ((int)init_bits.size() != (int)state_regs.size()) {
    cerr << "ERROR: init_bits length (" << init_bits.size()
         << ") must equal number of state regs (" << state_regs.size() << ")\n";
    return 1;
  }

  // Ensure output directory exists
  if (!out_dir.empty()) {
    string cmd = string("mkdir -p ") + out_dir;
    int rc = system(cmd.c_str());
    if (rc != 0) {
 	 cerr << "WARNING: mkdir returned non-zero exit code " << rc << "\n";
	}
  }
  string dimacs_path = out_dir + string("/out.dimacs");
  string nodes_path  = out_dir + string("/out.nodes");
  string sat_path    = out_dir + string("/out.sat");

  // Build CNF
  CNF cnf;
  VarMap vm;

  // We'll create variables as needed. Timeframes:
  // - State regs exist at t=0..k
  // - Inputs exist at t=0..k-1 (only needed in transition copies)
  // - Combinational nets exist per transition copy t=0..k-1

  // Helper: ensure vars for nodes in a given transition copy
  auto var = [&](const string& node, int t)->int { return vm.get(node, t); };

  // For each transition copy t = 0..k-1, encode all gates as constraints for that copy
  for (int t = 0; t < k; t++) {
    // Ensure state regs vars exist for this t (and t+1 will be created when needed)
    for (auto &sr : state_regs) (void)var(sr, t);
    for (auto &in : nl.inputs)  (void)var(in, t);

    // Encode gate constraints
    for (const auto &g : nl.gates) {
      int y = var(g.out, t);
      vector<int> xs;
      for (auto &iname : g.in) xs.push_back(var(iname, t));

      if (g.type == "not") {
        if (xs.size() != 1) {
          cerr << "ERROR: not gate with !=1 input\n";
          return 1;
        }
        add_not(cnf, y, xs[0]);
      } else if (g.type == "and") {
        if (xs.size() < 2) {
          cerr << "ERROR: and gate with <2 inputs\n";
          return 1;
        }
        add_and(cnf, y, xs);
      } else {
        cerr << "ERROR: unsupported gate type: " << g.type << "\n";
        return 1;
      }
    }

    // State update constraints: state(t+1) == NS(t)
    for (size_t i = 0; i < nl.state_updates.size(); i++) {
      const string &S  = nl.state_updates[i].first;
      const string &NS = nl.state_updates[i].second;
      int s_next = var(S, t+1);
      int ns_now = var(NS, t);
      add_equiv(cnf, s_next, ns_now);
    }
  }

  // Reachability target constraint at time k:
  // "target state as string of 0/1 ordered by descending index as listed in table"
  // We interpret your given order as exactly the order of state_regs inferred from always block,
  // BUT you can reorder here if your table says (S3,S2,S1,S0).
  // If your always block is S3,S2,S1,S0, you're good.
  for (int i = 0; i < (int)state_regs.size(); i++) {
    char b = target[i];
    int v = var(state_regs[i], k);
    if (b == '1') cnf.add_clause({ v});
    else if (b == '0') cnf.add_clause({-v});
    else {
      cerr << "ERROR: target_bits must be only 0/1\n";
      return 1;
    }
  }
  // Constrain initial state at time 0
  for (int i = 0; i < (int)state_regs.size(); i++) {
    char b = init_bits[i];
    int v = var(state_regs[i], 0);
    if (b == '1') cnf.add_clause({ v});
    else if (b == '0') cnf.add_clause({-v});
    else {
      cerr << "ERROR: init_bits must be only 0/1\n";
return 1;
    }
  }
  
  // Finalize var count
  cnf.nvars = vm.next_id - 1;

  // Write out.nodes
  {
    ofstream fout(nodes_path.c_str());
    if (!fout) { cerr << "ERROR: cannot write " << nodes_path << "\n"; return 1; }
    // lines: varID:nodeName,timeframe
    for (int id = 1; id <= cnf.nvars; id++) {
      auto &p = vm.id2node[id];
      fout << id << ":" << p.first << "," << p.second << "\n";
    }
  }

  // Write out.dimacs
  {
    ofstream fout(dimacs_path.c_str());
    if (!fout) { cerr << "ERROR: cannot write " << dimacs_path << "\n"; return 1; }

    fout << "c Reachability CNF generated by lab1_parser_jkhare.cpp\n";
    fout << "c File: " << vfile << "\n";
    fout << "c Unroll k = " << k << "\n";
    fout << "c Target at time k = " << target << "\n";
    fout << "p cnf " << cnf.nvars << " " << cnf.clauses.size() << "\n";
    for (auto &cl : cnf.clauses) {
      for (int lit : cl) fout << lit << " ";
      fout << "0\n";
    }
  }

  // Run MiniSat on generated CNF
  {
    string cmd = minisat_path + string(" ") + dimacs_path + string(" ") + sat_path;
    int rc = system(cmd.c_str());
    if (rc != 0) {
      cerr << "WARNING: minisat returned non-zero exit code " << rc << "\n";
    }
  }

  cerr << "Wrote " << dimacs_path << " and " << nodes_path << "\n";
  cerr << "State regs inferred (target bit order assumed to match this order): ";
  for (auto &s: state_regs) cerr << s << " ";
  cerr << "\n";
  return 0;
}

