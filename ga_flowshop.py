import argparse
import random
import time
from multiprocessing import Pool, cpu_count

P = None


def init_worker(p):
    global P
    P = p


def generate_instance(n_jobs, n_machines, seed=1):
    rnd = random.Random(seed)
    return [[rnd.randint(1, 99) for _ in range(n_machines)] for _ in range(n_jobs)]


def makespan(perm):
    m = len(P[0])
    c = [0] * m
    for j in perm:
        pj = P[j]
        c[0] += pj[0]
        for k in range(1, m):
            c[k] = (c[k] if c[k] > c[k - 1] else c[k - 1]) + pj[k]
    return c[-1]


def initial_population(n_jobs, pop_size):
    pop = []
    for _ in range(pop_size):
        perm = list(range(n_jobs))
        random.shuffle(perm)
        pop.append(perm)
    return pop


def evaluate(pop, pool):
    if pool is None:
        return [makespan(ind) for ind in pop]
    chunk = max(1, len(pop) // (4 * pool._processes))
    return pool.map(makespan, pop, chunksize=chunk)


def tournament(pop, fit, k=3):
    best = random.randrange(len(pop))
    for _ in range(k - 1):
        i = random.randrange(len(pop))
        if fit[i] < fit[best]:
            best = i
    return pop[best]


def ox(p1, p2, a, b):
    n = len(p1)
    child = [None] * n
    child[a:b] = p1[a:b]
    used = set(p1[a:b])
    fill = [g for g in p2 if g not in used]
    idx = 0
    for i in list(range(b, n)) + list(range(0, a)):
        child[i] = fill[idx]
        idx += 1
    return child


def crossover(p1, p2, pc):
    if random.random() > pc or p1 is p2:
        return p1[:], p2[:]
    n = len(p1)
    a, b = sorted(random.sample(range(n + 1), 2))
    return ox(p1, p2, a, b), ox(p2, p1, a, b)


def mutate(ind, pm):
    if random.random() < pm:
        i, j = random.sample(range(len(ind)), 2)
        ind[i], ind[j] = ind[j], ind[i]


def ga(p, pop_size=200, generations=200, pc=0.9, pm=0.1, workers=1, seed=42):
    global P
    P = p
    random.seed(seed)
    n_jobs = len(p)

    pool = Pool(workers, initializer=init_worker, initargs=(p,)) if workers > 1 else None
    try:
        pop = initial_population(n_jobs, pop_size)
        fit = evaluate(pop, pool)
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
            fit = evaluate(pop, pool)

            gi = min(range(pop_size), key=fit.__getitem__)
            if fit[gi] < best_fit:
                best, best_fit = pop[gi][:], fit[gi]
    finally:
        if pool is not None:
            pool.close()
            pool.join()

    return best, best_fit


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=100)
    ap.add_argument("--machines", type=int, default=20)
    ap.add_argument("--pop", type=int, default=200)
    ap.add_argument("--gens", type=int, default=200)
    ap.add_argument("--workers", type=int, default=cpu_count())
    args = ap.parse_args()

    p = generate_instance(args.jobs, args.machines)
    print(f"Instancja: {args.jobs} zadań x {args.machines} maszyn, "
          f"populacja {args.pop}, pokoleń {args.gens}")

    t = time.perf_counter()
    _, cmax_seq = ga(p, args.pop, args.gens, workers=1)
    t_seq = time.perf_counter() - t
    print(f"Sekwencyjnie:          Cmax = {cmax_seq}, czas = {t_seq:.2f} s")

    t = time.perf_counter()
    _, cmax_par = ga(p, args.pop, args.gens, workers=args.workers)
    t_par = time.perf_counter() - t
    print(f"Równolegle ({args.workers} proc.): Cmax = {cmax_par}, czas = {t_par:.2f} s")

    print(f"Przyspieszenie: {t_seq / t_par:.2f}x")