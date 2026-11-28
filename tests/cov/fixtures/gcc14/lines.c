#define BOTH(x,y) ((x) && (y))
#define IF if
int ifsplit(int a, int b) {
  if (
      a &&
      b)
    return 1;
  return 0;
}
int retsplit(int a, int b) {
  return a
      && b;
}
int tsplit(int a) {
  int x =
      a
      ? 1 : 2;
  return x;
}
int mac(int a, int b) { return BOTH(a, b); }
int forsplit(int n) {
  int i;
  for (i = 0;
       i < n;
       i++) ;
  return i;
}
int sw(int a) { switch (a) { case 1: return 2; default: return 3; } }
int gnu(int a) { return a ?: 5; }
int szof(int a, int b) { return (int)sizeof(a && b); }
int comma(int a, int b) { if ((a, b)) return 1; return 0; }
int doubleneg(int a) { if (!!a) return 1; return 0; }
int castbool(int a, int b) { if ((_Bool)(a && b)) return 1; return 0; }
int cmpbool(int a, int b) { if ((a && b) == 0) return 1; return 0; }
int main(void) { ifsplit(1,0); retsplit(1,0); tsplit(1); mac(1,1); forsplit(2); sw(1); gnu(0); comma(1,1); doubleneg(1); castbool(1,1); cmpbool(1,1); return 0; }
