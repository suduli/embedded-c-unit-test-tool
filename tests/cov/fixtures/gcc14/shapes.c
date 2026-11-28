int g(int);
int single(int a) { if (a) return 1; return 0; }
int notand(int a, int b) { if (!(a && b)) return 1; return 0; }
int arg(int a, int b) { return g(a && b); }
int tern1(int a) { return a ? 2 : 3; }
int ternand(int a, int b) { return (a && b) ? 2 : 3; }
int loops(int a, int b) { int n = 0; while (a && n < b) n++; for (; n > 0 && b; n--) ; do n++; while (n < 3 && a); return n; }
int mixed(int a, int b, int c) { int x = (a && b) || c; return x; }
int cmp(int a, int b) { if (a > 0 && b < 3) return 1; return 0; }
int multi(int a, int b,
          int c) {
  if (a &&
      (b ||
       c))
    return 1;
  return 0;
}
int konst(int a) { if (a && 1) return 1; if (a || 0) return 2; return 0; }
int innerarg(int a, int b, int c) { if (a && g(b || c)) return 1; return 0; }
int plainassign(int a) { int x = !a; int y = a > 3; return x + y; }
int condret(int a, int b) { return (a > 0) && (b > 0); }
int twoline(int a, int b, int c, int d) { if (a && b) return 1; if (c || d) return 2; return 0; } 
int g(int v) { return v; }
int main(void) { single(1); notand(1,1); arg(1,0); tern1(1); ternand(1,1); loops(1,3); mixed(1,0,0); cmp(1,1); multi(1,0,0); konst(1); innerarg(1,0,0); plainassign(1); condret(1,0); twoline(1,0,0,0); return 0; }
