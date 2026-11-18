import argparse
import random
import time

import numpy as np

from ga_flowshop import (generate_instance, initial_population, tournament,
                         crossover, mutate, ga as ga_cpu)
import ga_flowshop

import os
import sys
import pathlib

site_packages = pathlib.Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
if site_packages.exists():
    for bin_dir in site_packages.rglob("bin"):
        os.add_dll_directory(str(bin_dir))
        os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ["PATH"]

try:
    import cupy as cp
    cp.cuda.runtime.getDeviceCount()
    GPU = True
except Exception as e:
    print("Błąd inicjalizacji GPU:", e)
    GPU = False


try:
    import cupy as cp
    cp.cuda.runtime.getDeviceCount()
    GPU = True
except Exception:
    GPU = False

KERNEL_CODE = r"""
extern "C" __global__
void makespan_kernel(const int* pop, const int* P, int* out,
                     int pop_size, int n, int m)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= pop_size) return;

    int c[64];
    for (int k = 0; k < m; k++) c[k] = 0;

    const int* perm = pop + idx * n;
    for (int i = 0; i < n; i++) {
        int j = perm[i];
        c[0] += P[j * m];
        for (int k = 1; k < m; k++) {
            int start = c[k] > c[k - 1] ? c[k] : c[k - 1];
            c[k] = start + P[j * m + k];
        }
    }
    out[idx] = c[m - 1];
}
"""

if GPU:
    makespan_kernel = cp.RawKernel(KERNEL_CODE, "makespan_kernel")


def evaluate_gpu(pop, P_gpu, n, m):
    pop_size = len(pop)
    pop_gpu = cp.asarray(np.array(pop, dtype=np.int32))
    out_gpu = cp.empty(pop_size, dtype=cp.int32)

    threads = 128
    blocks = (pop_size + threads - 1) // threads
    makespan_kernel((blocks,), (threads,),
                    (pop_gpu, P_gpu, out_gpu,
                     np.int32(pop_size), np.int32(n), np.int32(m)))
    cp.cuda.Stream.null.synchronize()
    return out_gpu.get().tolist()


def ga_gpu(p, pop_size=200, generations=200, pc=0.9, pm=0.1, seed=42):
    random.seed(seed)
    n, m = len(p), len(p[0])
    if m > 64:
        raise ValueError("Kernel obsługuje maksymalnie 64 maszyny")

    P_gpu = cp.asarray(np.array(p, dtype=np.int32))

    pop = initial_population(n, pop_size)
    fit = evaluate_gpu(pop, P_gpu, n, m)
    best_i = min(range(pop_size), key=fit.__getitem__)
    best, best_fit = pop[best_i][:], fit[best_i]

    for gen in range(generations):
        parents = [tournament(pop, fit) for _ in range(pop_size)]

        children = []
        for i in range(0, pop_size, 2):
            c1, c2 = crossover(parents[i], parents[(i + 1) % pop_size], pc)
            mutate(c1, pm)
            mutate(c2, pm)
            children += [c1, c2]
        children = children[:pop_size]
        children[0] = best[:]

        pop = children
        fit = evaluate_gpu(pop, P_gpu, n, m)

        gi = min(range(pop_size), key=fit.__getitem__)
        if fit[gi] < best_fit:
            best, best_fit = pop[gi][:], fit[gi]

    return best, best_fit


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=100)
    ap.add_argument("--machines", type=int, default=20)
    ap.add_argument("--pop", type=int, default=200)
    ap.add_argument("--gens", type=int, default=200)
    args = ap.parse_args()

    p = generate_instance(args.jobs, args.machines)
    print(f"Instancja: {args.jobs} zadań x {args.machines} maszyn, "
          f"populacja {args.pop}, pokoleń {args.gens}")

    t = time.perf_counter()
    _, cmax_cpu = ga_cpu(p, args.pop, args.gens, workers=1)
    t_cpu = time.perf_counter() - t
    print(f"CPU (sekwencyjnie): Cmax = {cmax_cpu}, czas = {t_cpu:.2f} s")

    if not GPU:
        print("Brak GPU/CuPy – pomijam wersję GPU.")
    else:
        ga_flowshop.P = p
        test_pop = initial_population(args.jobs, 50)
        P_gpu = cp.asarray(np.array(p, dtype=np.int32))
        ok = evaluate_gpu(test_pop, P_gpu, args.jobs, args.machines) == \
             [ga_flowshop.makespan(x) for x in test_pop]
        print(f"Zgodność wyników GPU z CPU: {'OK' if ok else 'BŁĄD'}")

        evaluate_gpu(test_pop, P_gpu, args.jobs, args.machines)

        t = time.perf_counter()
        _, cmax_gpu = ga_gpu(p, args.pop, args.gens)
        t_gpu = time.perf_counter() - t
        print(f"GPU:                Cmax = {cmax_gpu}, czas = {t_gpu:.2f} s")
        print(f"Przyspieszenie: {t_cpu / t_gpu:.2f}x")