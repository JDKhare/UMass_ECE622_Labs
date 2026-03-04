#include <bits/stdc++.h>
using namespace std;

/*
  add_target_clause.cpp

  Usage:
    ./add_target_clause --base base_1.txt --nodes nodes_1.txt --k 1 --n 9 --target 010011001 --outdir out

  What it does:
    - Parses nodes file lines like:  1:S8,0
      meaning var_id=1, name=S8, time=0
    - For j in [0..n-1], looks for node name "NS<idx>" at time=k
      where idx = (n-1-j) if target string is MSB..LSB.
      Example target="010" with n=3 maps:
        target[0] -> NS2
        target[1] -> NS1
        target[2] -> NS0
    - Appends a SINGLE clause line with n literals matching target bits.
    - Updates "p cnf V C" clause count C -> C+1 (V unchanged).
*/

static inline string trim(const string &s) {
    size_t b = s.find_first_not_of(" \t\r\n");
    if (b == string::npos) return "";
    size_t e = s.find_last_not_of(" \t\r\n");
    return s.substr(b, e - b + 1);
}

struct Args {
    string base_path;
    string nodes_path;
    int k = -1;
    int n = -1;
    string target;
    string outdir = ".";
};

static void die(const string &msg) {
    cerr << "ERROR: " << msg << "\n";
    exit(1);
}

static Args parse_args(int argc, char** argv) {
    Args a;
    for (int i = 1; i < argc; i++) {
        string s = argv[i];
        auto need = [&](const string &flag) {
            if (i + 1 >= argc) die("Missing value for " + flag);
            return string(argv[++i]);
        };
        if (s == "--base") a.base_path = need("--base");
        else if (s == "--nodes") a.nodes_path = need("--nodes");
        else if (s == "--k") a.k = stoi(need("--k"));
        else if (s == "--n") a.n = stoi(need("--n"));
        else if (s == "--target") a.target = need("--target");
        else if (s == "--outdir") a.outdir = need("--outdir");
        else die("Unknown arg: " + s);
    }
    if (a.base_path.empty()) die("Provide --base <base_i.txt>");
    if (a.nodes_path.empty()) die("Provide --nodes <nodes_i.txt>");
    if (a.k < 0) die("Provide --k <unroll k> (target time index)");
    if (a.n <= 0) die("Provide --n <num_state_bits>");
    if ((int)a.target.size() != a.n) die("--target length must equal --n");
    for (char c : a.target) if (c != '0' && c != '1') die("--target must be a 0/1 bitstring");
    return a;
}

// Key: (name, time) -> var id
static unordered_map<string, int> parse_nodes(const string &nodes_path) {
    ifstream in(nodes_path);
    if (!in) die("Cannot open nodes file: " + nodes_path);

    unordered_map<string, int> mp;
    string line;
    while (getline(in, line)) {
        line = trim(line);
        if (line.empty()) continue;

        // Expect: <id>:<name>,<time>
        // Example: 1:S8,0
        size_t colon = line.find(':');
        size_t comma = line.rfind(',');
        if (colon == string::npos || comma == string::npos || comma < colon) {
            // ignore malformed lines rather than hard-fail
            continue;
        }

        string id_s = trim(line.substr(0, colon));
        string name = trim(line.substr(colon + 1, comma - (colon + 1)));
        string time_s = trim(line.substr(comma + 1));

        if (id_s.empty() || name.empty() || time_s.empty()) continue;

        int id = -1, t = -1;
        try {
            id = stoi(id_s);
            t = stoi(time_s);
        } catch (...) {
            continue;
        }

        // store key as "name,time"
        string key = name + "," + to_string(t);
        mp[key] = id;
    }
    return mp;
}

static vector<string> read_all_lines(const string &path) {
    ifstream in(path);
    if (!in) die("Cannot open file: " + path);
    vector<string> lines;
    string line;
    while (getline(in, line)) lines.push_back(line);
    return lines;
}

static void write_all_lines(const string &path, const vector<string> &lines) {
    ofstream out(path);
    if (!out) die("Cannot write file: " + path);
    for (auto &l : lines) out << l << "\n";
}

static bool parse_dimacs_header(const string &line, int &vars, int &clauses) {
    // "p cnf 238 556"
    // allow extra whitespace
    string s = trim(line);
    if (s.size() < 5) return false;
    if (s.rfind("p", 0) != 0) return false;

    istringstream iss(s);
    string p, cnf;
    if (!(iss >> p >> cnf >> vars >> clauses)) return false;
    if (p != "p" || cnf != "cnf") return false;
    return true;
}

// Customize node naming here if needed
static string ns_name_for_index(int idx) {
    // default assumes nodes are named like: NS8, NS7, ..., NS0
    return "NS" + to_string(idx);
}

int main(int argc, char** argv) {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    Args args = parse_args(argc, argv);

    auto nodes = parse_nodes(args.nodes_path);
    auto base_lines = read_all_lines(args.base_path);

    // Find and update header line
    int header_vars = -1, header_clauses = -1;
    int header_line_idx = -1;
    for (int i = 0; i < (int)base_lines.size(); i++) {
        int v, c;
        if (parse_dimacs_header(base_lines[i], v, c)) {
            header_vars = v;
            header_clauses = c;
            header_line_idx = i;
            break;
        }
    }
    if (header_line_idx < 0) die("DIMACS header 'p cnf V C' not found in base file");

    // Build target clause (single line)
    // target string is MSB..LSB, and we map:
    // target[0] -> NS(n-1)
    // target[n-1] -> NS0
    vector<int> lits;
    lits.reserve(args.n);

    for (int j = 0; j < args.n; j++) {
        int bit_index = args.n - 1 - j; // NS index
        char bit = args.target[j];

        string node_name = ns_name_for_index(bit_index);
        string key = node_name + "," + to_string(args.k);

        auto it = nodes.find(key);
        if (it == nodes.end()) {
            die("Missing node mapping for " + node_name + " at time k=" + to_string(args.k) +
                " (expected key '" + key + "') in nodes file");
        }
        int var_id = it->second;

        // If target bit is 1: literal is +var
        // If target bit is 0: literal is -var
        int lit = (bit == '1') ? var_id : -var_id;
        lits.push_back(lit);
    }

    // Format clause line
    ostringstream clause;
    for (int lit : lits) clause << lit << " ";
    clause << "0";

    // Update header clause count
    header_clauses += 1;
    {
        ostringstream new_header;
        new_header << "p cnf " << header_vars << " " << header_clauses;
        base_lines[header_line_idx] = new_header.str();
    }

    // Append clause at end
    base_lines.push_back(clause.str());

    // Output name includes target bitstring
    // base_1.txt -> base_1_target_0101... .dimacs (or .cnf)
    string base_name = args.base_path;
    // strip directory
    size_t slash = base_name.find_last_of("/\\");
    if (slash != string::npos) base_name = base_name.substr(slash + 1);

    // strip extension
    string stem = base_name;
    size_t dot = stem.find_last_of('.');
    if (dot != string::npos) stem = stem.substr(0, dot);

    // ensure outdir has no trailing slash issues
    string outdir = args.outdir;
    if (!outdir.empty() && (outdir.back() == '/' || outdir.back() == '\\')) outdir.pop_back();

    string out_path = outdir + "/" + stem + "_target_" + args.target + ".dimacs";

    write_all_lines(out_path, base_lines);

    cerr << "Wrote: " << out_path << "\n";
    cerr << "Appended target clause: " << clause.str() << "\n";
   return 0;
}
