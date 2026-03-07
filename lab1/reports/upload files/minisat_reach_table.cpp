#include <cstdio>
#include <cstdlib>
#include <cstring>

// i: 0..20, t: 0..511
static unsigned char sat_tbl[21][512];

static int minisat_is_sat(const char* path) {
    char cmd[1024];
    std::snprintf(cmd, sizeof(cmd), "minisat \"%s\" 2>/dev/null", path);

    FILE* p = popen(cmd, "r");
    if (!p) return 0;

    char line[512];
    int saw_sat = 0;
    int saw_unsat = 0;

    while (fgets(line, sizeof(line), p)) {
        if (strstr(line, "UNSATISFIABLE")) saw_unsat = 1;
        else if (strstr(line, "SATISFIABLE")) saw_sat = 1;
    }
    pclose(p);

    if (saw_unsat) return 0;
    if (saw_sat) return 1;
    return 0;
}

static int bin9_to_int(const char* bits) {
    int x = 0;
    for (int k = 0; bits[k]; k++) {
        if (bits[k] != '0' && bits[k] != '1') return -1;
        x = (x << 1) | (bits[k] - '0');
    }
    return x;
}

static void int_to_bin9(int v, char out[10]) {
    out[9] = 0;
    for (int k = 8; k >= 0; k--) {
        out[k] = (v & 1) ? '1' : '0';
        v >>= 1;
    }
}

int main(int argc, char** argv) {
    const char* dir = (argc >= 2) ? argv[1] : "out_partc_dimacs";
    int i_min = (argc >= 3) ? atoi(argv[2]) : 0;
    int i_max = (argc >= 4) ? atoi(argv[3]) : 20;

    if (i_min < 0) i_min = 0;
    if (i_max > 20) i_max = 20;
    if (i_min > i_max) { int tmp=i_min; i_min=i_max; i_max=tmp; }

    // list files
    char lscmd[1024];
    std::snprintf(lscmd, sizeof(lscmd), "ls %s/base_*_target_*.dimacs 2>/dev/null", dir);

    FILE* ls = popen(lscmd, "r");
    if (!ls) {
        std::fprintf(stderr, "ERROR: could not list dimacs files in %s\n", dir);
        return 1;
    }

    char path[1024];
    while (fgets(path, sizeof(path), ls)) {
        // strip newline
        size_t n = std::strlen(path);
        while (n && (path[n-1] == '\n' || path[n-1] == '\r')) path[--n] = 0;

        // find "base_" inside the path
        const char* pbase = std::strstr(path, "base_");
        if (!pbase) continue;

        int i = -1;
        char bits[64] = {0};

        // parse: base_<i>_target_<bits>.dimacs
        if (std::sscanf(pbase, "base_%d_target_%[^.].dimacs", &i, bits) != 2) continue;
        if (i < i_min || i > i_max) continue;

        int t = bin9_to_int(bits);
        if (t < 0 || t > 511) continue;

        if (minisat_is_sat(path)) sat_tbl[i][t] = 1;
    }
    pclose(ls);

    // print all SAT targets per i
    std::printf("Reachability table (SAT targets)\n");
    std::printf("dir=%s, i=%d..%d\n\n", dir, i_min, i_max);

    for (int i = i_min; i <= i_max; i++) {
        int count = 0;
        for (int t = 0; t <= 511; t++) if (sat_tbl[i][t]) count++;

        std::printf("i=%d  SAT=%d/512\n", i, count);

        if (count == 0) {
            std::printf("  (none)\n\n");
            continue;
        }

        // print in rows (8 per line)
        int per_line = 8;
        int printed = 0;
        for (int t = 0; t <= 511; t++) {
            if (!sat_tbl[i][t]) continue;

            char b[10];
            int_to_bin9(t, b);

            if (printed % per_line == 0) std::printf("  ");
            std::printf("%s", b);
            printed++;

            if (printed % per_line == 0) std::printf("\n");
            else std::printf("  ");
        }
        if (printed % per_line != 0) std::printf("\n");
        std::printf("\n");
    }

    return 0;
}
