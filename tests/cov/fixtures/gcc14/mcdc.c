#define BOTH(x, y) ((x) && (y))
static int and2(int a, int b) { if (a && b) { return 1; } return 0; }
static int nested(int a, int b, int c) { if (a && (b || c)) { return 1; } return 0; }
static int repeated(int a, int b) { if ((a && b) || (a && !b)) { return 1; } return 0; }
static int bump(int *n) { *n += 1; return 1; }
static int side(int a, int *n) { if (a && bump(n)) { return 1; } return 0; }
static int macro(int a, int b) { if (BOTH(a, b)) { return 1; } return 0; }
static int constant(void) { if (0) { return 1; } return 0; }
static int unused(int a, int b) { return a || b; }
int main(void) {
    int n = 0;
    and2(1, 1); and2(0, 1);
    nested(1, 0, 1); nested(0, 0, 0);
    repeated(1, 1);
    side(1, &n); side(0, &n);
    macro(1, 0);
    constant();
    return (int)(sizeof(&unused) == 0);
}
