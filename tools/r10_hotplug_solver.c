/* Charge-based trapezoidal RLC integration for r10_hotplug.py. No external libraries. */
#include <math.h>
#include <string.h>

#define NMAX 32
#define EMAX 64
#define CMAX 6
#define PMAX 160

static int solve(int n, double a[NMAX][NMAX], double *b) {
    for (int k = 0; k < n; ++k) {
        int p = k;
        for (int i = k + 1; i < n; ++i) if (fabs(a[i][k]) > fabs(a[p][k])) p = i;
        if (fabs(a[p][k]) < 1e-20) return 1;
        if (p != k) {
            for (int j = k; j < n; ++j) { double t = a[k][j]; a[k][j] = a[p][j]; a[p][j] = t; }
            double t = b[k]; b[k] = b[p]; b[p] = t;
        }
        for (int i = k + 1; i < n; ++i) {
            double f = a[i][k] / a[k][k];
            for (int j = k + 1; j < n; ++j) a[i][j] -= f * a[k][j];
            b[i] -= f * b[k];
        }
    }
    for (int i = n - 1; i >= 0; --i) {
        for (int j = i + 1; j < n; ++j) b[i] -= a[i][j] * b[j];
        b[i] /= a[i][i];
    }
    return 0;
}

static void capacitor(double v, int count, const double *x, const double *c, const double *q,
                      double scale, double *cap, double *charge) {
    double u = fabs(v);
    int lo = 0, hi = count - 1;
    while (hi - lo > 1) { int mid = (lo + hi) / 2; if (x[mid] > u) hi = mid; else lo = mid; }
    double slope = u >= x[count - 1] ? 0 : (c[hi] - c[lo]) / (x[hi] - x[lo]);
    if (u >= x[count - 1]) lo = count - 1;
    double d = u - x[lo];
    *cap = scale * (c[lo] + d * slope);
    *charge = copysign(scale * (q[lo] + c[lo] * d + slope * d * d / 2), v);
}

static double pack(double t, double edge_ns) {
    return edge_ns > 0 && t < edge_ns * 1e-9 ? 2 - 10.4 * t / (edge_ns * 1e-9) : -8.4;
}

/* E and CE are incidence matrices. PACK is the source offset on the last inductor.
   V starts with 2V on BAT_IN and 0V on BAT_DAMP. Results: min,max,fall,rise,tfall,vfall,damper_W,damper_J. */
int hotplug(int n, int m, const double *E, const double *CE, const double *R, const double *L,
            const int *curve_n, const double *curve_x, const double *curve_c, const double *curve_q,
            const double *scale, double *V, int tvs_node, int input_node, int damper_node, int bleed_node,
            double vbr, double rdamp, double contact_edge_ns, double step_scale, double end_us, double *out) {
    if (n < 1 || n > NMAX || m < 1 || m > EMAX || !isfinite(step_scale) || step_scale <= 0 ||
        !isfinite(end_us) || end_us <= 0 || !isfinite(contact_edge_ns) || contact_edge_ns < 0) return 1;
    double I[EMAX] = {0}, IC[CMAX] = {0}, Qold[CMAX], Gold[EMAX], H[EMAX];
    double A[NMAX][NMAX], J[NMAX][NMAX], rhs[NMAX], delta[NMAX], next[NMAX];
    double old_drop[EMAX], cap, charge;
    const int types[CMAX] = {0, 0, 1, 1, 2, 3};
    out[0] = out[1] = V[input_node]; out[2] = out[3] = out[4] = 0; out[5] = V[input_node];
    out[6] = out[7] = 0;
    double t = 0, previous_dt = 0;
    int first = 1;
    while (t < end_us * 1e-6 - 1e-15) {
        double dt = (t < 1e-6 - 1e-15 ? .5e-9 : t < 20e-6 - 1e-15 ? 2e-9 : 10e-9) * step_scale;
        if (t + dt > end_us * 1e-6) dt = end_us * 1e-6 - t;
        double alpha = first ? 1 : 2;
        if (dt != previous_dt) {
            memset(A, 0, sizeof A);
            for (int e = 0; e < m; ++e) {
                Gold[e] = dt / (alpha * L[e] + R[e] * dt);
                for (int i = 0; i < n; ++i) for (int j = 0; j < n; ++j)
                    A[i][j] += Gold[e] * E[e*n+i] * E[e*n+j];
            }
            A[damper_node][damper_node] += 1 / rdamp;
            A[bleed_node][bleed_node] += 1e-4;
            previous_dt = dt;
        }
        memset(rhs, 0, sizeof rhs);
        for (int e = 0; e < m; ++e) {
            double offset = e == m - 1 ? pack(t + dt, contact_edge_ns) : 0;
            old_drop[e] = e == m - 1 ? pack(t, contact_edge_ns) : 0;
            for (int i = 0; i < n; ++i) old_drop[e] += E[e*n+i] * V[i];
            H[e] = first ? L[e] / (L[e] + R[e]*dt) * I[e] :
                (2*L[e] - R[e]*dt) / (2*L[e] + R[e]*dt) * I[e] + Gold[e]*old_drop[e];
            for (int i = 0; i < n; ++i) rhs[i] -= E[e*n+i] * (H[e] + Gold[e]*offset);
        }
        for (int c = 0; c < CMAX; ++c) {
            int type = types[c]; double voltage = 0;
            for (int i = 0; i < n; ++i) voltage += CE[c*n+i] * V[i];
            capacitor(voltage, curve_n[type], curve_x+type*PMAX, curve_c+type*PMAX, curve_q+type*PMAX,
                      scale[c], &cap, &Qold[c]);
        }
        memcpy(next, V, n*sizeof(double));
        int converged = 0;
        for (int iteration = 0; iteration < 25; ++iteration) {
            memcpy(J, A, sizeof A);
            for (int i = 0; i < n; ++i) {
                delta[i] = rhs[i];
                for (int j = 0; j < n; ++j) delta[i] -= A[i][j] * next[j];
            }
            for (int c = 0; c < CMAX; ++c) {
                int type = types[c]; double voltage = 0;
                for (int i = 0; i < n; ++i) voltage += CE[c*n+i] * next[i];
                capacitor(voltage, curve_n[type], curve_x+type*PMAX, curve_c+type*PMAX, curve_q+type*PMAX,
                          scale[c], &cap, &charge);
                /* Form charge differences before multiplying by 1/dt. This avoids cancellation of
                   large companion-source currents when the sensitivity adds a pF input shunt. */
                double current = alpha / dt * (charge - Qold[c]) - (first ? 0 : IC[c]);
                for (int i = 0; i < n; ++i) {
                    delta[i] -= CE[c*n+i] * current;
                    for (int j = 0; j < n; ++j) J[i][j] += CE[c*n+i] * CE[c*n+j] * alpha / dt * cap;
                }
            }
            double v = next[tvs_node], x = (fabs(v) - vbr) / .1;
            double current = copysign(.5 * (x > 40 ? x : log1p(exp(x))), v);
            double slope = 5 / (1 + exp(fmax(-700, fmin(700, -x))));
            delta[tvs_node] -= current; J[tvs_node][tvs_node] += slope;
            if (solve(n, J, delta)) return 2;
            double error = 0;
            for (int i = 0; i < n; ++i) {
                if (!isfinite(delta[i])) return 4;
                next[i] += delta[i];
                if (!isfinite(next[i])) return 4;
                error = fmax(error, fabs(delta[i]));
            }
            if (error < 1e-9) { converged = 1; break; }
        }
        if (!converged) return 3;
        for (int e = 0; e < m; ++e) {
            double voltage = e == m - 1 ? pack(t + dt, contact_edge_ns) : 0;
            for (int i = 0; i < n; ++i) voltage += E[e*n+i] * next[i];
            I[e] = Gold[e]*voltage + H[e];
            if (!isfinite(I[e])) return 4;
        }
        for (int c = 0; c < CMAX; ++c) {
            int type = types[c]; double voltage = 0;
            for (int i = 0; i < n; ++i) voltage += CE[c*n+i] * next[i];
            capacitor(voltage, curve_n[type], curve_x+type*PMAX, curve_c+type*PMAX, curve_q+type*PMAX,
                      scale[c], &cap, &charge);
            IC[c] = alpha / dt * (charge - Qold[c]) - (first ? 0 : IC[c]);
            if (!isfinite(IC[c])) return 4;
        }
        double fall = (V[input_node] - next[input_node]) / dt / 1e6;
        out[0] = fmin(out[0], next[input_node]); out[1] = fmax(out[1], next[input_node]);
        if (fall > out[2]) { out[2] = fall; out[4] = (t + dt/2)*1e6; out[5] = (V[input_node]+next[input_node])/2; }
        out[3] = fmax(out[3], -fall);
        double old_power = V[damper_node] * V[damper_node] / rdamp;
        double power = next[damper_node] * next[damper_node] / rdamp;
        out[6] = fmax(out[6], power);
        out[7] += (old_power + power) * dt / 2;
        if (!isfinite(out[0]) || !isfinite(out[2])) return 4;
        memcpy(V, next, n*sizeof(double));
        t += dt;
        if (first) previous_dt = 0;  /* rebuild alpha=2 conductances even when dt stays the same */
        first = 0;
    }
    return 0;
}
