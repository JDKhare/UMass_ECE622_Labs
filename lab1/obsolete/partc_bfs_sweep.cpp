#include <bits/stdc++.h>
using namespace std;

// minisat runner
static string run_capture(const string &cmd) {
    array<char, 4096> buf{};
    string out;
    FILE *p = popen(cmd.c_str(), "r");
    if (!p) return "";
    while (fgets(buf.data(), (int)buf.size(), p)) out += buf.data();
    pclose(p);
    return out;
}

static bool minisat_is_sat(const string &minisat_cmd, const string &cnf_path) {
    string cmd = minisat_cmd + " -verb=0 " + cnf_path + " /dev/null 2>&1";
    string out = run_capture(cmd);
    if (out.find("UNSAT") != string::npos) return false;
    if (out.find("SAT") != string::npos)   return true;
    return false; // conservative
}

// Read DIMACS header p cnf V C
static bool read_dimacs_header(const string &path, int &vars, int &clauses) {
    ifstream in(path);
    if (!in) return false;
    string line;
    while (getline(in, line)) {
        if (!line.empty() && line[0] == 'p') {
            string p, cnf;
            stringstream ss(line);
            ss >> p >> cnf >> vars >> clauses;
            return true;
        }
    }
    return false;
}

// Copy base CNF to temp and append unit clauses, fixing header clause count.
static bool write_dimacs_with_units(const string &base_path,
                                   const string &out_path,
                                   const vector<int> &unit_lits) {
    int vars = 0, clauses = 0;
    if (!read_dimacs_header(base_path, vars, clauses)) return false;

    ifstream in(base_path);
    ofstream out(out_path);
    if (!in || !out) return false;

    string line;
    bool header_done = false;
    while (getline(in, line)) {
        if (!header_done && !line.empty() && line[0] == 'p') {
            out << "p cnf " << vars << " " << (clauses + (int)unit_lits.size()) << "\n";
            header_done = true;
        } else {
            out << line << "\n";
        }
    }

    for (int lit : unit_lits) out << lit << " 0\n";
    return true;
}

// Parse your nodes format: "<varID>:<name>,<time>"
//
// Example:
//   17:S1,2
// stores mp["S1"][2] = 17
static bool load_nodes(const string &nodes_path,
                       unordered_map<string, unordered_map<int,int>> &mp) {
    ifstream in(nodes_path);
    if (!in) return false;
    string line;
    bool any = false;
    while (getline(in, line)) {
        if (line.empty()) continue;

        // split at ':'
        auto cpos = line.find(':');
        if (cpos == string::npos) continue;
        string a = line.substr(0, cpos);
        string rest = line.substr(cpos + 1);

        // split rest at ','
        auto comma = rest.find(',');
        if (comma == string::npos) continue;
        string name = rest.substr(0, comma);
        string tstr = rest.substr(comma + 1);

        // trim whitespace
        auto trim = [](string s){
            size_t b = s.find_first_not_of(" \t\r\n");
            size_t e = s.find_last_not_of(" \t\r\n");
            if (b == string::npos) return string("");
            return s.substr(b, e-b+1);
        };
        a = trim(a); name = trim(name); tstr = trim(tstr);
        if (a.empty() || name.empty() || tstr.empty()) continue;

        int var = 0, t = 0;
        try {
            var = stoi(a);
            t   = stoi(tstr);
        } catch(...) { continue; }

        mp[name][t] = var;
        any = true;
    }
    return any;
}

static string bitstring_msb(uint64_t x, int nbits) {
    string s;
    s.reserve(nbits);
    for (int i = nbits - 1; i >= 0; --i) s.push_back(((x >> i) & 1ULL) ? '1' : '0');
    return s;
}

static void usage(const char *argv0) {
    cerr <<
    "Usage:\n"
    "  " << argv0 << " --dir <folder> --nbits N --imax 20 [--minisat minisat] [--matrix]\n\n"
    "Folder must contain:\n"
    "  base_1.dimacs ... base_imax.dimacs\n"
    "  nodes_1.txt   ... nodes_imax.txt   (format: varID:name,time)\n";
}

int main(int argc, char **argv) {
    string dir, minisat_cmd = "minisat";
    int nbits = -1, imax = 20;
    bool matrix = false;

    for (int i = 1; i < argc; i++) {
        string a = argv[i];
        auto need = [&](const string &flag) {
            if (i + 1 >= argc) { cerr << "Missing value after " << flag << "\n"; exit(2); }
            return string(argv[++i]);
        };
        if (a == "--dir") dir = need("--dir");
        else if (a == "--nbits") nbits = stoi(need("--nbits"));
        else if (a == "--imax") imax = stoi(need("--imax"));
        else if (a == "--minisat") minisat_cmd = need("--minisat");
        else if (a == "--matrix") matrix = true;
        else if (a == "-h" || a == "--help") { usage(argv[0]); return 0; }
        else { cerr << "Unknown arg: " << a << "\n"; usage(argv[0]); return 2; }
    }

    if (dir.empty() || nbits <= 0) { usage(argv[0]); return 2; }
    if (nbits > 20) { cerr << "nbits too large for brute-force sweep.\n"; return 2; }

    uint64_t nstates = 1ULL << nbits;
    vector<vector<uint8_t>> sat(imax + 1, vector<uint8_t>(nstates, 0));
    unordered_set<uint64_t> cum;
    cum.reserve((size_t)nstates);

    // Determine state reg names in MSB->LSB order: S(n-1) ... S0
    vector<string> sname(nbits);
    for (int b = 0; b < nbits; b++) sname[b] = "S" + to_string(nbits - 1 - b); // b=0 is MSB

    for (int k = 1; k <= imax; k++) {
        string base = dir + "/base_" + to_string(k) + ".dimacs";
        string nodes = dir + "/nodes_" + to_string(k) + ".txt";

        unordered_map<string, unordered_map<int,int>> mp;
        if (!load_nodes(nodes, mp)) {
            cerr << "Could not load nodes mapping from: " << nodes << "\n";
            cerr << "Expected lines like: 17:S1,2\n";
            return 2;
        }

        // For each target state, append clauses that constrain S* at time k
        for (uint64_t t = 0; t < nstates; t++) {
            vector<int> units;
            units.reserve((size_t)nbits);

            // Build unit clauses in MSB->LSB order, matching your CLI convention.
            // sname[0] = S(n-1), sname[nbits-1] = S0
            for (int b = 0; b < nbits; b++) {
                const string &nm = sname[b];
                auto it1 = mp.find(nm);
                if (it1 == mp.end() || it1->second.find(k) == it1->second.end()) {
                    cerr << "Missing mapping for " << nm << " at time " << k << " in " << nodes << "\n";
                    return 2;
                }
                int var = it1->second[k];

                // MSB-first bitstring: bit b corresponds to (nbits-1-b) in integer
                bool bit_is_1 = ((t >> (nbits - 1 - b)) & 1ULL) != 0ULL;
                units.push_back(bit_is_1 ? var : -var);
            }

            string tmp = "/tmp//tmp_query.dimacs";
            if (!write_dimacs_with_units(base, tmp, units)) {
                cerr << "Failed to write temp CNF from base: " << base << "\n";
                return 2;
            }

            bool is_sat = minisat_is_sat(minisat_cmd, tmp);
            sat[k][t] = is_sat ? 1 : 0;
        }
    }

    // Print Part C.1 table: cumulative reachable within i
    cout << "nbits=" << nbits << " total_states=" << nstates << "\n\n";
    cout << left << setw(4) << "i"
         << setw(22) << "reachable_exactly_i"
         << setw(24) << "reachable_within_i"
         << "\n";
    cout << string(4 + 22 + 24, '-') << "\n";

    cum.clear();
    for (int k = 1; k <= imax; k++) {
        uint64_t exact = 0;
        for (uint64_t t = 0; t < nstates; t++) {
            if (sat[k][t]) { exact++; cum.insert(t); }
        }
        cout << left << setw(4) << k
             << setw(22) << exact
             << setw(24) << cum.size()
             << "\n";
    }

    if (matrix) {
        cout << "\nMatrix (rows=i, cols=targets in MSB->LSB order, 1=SAT 0=UNSAT)\n";
        cout << "i\\t ";
        for (uint64_t t = 0; t < nstates; t++) cout << bitstring_msb(t, nbits) << " ";
        cout << "\n";
        for (int k = 1; k <= imax; k++) {
            cout << setw(4) << k << " ";
            for (uint64_t t = 0; t < nstates; t++) cout << int(sat[k][t]) << " ";
            cout << "\n";
        }
    }

    return 0;
}
