// Octilinear A* kernel for the R10 signal design aid. Reads a binary job on stdin, writes the path on stdout.
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { float f; int32_t s; } HN;
static HN *heap; static int hn, hcap;
static void hpush(float f, int32_t s) {
    if (hn == hcap) { hcap = hcap ? hcap * 2 : 1 << 16; heap = realloc(heap, sizeof(HN) * hcap); }
    int i = hn++; heap[i].f = f; heap[i].s = s;
    while (i) { int p = (i - 1) / 2; if (heap[p].f <= heap[i].f) break; HN t = heap[p]; heap[p] = heap[i]; heap[i] = t; i = p; }
}
static HN hpop(void) {
    HN r = heap[0]; heap[0] = heap[--hn]; int i = 0;
    for (;;) { int l = 2 * i + 1, rr = l + 1, m = i;
        if (l < hn && heap[l].f < heap[m].f) m = l; if (rr < hn && heap[rr].f < heap[m].f) m = rr;
        if (m == i) break; HN t = heap[m]; heap[m] = heap[i]; heap[i] = t; i = m; }
    return r;
}

static int DX[8] = {1, 1, 0, -1, -1, -1, 0, 1}, DY[8] = {0, -1, -1, -1, 0, 1, 1, 1};
// job
static int NX, NY;                 // crop size (global cells)
static double CX0, CY0, GR;        // crop origin (mm of cell 0,0) and global resolution
static uint8_t *TF[2], *VF;        // track-free per layer, via-free
static float *EX[2], *VEX;         // congestion extra per unit length, via extra
static double SX, SY, GX, GY, R, T45, T90, VIAC, MINRUN, MINEND;
static int SL, GL, MAXEXP;         // layer bitmasks

static int cell(double x, double y, int *ci, int *cj) {
    int i = (int)lround((x - CX0) / GR), j = (int)lround((y - CY0) / GR);
    if (i < 0 || j < 0 || i >= NX || j >= NY) return 0;
    *ci = i; *cj = j; return 1;
}
static int tfree(int l, double x, double y) { int i, j; if (!cell(x, y, &i, &j)) return 0; return TF[l][j * NX + i]; }
static int vfree(double x, double y) { int i, j; if (!cell(x, y, &i, &j)) return 0; return VF[j * NX + i]; }
static float tex(int l, double x, double y) { int i, j; if (!cell(x, y, &i, &j)) return 0; return EX[l][j * NX + i]; }
static float vex(double x, double y) { int i, j; if (!cell(x, y, &i, &j)) return 0; return VEX[j * NX + i]; }
static int segfree(int l, double ax, double ay, double bx, double by) {
    double L = hypot(bx - ax, by - ay); int n = (int)(L / (GR / 2)); if (n < 1) n = 1;
    for (int k = 0; k <= n; k++) if (!tfree(l, ax + (bx - ax) * k / n, ay + (by - ay) * k / n)) return 0;
    return 1;
}

int main(void) {
    int hdr[6]; double dh[16];
    if (fread(hdr, sizeof(int), 6, stdin) != 6) return 2;
    NX = hdr[0]; NY = hdr[1]; SL = hdr[2]; GL = hdr[3]; MAXEXP = hdr[4];
    if (fread(dh, sizeof(double), 13, stdin) != 13) return 2;
    CX0 = dh[0]; CY0 = dh[1]; GR = dh[2]; SX = dh[3]; SY = dh[4]; GX = dh[5]; GY = dh[6];
    R = dh[7]; T45 = dh[8]; T90 = dh[9]; VIAC = dh[10]; MINRUN = dh[11]; MINEND = dh[12];
    size_t N = (size_t)NX * NY;
    for (int l = 0; l < 2; l++) { TF[l] = malloc(N); if (fread(TF[l], 1, N, stdin) != N) return 2; }
    VF = malloc(N); if (fread(VF, 1, N, stdin) != N) return 2;
    for (int l = 0; l < 2; l++) { EX[l] = malloc(N * 4); if (fread(EX[l], 4, N, stdin) != N) return 2; }
    VEX = malloc(N * 4); if (fread(VEX, 4, N, stdin) != N) return 2;
    // local grid: i in [ilo, ihi] around start, covering the crop
    int ilo = (int)floor((CX0 - SX) / R), ihi = (int)ceil((CX0 + (NX - 1) * GR - SX) / R);
    int jlo = (int)floor((CY0 - SY) / R), jhi = (int)ceil((CY0 + (NY - 1) * GR - SY) / R);
    int NI = ihi - ilo + 1, NJ = jhi - jlo + 1;
    int MR = (int)ceil(MINRUN / R - 1e-9); if (MR < 1) MR = 1;
    int NR = MR + 1, ND = 9;
    size_t NS = (size_t)2 * NJ * NI * ND * NR;
    float *gb = malloc(NS * 4); int32_t *par = malloc(NS * 4);
    for (size_t k = 0; k < NS; k++) { gb[k] = 1e30f; par[k] = -1; }
#define SIDX(l, j, i, d, r) (((((size_t)(l) * NJ + (j)) * NI + (i)) * ND + (d)) * NR + (r))
    double s2 = sqrt(2.0);
    #define H(x, y) ({ double dx_ = fabs(GX - (x)), dy_ = fabs(GY - (y)); (dx_ > dy_ ? dx_ : dy_) + (s2 - 1) * (dx_ < dy_ ? dx_ : dy_); })
    int i0 = -ilo, j0 = -jlo;
    for (int l = 0; l < 2; l++) if (SL & (1 << l)) { size_t s = SIDX(l, j0, i0, 8, MR); gb[s] = 0; hpush((float)H(SX, SY), (int32_t)s); }
    long exp = 0;
    while (hn) {
        HN top = hpop(); size_t s = (size_t)top.s;
        int r = s % NR; size_t t = s / NR; int d = t % ND; t /= ND; int i = t % NI; t /= NI; int j = t % NJ; int l = (int)(t / NJ);
        double gc = gb[s];
        if (top.f > gc + H(SX + (i + ilo) * R, SY + (j + jlo) * R) + 1e-4) continue;
        if (++exp > MAXEXP) break;
        double x = SX + (i + ilo) * R, y = SY + (j + jlo) * R;
        // goal edges
        if (GL & (1 << l)) {
            for (int d1 = 0; d1 < 8; d1++) {
                if (d != 8 && d1 != d) continue;
                double ux = DX[d1], uy = DY[d1];
                int d2s[5] = {d1, (d1 + 1) % 8, (d1 + 7) % 8, (d1 + 2) % 8, (d1 + 6) % 8};
                for (int q = 0; q < 5; q++) {
                    int d2 = d2s[q]; double vx = DX[d2], vy = DY[d2];
                    double rx = GX - x, ry = GY - y, tt, uu;
                    if (d2 == d1) {
                        double cr = ux * ry - uy * rx; if (fabs(cr) > 1e-6) continue;
                        tt = (rx * ux + ry * uy) / (ux * ux + uy * uy); uu = 0; if (tt < -1e-9) continue;
                    } else {
                        double det = ux * vy - vx * uy; if (fabs(det) < 1e-12) continue;
                        tt = (rx * vy - vx * ry) / det; uu = (ux * ry - uy * rx) / det;
                        if (tt < -1e-9 || uu < -1e-9) continue;
                    }
                    double px = x + tt * ux, py = y + tt * uy, L1 = tt * hypot(ux, uy), L2 = uu * hypot(vx, vy);
                    if (d2 != d1) {
                        if (d != 8 && r * R + L1 < MINRUN - 1e-6) continue;
                        if (L2 > 1e-6 && L2 < MINEND) continue;
                    }
                    if (!segfree(l, x, y, px, py) || !segfree(l, px, py, GX, GY)) continue;
                    // emit path
                    int cnt = 0; size_t k = s; while (k != (size_t)-1 && (int32_t)k >= 0) { cnt++; if (par[k] < 0) break; k = (size_t)par[k]; }
                    printf("OK %d\n", cnt);
                    k = s;
                    for (;;) {
                        int rr = k % NR; size_t tq = k / NR; tq /= ND; int ii = tq % NI; tq /= NI; int jj = tq % NJ; int ll = (int)(tq / NJ); (void)rr;
                        printf("%.4f %.4f %d\n", SX + (ii + ilo) * R, SY + (jj + jlo) * R, ll);
                        if (par[k] < 0) break; k = (size_t)par[k];
                    }
                    printf("END %.4f %.4f %.4f %.4f %d %d\n", px, py, GX, GY, l, (L1 > 1e-6 && L2 > 1e-6) ? 1 : 0);
                    return 0;
                }
            }
        }
        // moves
        int cand[5]; int nc = 0;
        if (d == 8) { for (int k = 0; k < 8; k++) cand[nc++] = k; }
        else { cand[0] = d; cand[1] = (d + 1) % 8; cand[2] = (d + 7) % 8; cand[3] = (d + 2) % 8; cand[4] = (d + 6) % 8; nc = 5; }
        int ncand = (d == 8) ? 8 : 5;
        for (int q = 0; q < ncand; q++) {
            int nd = (d == 8) ? q : cand[q];
            double tc = 0;
            if (d != 8 && nd != d) {
                if (r < MR) continue;
                int dd = abs(nd - d); if (dd > 4) dd = 8 - dd;
                tc = dd == 1 ? T45 : T90;
            }
            int ni = i + DX[nd], nj = j + DY[nd];
            if (ni < 0 || nj < 0 || ni >= NI || nj >= NJ) continue;
            double nx = x + DX[nd] * R, ny = y + DY[nd] * R;
            if (!tfree(l, nx, ny)) continue;
            double step = R * ((nd & 1) ? s2 : 1.0);
            step += tex(l, nx, ny) * step;
            int nr = (nd == d) ? (r + 1 > MR ? MR : r + 1) : 1;
            size_t ns = SIDX(l, nj, ni, nd, nr);
            double ng = gc + step + tc;
            if (ng < gb[ns] - 1e-7) { gb[ns] = (float)ng; par[ns] = (int32_t)s; hpush((float)(ng + H(nx, ny)), (int32_t)ns); }
        }
        // via
        if ((d != 8 && r >= MR) || (d == 8 && !(i == i0 && j == j0))) {
            if (vfree(x, y)) {
                int nl = 1 - l; size_t ns = SIDX(nl, j, i, 8, 0);
                double ng = gc + VIAC + vex(x, y);
                if (ng < gb[ns] - 1e-7) { gb[ns] = (float)ng; par[ns] = (int32_t)s; hpush((float)(ng + H(x, y)), (int32_t)ns); }
            }
        }
    }
    printf("FAIL %ld\n", exp);
    return 0;
}
