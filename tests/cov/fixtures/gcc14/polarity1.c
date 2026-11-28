/* Each function is called once, so each condition has exactly one real value. */
int g(int v) { return v; }
int n1(int a) { if (!a) return 1; return 0; }
int n2(int a) { if (!!a) return 1; return 0; }
int n3(int a) { if (!!!a) return 1; return 0; }
int and_not(int a, int b) { if (a && !b) return 1; return 0; }
int or_not(int a, int b) { if (a || !b) return 1; return 0; }
int not_and(int a, int b) { if (!(a && b)) return 1; return 0; }
int not_or(int a, int b) { if (!(a || b)) return 1; return 0; }
int not_and_not(int a, int b) { if (!(!a && !b)) return 1; return 0; }
int value_not_and(int a, int b) { return !(a && b); }
int value_and_not(int a, int b) { return a && !b; }
int value_arg_not(int a, int b) { return g(!a && b); }
int eq0(int a, int b) { if (a == 0 && b != 0) return 1; return 0; }
int tern_not(int a) { return !a ? 7 : g(9); }
int loop_not(int a) { int n = 0; while (!a) { n++; a = 1; } return n; }
int nested(int a, int b, int c) { if (a && !(b || !c)) return 1; return 0; }
int cmp_not(int a, int b) { if (!(a > 0) && b) return 1; return 0; }
int ptr_not(int *p, int b) { if (!p || b) return 1; return 0; }
int main(void) {
    n1(0); n2(1); n3(0);
    and_not(1, 0); or_not(0, 1); not_and(1, 1); not_or(0, 0); not_and_not(0, 0);
    value_not_and(1, 1); value_and_not(1, 0); value_arg_not(0, 1);
    eq0(0, 1); tern_not(0); loop_not(0); nested(1, 0, 1); cmp_not(0, 1); ptr_not(0, 0);
    return 0;
}
