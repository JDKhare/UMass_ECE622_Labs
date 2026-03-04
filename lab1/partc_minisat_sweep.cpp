#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <array>
#include <cstdlib>
#include <algorithm>
#include <chrono>

using namespace std;

struct Gate {
  string type;
  string out;
  vector<string> in;
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

bool parse_gate_line(const string& line, Gate &g) {
  string t = trim(line);
  if (!(starts_with(t, "and ") || starts_with(t, "not "))) return false;

  size_t sp = t.find(' ');
  g.type = t.substr(0, sp);

  size_t lp = t.find('(');
  size_t rp = t.rfind(')');
  if (lp == string::npos || rp == string::npos || rp <= lp) return false;

  string inside = t.substr(lp + 1, rp - lp - 1); 
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
  vector<string> regs;   
  vector<string> wires;  
  vector<Gate> gates;
  vector<pair<string,string>> state_updates;
};

struct CNF {
  int nvars = 0;
  vector<vector<int>> clauses;
  void add_clause(const vector<int>& c) { clauses.push_back(c); }
};

struct VarMap {
  vector<pair<string,int>> id2node; 
  unordered_map<string,int> key2id; 
  int next_id = 1;

  void clear() {
      id2node.clear();
      key2id.clear();
      next_id = 1;
  }

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
  cnf.add_clause({-a, b});
  cnf.add_clause({ a,-b});
}

static inline void add_not(CNF& cnf, int y, int a) {
  cnf.add_clause({ a,  y});
  cnf.add_clause({-a, -y});
}

static inline void add_and(CNF& cnf, int y, const vector<int>& xs) {
  vector<int> big;
  for (int x: xs) big.push_back(-x);
  big.push_back(y);
  cnf.add_clause(big);
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
      string u;
      for (char c: t) if (!isspace((unsigned char)c)) u.push_back(c);
      size_t le = u.find("<=");
      if (le != string::npos) {
        string lhs = u.substr(0, le);
        string rhs = u.substr(le+2);
        if (!rhs.empty() && rhs.back() == ';') rhs.pop_back();
        nl.state_updates.push_back({lhs, rhs});
      }
      continue;
    }

    if (starts_with(t, "input ")) {
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

    Gate g;
    if (parse_gate_line(t, g)) {
      nl.gates.push_back(g);
      continue;
    }
  }
  return nl;
}

int main(int argc, char** argv) {
  if (argc != 4) {
    cerr << "Usage: " << argv[0] << " <verilog_file> <init_state_bitstring> <max_k>\n";
    cerr << "Example: " << argv[0] << " ./verilog_src/ex5.v 000000000 20\n";
    return 1;
  }

  string vfile = argv[1];
  string init_bits = argv[2];
  int max_k = atoi(argv[3]);
  int n = init_bits.length();

  Netlist nl = parse_verilog_structural(vfile);

  vector<string> state_regs;
  for (auto &p : nl.state_updates) {
    state_regs.push_back(p.first);
  }

  if ((int)state_regs.size() != n) {
    cerr << "ERROR: init_state_bitstring length (" << n << ") does not match inferred state regs (" << state_regs.size() << ").\n";
    return 1;
  }

  // To answer Part C: we need cumulative reachable states for k = 1 to max_k.
  // We represent state as an integer 0..2^n - 1.
  int total_states = 1 << n;
  vector<bool> reachable(total_states, false);
  
  // The initial state is obviously reachable at depth 0
  int init_val = 0;
  for (int i = 0; i < n; i++) {
      if (init_bits[i] == '1') init_val |= (1 << (n - 1 - i));
  }
  // The problem usually asks what's reachable *within* i transitions. 
  // Initial state is reachable within 0...
  reachable[init_val] = true;

  cout << "Calculating cumulative reachable states for " << vfile << " from k=1 to " << max_k << "\n";
  cout << "State bits: " << n << " (Total possible states: " << total_states << ")\n\n";
  cout << "k\tNew\tCumulative\tTime(s)\n";
  cout << "---------------------------------------\n";

  string tmp_dimacs = "temp_partc.dimacs";
  string tmp_sat = "temp_partc.sat";

  for (int k = 1; k <= max_k; k++) {
      auto t_start = chrono::high_resolution_clock::now();
      
      // 1. Build base CNF for k transitions WITHOUT target state
      CNF base_cnf;
      VarMap vm;
      auto var = [&](const string& node, int t)->int { return vm.get(node, t); };

      for (int t = 0; t < k; t++) {
        for (auto &sr : state_regs) (void)var(sr, t);
        for (auto &in : nl.inputs)  (void)var(in, t);

        for (const auto &g : nl.gates) {
          int y = var(g.out, t);
          vector<int> xs;
          for (auto &iname : g.in) xs.push_back(var(iname, t));

          if (g.type == "not") {
            add_not(base_cnf, y, xs[0]);
          } else if (g.type == "and") {
            add_and(base_cnf, y, xs);
          }
        }

        for (size_t i = 0; i < nl.state_updates.size(); i++) {
          int s_next = var(nl.state_updates[i].first, t+1);
          int ns_now = var(nl.state_updates[i].second, t);
          add_equiv(base_cnf, s_next, ns_now);
        }
      }

      // Constrain initial state
      for (int i = 0; i < n; i++) {
        char b = init_bits[i];
        int v = var(state_regs[i], 0);
        if (b == '1') base_cnf.add_clause({ v});
        else if (b == '0') base_cnf.add_clause({-v});
      }

      base_cnf.nvars = vm.next_id - 1;
      
      // Identify the variables for the target state at timeframe k
      vector<int> target_vars(n);
      for (int i = 0; i < n; i++) {
          target_vars[i] = var(state_regs[i], k);
      }

      // 2. Loop through all 2^N states to check reachability
      int newly_reached = 0;

      for (int s = 0; s < total_states; s++) {
          // Optimization: if it's already reachable, we don't need to check it again
          // since Part C asks for CUMULATIVE reachable states within i transitions.
          if (reachable[s]) continue;

          // It's not reachable yet. Let's dump the DIMACS and append the unit clauses for this state.
          ofstream fout(tmp_dimacs.c_str());
          
          // Notice we add 'n' extra clauses (one for each state bit)
          fout << "p cnf " << base_cnf.nvars << " " << base_cnf.clauses.size() + n << "\n";
          
          for (auto &cl : base_cnf.clauses) {
            for (int lit : cl) fout << lit << " ";
            fout << "0\n";
          }
          
          // Append target clauses
          for (int i = 0; i < n; i++) {
              int bit_val = (s >> (n - 1 - i)) & 1;
              int v = target_vars[i];
              if (bit_val == 1) fout << v << " 0\n";
              else fout << -v << " 0\n";
          }
          fout.close();

          // Run minisat
          string cmd = "minisat " + tmp_dimacs + " " + tmp_sat + " > /dev/null 2>&1";
          int rc = system(cmd.c_str());

          // Read result
          bool is_sat = false;
          ifstream fsat(tmp_sat.c_str());
          string l;
          while(getline(fsat, l)) {
              if (l.find("SAT") != string::npos && l.find("UNSAT") == string::npos) { 
                 is_sat = true; break; 
              }
              if (l.find("UNSAT") != string::npos) { 
                 is_sat = false; break; 
              }
          }
          fsat.close();

          if (is_sat) {
              reachable[s] = true;
              newly_reached++;
          }
      }

      auto t_end = chrono::high_resolution_clock::now();
      chrono::duration<double> diff = t_end - t_start;

      // Calculate cumulative
      int cumulative = 0;
      for (int s = 0; s < total_states; s++) {
          if (reachable[s]) cumulative++;
      }

      cout << k << "\t" << newly_reached << "\t" << cumulative << "\t\t" << diff.count() << "\n";
  }

  // Cleanup temp files
  system("rm -f temp_partc.dimacs temp_partc.sat");

  cout << "\nDone! Total reachable states cumulatively up to k=" << max_k << " is: ";
  int final_cumulative = 0;
  for (int s = 0; s < total_states; s++) {
      if (reachable[s]) final_cumulative++;
  }
  cout << final_cumulative << "\n";

  return 0;
}

