"""
============================================================
  Exam Timetabling — Hyper-Heuristics
  Author  : Salem Ajimi
  Dataset : sta-f-83 (St. Andrews University)
  Run     : python algorithms/3_hyper_heuristique.py
============================================================
"""

import random
import time
import math
import os

# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────
DATASET_NAME  = "sta-f-83"
DATASETS_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets")
NUM_SLOTS     = 35
MAX_TIME_SEC  = 60
INITIAL_TEMP  = 2.0
COOLING_RATE  = 0.99995

# ──────────────────────────────────────────────
# 1. DATA LOADING
# ──────────────────────────────────────────────

def load_data():
    crs_path = os.path.join(DATASETS_PATH, DATASET_NAME + ".crs")
    stu_path = os.path.join(DATASETS_PATH, DATASET_NAME + ".stu")

    exams, exam_index = [], {}
    with open(crs_path) as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                eid = parts[0]
                if eid not in exam_index:
                    exam_index[eid] = len(exams)
                    exams.append(eid)

    n = len(exams)
    conflicts = [set() for _ in range(n)]

    with open(stu_path) as f:
        for line in f:
            ids = [exam_index[e] for e in line.strip().split() if e in exam_index]
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    conflicts[ids[i]].add(ids[j])
                    conflicts[ids[j]].add(ids[i])

    return exams, conflicts, n

# ──────────────────────────────────────────────
# 2. TIMETABLE STATE (incremental conflict count)
# ──────────────────────────────────────────────

class TimetableState:
    """
    snc[exam][slot] = number of conflicting neighbors of exam currently in slot.
    Moving exam costs O(neighbors) not O(n^2).
    """
    def __init__(self, n, num_slots, conflicts):
        self.n, self.num_slots, self.conflicts = n, num_slots, conflicts
        self.timetable       = [0] * n
        self.snc             = [[0] * num_slots for _ in range(n)]
        self.total_conflicts = 0

    def set_slot(self, exam, new_slot):
        old_slot = self.timetable[exam]
        if old_slot == new_slot:
            return
        self.total_conflicts -= self.snc[exam][old_slot]
        self.total_conflicts += self.snc[exam][new_slot]
        for nb in self.conflicts[exam]:
            self.snc[nb][old_slot] -= 1
            self.snc[nb][new_slot] += 1
        self.timetable[exam] = new_slot

    def best_slot_for(self, exam):
        return min(range(self.num_slots), key=lambda s: self.snc[exam][s])

    def copy_timetable(self):
        return self.timetable[:]

    def load_timetable(self, tt):
        self.snc             = [[0] * self.num_slots for _ in range(self.n)]
        self.total_conflicts = 0
        self.timetable       = [0] * self.n
        for exam, slot in enumerate(tt):
            self.set_slot(exam, slot)

# ──────────────────────────────────────────────
# 3. GREEDY INITIALISATION
# ──────────────────────────────────────────────

def greedy_init(state):
    order = sorted(range(state.n), key=lambda x: len(state.conflicts[x]), reverse=True)
    for exam in order:
        state.set_slot(exam, state.best_slot_for(exam))

# ──────────────────────────────────────────────
# 4. LOW-LEVEL HEURISTICS
# ──────────────────────────────────────────────

def llh_random_move(state):
    exam     = random.randint(0, state.n - 1)
    old_slot = state.timetable[exam]
    before   = state.total_conflicts
    state.set_slot(exam, random.randint(0, state.num_slots - 1))
    return before - state.total_conflicts, exam, old_slot

def llh_swap(state):
    a, b = random.sample(range(state.n), 2)
    sa, sb = state.timetable[a], state.timetable[b]
    if sa == sb:
        return 0, None, None
    before = state.total_conflicts
    state.set_slot(a, sb)
    state.set_slot(b, sa)
    return before - state.total_conflicts, (a, b), (sa, sb)

def llh_move_conflict(state):
    candidates = [e for e in range(state.n) if state.snc[e][state.timetable[e]] > 0]
    if not candidates:
        return llh_random_move(state)
    exam     = random.choice(candidates)
    old_slot = state.timetable[exam]
    before   = state.total_conflicts
    state.set_slot(exam, state.best_slot_for(exam))
    return before - state.total_conflicts, exam, old_slot

def llh_kempe_chain(state):
    if state.num_slots < 2:
        return 0, None, None
    slot_a, slot_b = random.sample(range(state.num_slots), 2)
    pool = [e for e in range(state.n) if state.timetable[e] in (slot_a, slot_b)]
    if not pool:
        return 0, None, None
    chain, frontier, target = set(), [random.choice(pool)], {slot_a, slot_b}
    while frontier:
        e = frontier.pop()
        if e in chain:
            continue
        chain.add(e)
        for nb in state.conflicts[e]:
            if state.timetable[nb] in target and nb not in chain:
                frontier.append(nb)
    saved  = {e: state.timetable[e] for e in chain}
    before = state.total_conflicts
    for e in chain:
        state.set_slot(e, slot_b if state.timetable[e] == slot_a else slot_a)
    return before - state.total_conflicts, chain, saved

def llh_balance(state):
    counts = [0] * state.num_slots
    for s in state.timetable:
        counts[s] += 1
    most  = max(range(state.num_slots), key=lambda s: counts[s])
    least = min(range(state.num_slots), key=lambda s: counts[s])
    pool  = [e for e in range(state.n) if state.timetable[e] == most]
    if not pool:
        return 0, None, None
    exam     = random.choice(pool)
    old_slot = state.timetable[exam]
    before   = state.total_conflicts
    state.set_slot(exam, least)
    return before - state.total_conflicts, exam, old_slot

LLH_LIST  = [llh_random_move, llh_swap, llh_move_conflict, llh_kempe_chain, llh_balance]
LLH_NAMES = ["Random Move", "Swap", "Move Conflicting", "Kempe Chain", "Load Balance"]

# ──────────────────────────────────────────────
# 5. UNDO
# ──────────────────────────────────────────────

def undo_move(state, idx, a, b):
    if idx in (0, 2, 4):
        if a is not None:
            state.set_slot(a, b)
    elif idx == 1:
        if a is not None:
            state.set_slot(a[0], b[0])
            state.set_slot(a[1], b[1])
    elif idx == 3:
        if a is not None:
            for e, s in b.items():
                state.set_slot(e, s)

# ──────────────────────────────────────────────
# 6. HYPER-HEURISTIC LOOP
# ──────────────────────────────────────────────

def run(state):
    greedy_init(state)
    best_tt   = state.copy_timetable()
    best_cost = state.total_conflicts
    scores    = [1.0] * len(LLH_LIST)
    temp      = INITIAL_TEMP
    start     = time.time()

    print(f"\n  After greedy init : {best_cost} conflicts")
    print(f"  Searching for {MAX_TIME_SEC}s ...\n")
    print(f"  {'Time':>6}  {'Iterations':>12}  {'Current':>10}  {'Best':>10}")
    print(f"  {'-'*46}")

    iteration = 0
    next_log  = max(1, MAX_TIME_SEC // 10)

    while True:
        elapsed = time.time() - start
        if elapsed >= MAX_TIME_SEC:
            break
        iteration += 1

        # Roulette-wheel LLH selection
        total = sum(scores)
        r, cumul, chosen = random.random() * total, 0, 0
        for i, w in enumerate(scores):
            cumul += w
            if r <= cumul:
                chosen = i
                break

        improvement, a, b = LLH_LIST[chosen](state)

        # SA acceptance
        if improvement >= 0 or random.random() < math.exp(improvement / (temp + 1e-10)):
            scores[chosen] = min(scores[chosen] * (1.3 if improvement > 0 else 0.99), 100.0)
            if state.total_conflicts < best_cost:
                best_cost = state.total_conflicts
                best_tt   = state.copy_timetable()
        else:
            undo_move(state, chosen, a, b)
            scores[chosen] = max(scores[chosen] * 0.98, 0.01)

        temp *= COOLING_RATE

        if elapsed >= next_log:
            print(f"  {elapsed:>5.0f}s  {iteration:>12,}  {state.total_conflicts:>10}  {best_cost:>10}")
            next_log += MAX_TIME_SEC // 10

        if best_cost == 0:
            print(f"\n  Zero conflicts found at iteration {iteration:,}!")
            break

    return best_tt, best_cost, iteration, time.time() - start, scores

# ──────────────────────────────────────────────
# 7. MAIN
# ──────────────────────────────────────────────

def main():
    print("=" * 56)
    print("  Hyper-Heuristics -- Exam Timetabling")
    print(f"  Dataset : {DATASET_NAME}  |  Slots: {NUM_SLOTS}  |  Time: {MAX_TIME_SEC}s")
    print("=" * 56)

    print("\n[1/3] Loading dataset ...")
    exams, conflicts, n = load_data()
    pairs = sum(len(c) for c in conflicts) // 2
    print(f"       {n} exams  |  {pairs} conflict pairs")

    print("\n[2/3] Running Hyper-Heuristic ...")
    state = TimetableState(n, NUM_SLOTS, conflicts)
    best_tt, best_cost, iterations, elapsed, scores = run(state)

    state.load_timetable(best_tt)
    verified = state.total_conflicts

    print(f"\n[3/3] Done")
    print(f"  Iterations : {iterations:,}")
    print(f"  Conflicts  : {best_cost}  (verified: {verified})")

    print("\n  LLH performance:")
    for name, sc in zip(LLH_NAMES, scores):
        bar = chr(0x2588) * int(20 * sc / max(scores))
        print(f"    {name:<20} {sc:>7.2f}  {bar}")

    # EXACT REQUIRED OUTPUT FORMAT
    print()
    print(f"[RESULT] Algorithm: Hyper-Heuristics | Time: {elapsed:.1f}s | Conflicts: {best_cost}")

if __name__ == "__main__":
    main()
