/* R12 routing drafting aid (D-R12-26): octilinear A* on a grid of up to three signal layers (F / B / In2, D-R12-34) joined by
 * through vias.
 * Not part of the build: its output is frozen into m3_design/r12_routes.tsv, which r12_route.py replays.
 *
 * State: (layer, x, y, dir, run, first, nvia). dir 0..7 = E, NE, N, NW, W, SW, S, SE (grid y grows south); run = steps
 * in the current segment (0 = no segment yet: at a start node or just after a via; capped at RM); first = the current
 * segment starts at a terminal (1: a pad, 2: a via; a via right after a via needs VMIN steps), so it may end after the end minimum; a middle segment needs the middle
 * minimum before a turn (route_check short_segment / tiny_jog). Turns are +-45 degrees only (no 90-degree bend, no
 * acute angle). nvia counts the vias of this path (route_check extra_vias: a net's vias are budgeted by the caller).
 * Visited states live in an open-addressing hash table (the window is too large for dense arrays).
 * Negotiated congestion (PathFinder, D-R12-35): ncost[l*H*W+...] is a per-node, per-layer cost added on entering the
 * node (present use x present factor + history, computed by route.py from the other units' copper), vcost[y*W+x] the
 * same for a via at the node; with goal_via (params[20]) the end via pays vcost too (a "paid" state bit, so the search
 * still stops at the cheapest goal). Both may be NULL. label4() labels 4-connected components of a mask (the 3V3 pour
 * guard, D-R12-36).
 *
 * build: cc -O2 -shared -fPIC -o astar.so astar.c
 */
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>

static const int DX[8] = {1, 1, 0, -1, -1, -1, 0, 1};
static const int DY[8] = {0, -1, -1, -1, 0, 1, 1, 1};

typedef struct { float f; int32_t e; } item;
typedef struct { item *a; int n, cap; } heap;
static int hpush(heap *h, float f, int32_t e) {
    if (h->n == h->cap) {
        int nc = h->cap ? h->cap * 2 : 1 << 16;
        item *na = realloc(h->a, sizeof(item) * nc);
        if (!na) return -1;
        h->a = na; h->cap = nc;
    }
    int i = h->n++;
    while (i > 0) { int p = (i - 1) / 2; if (h->a[p].f <= f) break; h->a[i] = h->a[p]; i = p; }
    h->a[i].f = f; h->a[i].e = e;
    return 0;
}
static item hpop(heap *h) {
    item top = h->a[0], last = h->a[--h->n];
    int i = 0;
    for (;;) { int c = 2 * i + 1; if (c >= h->n) break; if (c + 1 < h->n && h->a[c + 1].f < h->a[c].f) c++;
               if (h->a[c].f >= last.f) break; h->a[i] = h->a[c]; i = c; }
    if (h->n) h->a[i] = last;
    return top;
}

typedef struct { int64_t key; float g; int32_t parent; uint8_t closed; } entry;
static entry *T; static int64_t TCAP, TN;
static int32_t tfind(int64_t key, int create) {
    uint64_t hsh = (uint64_t)key * 0x9E3779B97F4A7C15ULL;
    int64_t i = (int64_t)(hsh >> 20) & (TCAP - 1);
    for (;;) {
        if (T[i].key == key) return (int32_t)i;
        if (T[i].key == -1) {
            if (!create || TN * 10 > TCAP * 7) return -1;
            T[i].key = key; T[i].g = 1e30f; T[i].parent = -1; T[i].closed = 0; TN++;
            return (int32_t)i;
        }
        i = (i + 1) & (TCAP - 1);
    }
}

/* Layers: 0 F, 1 B, 2 In2 (params[19] = NL, 2 or 3); a through via joins every allowed layer at its node.
 * blocked[l*H*W + y*W + x]: node closed on layer l; viaok[y*W+x]: a via may sit here; goal[l*H*W+...]: low byte = the
 * arrival directions that end the search there after an end-length segment (255 = any), high byte = arrival
 * directions that need a middle-length segment (a 45-degree bend onto a fixed escape stub); ncost / vcost: congestion costs.
 * params: [step, diag, turn, via, cost_F, cost_B, mid_s, mid_d, end_s, end_d, unused, allowF, allowB, RM, maxvia,
 *          heuristic weight, VMIN, cost_In2, allowIn2, NL, goal_via]
 * out: (layer, x, y) triples from goal back to start; returns count, -1 no path, -2 memory, -3 table full, -4 expansion limit. */
int astar(int W, int H, const uint8_t *blocked, const uint8_t *viaok, const uint16_t *goal, const float *ncost, const float *vcost,
          int ns, const int *starts, int ng, const float *gcx, const float *gcy, const float *gr,
          const float *params, int maxout, int *out, long maxexp) {
    const float STEP = params[0], DIAG = params[1], TURN = params[2], VIA = params[3];
    const int NL = (int)params[19];
    const float LC[3] = {params[4], params[5], params[17]};
    const int MID[2] = {(int)params[6], (int)params[7]}, END[2] = {(int)params[8], (int)params[9]};
    const int GV = (int)params[20];
    const int allow[3] = {(int)params[11], (int)params[12], NL > 2 ? (int)params[18] : 0};
    const int RM = (int)params[13], MAXV = (int)params[14];
    const float HW = params[15];                         /* heuristic weight (weighted A*: a drafting aid) */
    const int VMIN = (int)params[16];                    /* steps before a via: vias of one path stay apart */
    const long NODES = (long)W * H;
    TCAP = 1L << 24; TN = 0;
    T = malloc(sizeof(entry) * TCAP);
    if (!T) return -2;
    for (int64_t i = 0; i < TCAP; i++) T[i].key = -1;
    heap h = {0};
    float minlc = 1e30f;
    for (int q = 0; q < NL; q++) if (allow[q] && LC[q] < minlc) minlc = LC[q];
    int status = -1;
#define KEY(l, x, y, d, r, f, v, p) ((((((((((int64_t)(l) * H + (y)) * W + (x)) * 8 + (d)) * (RM + 1) + (r)) * 3 + (f)) * 3 + (v)) * 2 + (p))))
#define HEUR(x, y) ({ float best = 1e30f; for (int k = 0; k < ng; k++) { float ax = fabsf((x) - gcx[k]), ay = fabsf((y) - gcy[k]); \
        float mn = ax < ay ? ax : ay, mx = ax < ay ? ay : ax; float o = (mx - mn) * STEP + mn * DIAG - gr[k] * DIAG; \
        if (o < best) best = o; } (best < 0 ? 0 : best) * minlc * HW; })
    for (int i = 0; i < ns; i++) {
        int l = starts[3 * i], x = starts[3 * i + 1], y = starts[3 * i + 2];
        if (!allow[l]) continue;
        int32_t e = tfind(KEY(l, x, y, 0, 0, 1, 0, 0), 1);
        if (e < 0) { status = -3; goto done; }
        T[e].g = 0; T[e].parent = -1;
        hpush(&h, HEUR((float)x, (float)y), e);
    }
    int32_t found = -1;
    long expanded = 0;
    while (h.n) {
        item it = hpop(&h);
        int32_t e = it.e;
        if (T[e].closed) continue;
        T[e].closed = 1;
        if (++expanded > maxexp) { status = -4; break; }
        int64_t t = T[e].key;
        int p = (int)(t % 2); t /= 2; int v = t % 3; t /= 3; int f = t % 3; t /= 3; int r = t % (RM + 1); t /= RM + 1; int d = t % 8; t /= 8;
        int x = t % W; t /= W; int y = t % H; t /= H; int l = (int)t;
        long node = (long)l * NODES + (long)y * W + x;
        float gs = T[e].g;
        if (p) { found = e; break; }                       /* a goal whose end via has paid its congestion cost */
        if (r > 0) {
            int gm = goal[node], hit = 0;
            if ((gm & (1 << d)) && (r >= END[d & 1] || (f == 1 && T[e].parent >= 0)) && (f != 2 || r >= VMIN)) hit = 1;
            if (((gm >> 8) & (1 << d)) && r >= MID[d & 1]) hit = 1;
            if (hit) {
                float gc = (GV && vcost) ? vcost[(long)y * W + x] : 0.0f;
                if (gc <= 0.0f) { found = e; break; }
                int32_t ne = tfind(KEY(l, x, y, d, r, f, v, 1), 1);
                if (ne < 0) { status = -3; goto done; }
                if (!T[ne].closed && gs + gc < T[ne].g) {
                    T[ne].g = gs + gc; T[ne].parent = T[e].parent;
                    if (hpush(&h, gs + gc, ne)) { status = -2; goto done; }
                }
            }
        }
        for (int nd = 0; nd < 8; nd++) {
            int turn = 0;
            if (r > 0) {
                int diff = (nd - d + 8) % 8;
                if (diff == 0) turn = 0;
                else if (diff == 1 || diff == 7) turn = 1;
                else continue;
                if (turn && r < (f ? END[d & 1] : MID[d & 1])) continue;
                if (turn && f == 2 && r < VMIN) continue;      /* leave a via straight for VMIN steps */
            }
            int nx = x + DX[nd], ny = y + DY[nd];
            if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
            long nn = (long)l * NODES + (long)ny * W + nx;
            if (blocked[nn]) continue;
            if ((nd & 1) && blocked[(long)l * NODES + (long)y * W + nx] && blocked[(long)l * NODES + (long)ny * W + x])
                continue;
            int nr, nf;
            if (r == 0) { nr = 1; nf = f; }
            else if (turn) { nr = 1; nf = 0; }
            else { nr = r + 1 > RM ? RM : r + 1; nf = f; }
            float c = ((nd & 1) ? DIAG : STEP) * LC[l] + (turn ? TURN : 0) + (ncost ? ncost[nn] : 0);
            int32_t ne = tfind(KEY(l, nx, ny, nd, nr, nf, v, 0), 1);
            if (ne < 0) { status = -3; goto done; }
            if (T[ne].closed) continue;
            float ng2 = gs + c;
            if (ng2 < T[ne].g) {
                T[ne].g = ng2; T[ne].parent = e;
                if (hpush(&h, ng2 + HEUR((float)nx, (float)ny), ne)) { status = -2; goto done; }
            }
        }
        if (r > 0 && v < MAXV && viaok[(long)y * W + x] && r >= END[d & 1] && (f != 2 || r >= VMIN)) {
            for (int ol = 0; ol < NL; ol++) {
                if (ol == l || !allow[ol] || blocked[(long)ol * NODES + (long)y * W + x]) continue;
                int32_t ne = tfind(KEY(ol, x, y, 0, 0, 2, v + 1, 0), 1);
                if (ne < 0) { status = -3; goto done; }
                float ng2 = gs + VIA + (vcost ? vcost[(long)y * W + x] : 0.0f);
                if (!T[ne].closed && ng2 < T[ne].g) {
                    T[ne].g = ng2; T[ne].parent = e;
                    if (hpush(&h, ng2 + HEUR((float)x, (float)y), ne)) { status = -2; goto done; }
                }
            }
        }
    }
    if (found >= 0) {
        int n = 0;
        int32_t e = found;
        while (e >= 0 && n < maxout) {
            int64_t t = T[e].key;
            t /= 2; t /= 3; t /= 3; t /= RM + 1; t /= 8;
            int x = t % W; t /= W; int y = t % H; t /= H; int l = (int)t;
            out[3 * n] = l; out[3 * n + 1] = x; out[3 * n + 2] = y; n++;
            e = T[e].parent;
        }
        status = n;
    }
done:
    free(T); T = NULL; free(h.a);
    return status;
}

/* 4-connected component labels of mask (1 = member) into lab (0 = not a member, else 1..n); returns n or -2. */
int label4(int W, int H, const uint8_t *mask, int32_t *lab) {
    long N = (long)W * H;
    int32_t *st = malloc(sizeof(int32_t) * N);
    if (!st) return -2;
    for (long i = 0; i < N; i++) lab[i] = 0;
    int n = 0;
    for (long i = 0; i < N; i++) {
        if (!mask[i] || lab[i]) continue;
        n++; long sp = 0; st[sp++] = (int32_t)i; lab[i] = n;
        while (sp) {
            long q = st[--sp]; int x = (int)(q % W), y = (int)(q / W);
            const int ox[4] = {1, -1, 0, 0}, oy[4] = {0, 0, 1, -1};
            for (int k = 0; k < 4; k++) {
                int nx = x + ox[k], ny = y + oy[k];
                if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
                long r = (long)ny * W + nx;
                if (mask[r] && !lab[r]) { lab[r] = n; st[sp++] = (int32_t)r; }
            }
        }
    }
    free(st);
    return n;
}
