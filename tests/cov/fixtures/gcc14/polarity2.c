/* Every function is called with a = 1 (and b = 1) exactly once. */
int g(int v) { return v; }
int if_else_not(int a) { int r; if (!a) r = g(1); else r = g(2); return r; }
int if_empty_then(int a) { int r = 0; if (!a) { } else r = g(2); return r; }
int while_not(int a) { int n = 0; while (!a) { n++; break; } return n; }
int do_not(int a) { int n = 0; do n++; while (!a && n < 3); return n; }
int for_not(int a) { int n = 0; for (; !a; ) { n++; break; } return n; }
int tern_const(int a) { return !a ? 1 : 2; }
int tern_call(int a) { return !a ? g(1) : g(2); }
int tern_and(int a, int b) { return !(a && b) ? g(1) : g(2); }
int tern_and_not(int a, int b) { return (a && !b) ? g(1) : g(2); }
int tern_plain(int a) { return a ? g(1) : g(2); }
int if_eq_zero(int a) { if (a == 0) return g(1); return g(2); }
int if_ne_zero(int a) { if (a != 0) return g(1); return g(2); }
int not_eq(int a) { if (!(a == 0)) return g(1); return g(2); }
int cast_not(int a) { if ((int)!a) return g(1); return g(2); }
int not_cast(int a) { if (!(long)a) return g(1); return g(2); }
int comma_not(int a, int b) { if ((b, !a)) return g(1); return g(2); }
int not_not_and(int a, int b) { if (!!(a && b)) return g(1); return g(2); }
int main(void) {
    if_else_not(1); if_empty_then(1); while_not(1); do_not(1); for_not(1);
    tern_const(1); tern_call(1); tern_and(1, 1); tern_and_not(1, 1); tern_plain(1);
    if_eq_zero(1); if_ne_zero(1); not_eq(1); cast_not(1); not_cast(1); comma_not(1, 1); not_not_and(1, 1);
    return 0;
}
