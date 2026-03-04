#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <array>
#include <chrono>
#include <cstdlib>
#include <algorithm>

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
  if (argc != 5) {
    cerr << "Usage: " << argv[0] << " <verilog_file> <target_state_bitstring> <unroll_depth> <solver>\n";
    return 1;
  }

  string vfile = argv[1];
  string target = argv[2];
  int k = atoi(argv[3]);
  string solver = argv[4];

  if (k < 0) { cerr << "ERROR: unroll_depth must be >= 0\n"; return 1; }
  string init_bits(target.size(), '0');

  Netlist nl = parse_verilog_structural(vfile);

  vector<string> state_regs;
  for (auto &p : nl.state_updates) {
    state_regs.push_back(p.first);
  }

  if ((int)state_regs.size() == 0) {
    cerr << "ERROR: no state regs found.\n";
    return 1;
  }

  if ((int)target.size() != (int)state_regs.size()) {
    cerr << "ERROR: target size mismatch.\n";
    return 1;
  }

  string dimacs_path = "out.dimacs";
  string sat_path = "out.sat";

  CNF cnf;
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
        add_not(cnf, y, xs[0]);
      } else if (g.type == "and") {
        add_and(cnf, y, xs);
      }
    }

    for (size_t i = 0; i < nl.state_updates.size(); i++) {
      int s_next = var(nl.state_updates[i].first, t+1);
      int ns_now = var(nl.state_updates[i].second, t);
      add_equiv(cnf, s_next, ns_now);
    }
  }

  for (int i = 0; i < (int)state_regs.size(); i++) {
    char b = target[i];
    int v = var(state_regs[i], k);
    if (b == '1') cnf.add_clause({ v});
    else if (b == '0') cnf.add_clause({-v});
  }
  
  for (int i = 0; i < (int)state_regs.size(); i++) {
    char b = init_bits[i];
    int v = var(state_regs[i], 0);
    if (b == '1') cnf.add_clause({ v});
    else if (b == '0') cnf.add_clause({-v});
  }

  cnf.nvars = vm.next_id - 1;

  {
    ofstream fout("out.nodes");
    for (int id = 1; id <= cnf.nvars; id++) {
      auto &p = vm.id2node[id];
      fout << id << ":" << p.first << "," << p.second << "\n";
    }
  }

  {
    ofstream fout(dimacs_path.c_str());
    fout << "p cnf " << cnf.nvars << " " << cnf.clauses.size() << "\n";
    for (auto &cl : cnf.clauses) {
      for (int lit : cl) fout << lit << " ";
      fout << "0\n";
    }
  }

  auto t1 = std::chrono::high_resolution_clock::now();
  int rc = 0;
  if (solver == "minisat") {
      string cmd = "minisat " + dimacs_path + " " + sat_path + " > /dev/null 2>&1";
      rc = system(cmd.c_str());
  } else if (solver == "picosat") {
      string cmd = "picosat " + dimacs_path + " > " + sat_path + " 2> /dev/null";
      rc = system(cmd.c_str());
  } else {
      cerr << "ERROR: Unknown solver " << solver << "\n";
      return 1;
  }
  auto t2 = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> diff = t2 - t1;

  bool is_sat = false;
  ifstream satpf(sat_path.c_str());
  string l;
  while(getline(satpf, l)) {
      if (l.find("SAT") != string::npos && l.find("UNSAT") == string::npos) { 
         is_sat = true; break; 
      }
      if (l.find("UNSAT") != string::npos) { 
         is_sat = false; break; 
      }
  }

  if (is_sat) cout << "SAT\n";
  else cout << "UNSAT\n";
  cout << "Runtime: " << diff.count() << "s\n";

  return 0;
}
