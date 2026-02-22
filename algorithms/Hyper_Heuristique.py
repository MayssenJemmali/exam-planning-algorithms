import os
import sys
import time
import random
import math
from collections import defaultdict
import argparse


# ─────────────────────────── CONFIGURATION ───────────────────────────────────
DATASET_NAME = "sta-f-83"          # Change to 'car-s-91' for large benchmark

DATASET_INFO = {
    "sta-f-83": {"periods": 13},
    "car-s-91": {"periods": 35},
}

# Find datasets folder relative to this script
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(SCRIPT_DIR, "Opti-Exam-Project", "Opti-Exam-Project", "datasets")
if not os.path.isdir(DATASET_DIR):
    DATASET_DIR = os.path.join(SCRIPT_DIR, "datasets")

TIME_LIMIT      = 500     # seconds
INITIAL_TEMP    = 10.0    # SA initial temperature
COOLING_RATE    = 0.9995  # SA cooling rate
PENALTY_WEIGHT  = 1.0     # Weight for soft constraints
CONFLICT_WEIGHT = 1000.0  # Heavy weight for hard constraints


# ─────────────────────────── DATA LOADING ────────────────────────────────────

def load_dataset(name: str, folder: str):
    crs_path = os.path.join(folder, f"{name}.crs")
    stu_path = os.path.join(folder, f"{name}.stu")

    exam_map  = {}
    exam_list = []
    with open(crs_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            eid = line.split()[0]
            if eid not in exam_map:
                exam_map[eid] = len(exam_list)
                exam_list.append(eid)
    n_exams = len(exam_list)

    student_exams  = []
    conflict_set   = defaultdict(set)

    with open(stu_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            indices = [exam_map[r] for r in line.split() if r in exam_map]
            if len(indices) < 2:
                continue
            student_exams.append(indices)
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    a, b = indices[i], indices[j]
                    conflict_set[a].add(b)
                    conflict_set[b].add(a)

    exam_students_map = defaultdict(list)
    for student in student_exams:
        for exam in student:
            exam_students_map[exam].append(student)

    conflict_set = dict(conflict_set)

    print(f"[INFO] Dataset: {name}")
    print(f"[INFO] Exams: {n_exams} | Students: {len(student_exams)}")
    print(f"[INFO] Conflict pairs: {sum(len(v) for v in conflict_set.values()) // 2}")

    return exam_list, exam_map, student_exams, exam_students_map, conflict_set, n_exams


# ─────────────────────────── OBJECTIVE FUNCTIONS ─────────────────────────────

PENALTY_SCORES = [0, 16, 8, 4, 2, 1]  # index = slot diff (1..5)


def count_conflicts(solution, conflict_set):
    """Count conflicting exam pairs sharing the same slot."""
    count = 0
    for exam, conflicts in conflict_set.items():
        s = solution[exam]
        for other in conflicts:
            if solution[other] == s:
                count += 1
    return count // 2


def calculate_penalty(solution, student_exams):
    """Toronto Benchmark soft-constraint penalty."""
    if not student_exams:
        return 0.0
    total = 0
    for student in student_exams:
        slots = sorted(solution[e] for e in student)
        for i in range(len(slots)):
            for j in range(i + 1, len(slots)):
                diff = slots[j] - slots[i]
                if 1 <= diff <= 5:
                    total += PENALTY_SCORES[diff]
    return total / len(student_exams)


def get_objective(solution, conflict_set, student_exams):
    return (count_conflicts(solution, conflict_set) * CONFLICT_WEIGHT
            + calculate_penalty(solution, student_exams) * PENALTY_WEIGHT)


# ─────────────────────────── INITIAL SOLUTION ────────────────────────────────

def greedy_initial_solution(n_exams, conflict_set, n_slots):
    """Greedy graph-colouring: highest-degree exam first."""
    order = sorted(range(n_exams),
                   key=lambda e: len(conflict_set.get(e, set())),
                   reverse=True)
    solution = [-1] * n_exams
    for exam in order:
        conf_per_slot = [0] * n_slots
        for nb in conflict_set.get(exam, set()):
            if solution[nb] != -1:
                conf_per_slot[solution[nb]] += 1
        solution[exam] = conf_per_slot.index(min(conf_per_slot))
    return solution


# ─────────────────────────── LOW-LEVEL HEURISTICS ────────────────────────────
# Every heuristic returns (accepted: bool, delta_obj: float)
# Ground-truth conflict/penalty counts are maintained OUTSIDE the heuristics.

def _sa_accept(delta, temp):
    return temp > 0 and random.random() < math.exp(-delta / temp)


def heuristic_random_move(solution, conflict_set, student_exams, exam_students_map, n_slots, temp):
    """Move one exam (preferably conflicting) to a random slot."""
    n_exams = len(solution)
    conflicting = [e for e in range(n_exams)
                   if any(solution[nb] == solution[e]
                          for nb in conflict_set.get(e, set()))]
    exam = (random.choice(conflicting)
            if conflicting and random.random() < 0.7
            else random.randrange(n_exams))

    new_slot = random.randrange(n_slots)
    old_slot = solution[exam]
    if old_slot == new_slot:
        return False, 0.0

    # delta conflicts (local)
    d_conf = sum(
        (1 if solution[nb] == new_slot else 0) - (1 if solution[nb] == old_slot else 0)
        for nb in conflict_set.get(exam, set())
    )
    # delta penalty (local)
    old_pen = new_pen = 0.0
    for student in exam_students_map.get(exam, []):
        slots_old = sorted(solution[e] for e in student)
        slots_new = sorted(new_slot if e == exam else solution[e] for e in student)
        for i in range(len(slots_old)):
            for j in range(i + 1, len(slots_old)):
                d = slots_old[j] - slots_old[i]
                if 1 <= d <= 5:
                    old_pen += PENALTY_SCORES[d]
        for i in range(len(slots_new)):
            for j in range(i + 1, len(slots_new)):
                d = slots_new[j] - slots_new[i]
                if 1 <= d <= 5:
                    new_pen += PENALTY_SCORES[d]
    d_pen   = (new_pen - old_pen) / max(len(student_exams), 1)
    d_total = d_conf * CONFLICT_WEIGHT + d_pen * PENALTY_WEIGHT

    if d_total < 0 or _sa_accept(d_total, temp):
        solution[exam] = new_slot
        return True, d_total
    return False, 0.0


def heuristic_exam_reinsertion(solution, conflict_set, student_exams, exam_students_map, n_slots, temp):
    """Move one exam to its globally best slot."""
    n_exams = len(solution)
    conflicting = [e for e in range(n_exams)
                   if any(solution[nb] == solution[e]
                          for nb in conflict_set.get(e, set()))]
    exam = (random.choice(conflicting)
            if conflicting and random.random() < 0.7
            else random.randrange(n_exams))

    best_delta = 1e18
    best_slot  = solution[exam]

    for slot in range(n_slots):
        if slot == solution[exam]:
            continue
        d_conf = sum(
            (1 if solution[nb] == slot else 0) - (1 if solution[nb] == solution[exam] else 0)
            for nb in conflict_set.get(exam, set())
        )
        old_pen = new_pen = 0.0
        for student in exam_students_map.get(exam, []):
            slots_old = sorted(solution[e] for e in student)
            slots_new = sorted(slot if e == exam else solution[e] for e in student)
            for i in range(len(slots_old)):
                for j in range(i + 1, len(slots_old)):
                    d = slots_old[j] - slots_old[i]
                    if 1 <= d <= 5:
                        old_pen += PENALTY_SCORES[d]
            for i in range(len(slots_new)):
                for j in range(i + 1, len(slots_new)):
                    d = slots_new[j] - slots_new[i]
                    if 1 <= d <= 5:
                        new_pen += PENALTY_SCORES[d]
        d_pen   = (new_pen - old_pen) / max(len(student_exams), 1)
        d_total = d_conf * CONFLICT_WEIGHT + d_pen * PENALTY_WEIGHT
        if d_total < best_delta:
            best_delta = d_total
            best_slot  = slot

    if best_delta < 0 or _sa_accept(best_delta, temp):
        solution[exam] = best_slot
        return True, best_delta
    return False, 0.0


def heuristic_swap(solution, conflict_set, student_exams, exam_students_map, n_slots, temp):
    """Swap slots of two exams; evaluate via full recount (safe)."""
    n_exams = len(solution)
    a = random.randrange(n_exams)
    b = random.randrange(n_exams)
    if a == b or solution[a] == solution[b]:
        return False, 0.0

    old_obj = get_objective(solution, conflict_set, student_exams)
    solution[a], solution[b] = solution[b], solution[a]
    new_obj = get_objective(solution, conflict_set, student_exams)
    delta   = new_obj - old_obj

    if delta <= 0 or _sa_accept(delta, temp):
        return True, delta
    solution[a], solution[b] = solution[b], solution[a]   # revert
    return False, 0.0


def heuristic_kempe_chain(solution, conflict_set, student_exams, exam_students_map, n_slots, temp):
    """Kempe-chain swap between two slots; evaluate via full recount (safe)."""
    if n_slots < 2:
        return False, 0.0

    s1, s2 = random.sample(range(n_slots), 2)
    exams_s1 = [e for e in range(len(solution)) if solution[e] == s1]
    if not exams_s1:
        return False, 0.0

    chain    = set()
    frontier = [random.choice(exams_s1)]
    chain.add(frontier[0])
    current_slot = {frontier[0]: s1}

    while frontier:
        nxt = []
        for exam in frontier:
            target = s2 if current_slot[exam] == s1 else s1
            for nb in conflict_set.get(exam, set()):
                if nb not in chain and solution[nb] == target:
                    chain.add(nb)
                    current_slot[nb] = target
                    nxt.append(nb)
        frontier = nxt

    old_obj = get_objective(solution, conflict_set, student_exams)
    for exam in chain:
        solution[exam] = s2 if solution[exam] == s1 else s1
    new_obj = get_objective(solution, conflict_set, student_exams)
    delta   = new_obj - old_obj

    if delta <= 0 or _sa_accept(delta, temp):
        return True, delta
    for exam in chain:                                      # revert
        solution[exam] = s2 if solution[exam] == s1 else s1
    return False, 0.0


def heuristic_slot_shuffle(solution, conflict_set, student_exams, exam_students_map, n_slots, temp):
    """Disperse all exams in one slot to random other slots; evaluate via full recount."""
    slot    = random.randrange(n_slots)
    victims = [e for e in range(len(solution)) if solution[e] == slot]
    if not victims:
        return False, 0.0

    other_slots = [s for s in range(n_slots) if s != slot]
    if not other_slots:
        return False, 0.0

    old_obj = get_objective(solution, conflict_set, student_exams)
    saved   = {e: solution[e] for e in victims}
    for e in victims:
        solution[e] = random.choice(other_slots)

    new_obj = get_objective(solution, conflict_set, student_exams)
    delta   = new_obj - old_obj

    if delta <= 0 or _sa_accept(delta, temp):
        return True, delta
    for e, s in saved.items():                              # revert
        solution[e] = s
    return False, 0.0


# ─────────────────────────── ADAPTIVE SELECTOR ───────────────────────────────

class AdaptiveSelector:
    """Epsilon-greedy selector with exponential moving-average scores."""

    def __init__(self, heuristics, epsilon=0.15, decay=0.97):
        self.heuristics = heuristics
        self.names      = [h.__name__ for h in heuristics]
        self.scores     = [1.0] * len(heuristics)
        self.calls      = [0]   * len(heuristics)
        self.epsilon    = epsilon
        self.decay      = decay

    def select(self):
        if random.random() < self.epsilon:
            idx = random.randrange(len(self.heuristics))
        else:
            idx = max(range(len(self.heuristics)), key=lambda i: self.scores[i])
        return idx, self.heuristics[idx]

    def update(self, idx, improved, delta_obj):
        """
        delta_obj < 0  -> objective improved  -> big reward
        improved=True but delta_obj >= 0 -> SA accepted worsening -> small reward
        not improved   -> rejected            -> small penalty
        """
        self.calls[idx] += 1
        if improved and delta_obj < 0:
            reward = 1.0 + abs(delta_obj) * 0.001
        elif improved:
            reward = 0.1
        else:
            reward = -0.1
        self.scores[idx] = self.decay * self.scores[idx] + (1 - self.decay) * reward
        self.scores[idx] = max(0.01, self.scores[idx])

    def stats(self):
        lines = ["[STATS] Heuristic performance:"]
        for i, name in enumerate(self.names):
            lines.append(f"  {name:35s} calls={self.calls[i]:6d}  score={self.scores[i]:.4f}")
        return "\n".join(lines)


# ─────────────────────────── MAIN SOLVER LOOP ────────────────────────────────

def hyper_heuristic_solve(n_exams, conflict_set, student_exams, exam_students_map,
                          name, time_limit, initial_temp, cooling_rate, n_slots=None):

    if n_slots is None:
        n_slots = DATASET_INFO.get(name, {"periods": 13})["periods"]

    solution = greedy_initial_solution(n_exams, conflict_set, n_slots)

    # Ground-truth counters — always computed from scratch, never drifted
    current_conflicts = count_conflicts(solution, conflict_set)
    current_penalty   = calculate_penalty(solution, student_exams)

    print(f"[INFO] Initial periods:   {n_slots}")
    print(f"[INFO] Initial conflicts: {current_conflicts} | Initial penalty: {current_penalty:.4f}")

    best_solution  = solution[:]
    best_conflicts = current_conflicts
    best_penalty   = current_penalty

    heuristics = [
        heuristic_exam_reinsertion,
        heuristic_random_move,
        heuristic_swap,
        heuristic_kempe_chain,
        heuristic_slot_shuffle,
    ]
    selector = AdaptiveSelector(heuristics, epsilon=0.15, decay=0.97)

    temp             = initial_temp
    start_time       = time.time()
    iteration        = 0
    last_improvement = 0
    STUCK_LIMIT      = 20_000

    while True:
        if time.time() - start_time >= time_limit:
            break

        idx, heuristic = selector.select()
        improved, d_obj = heuristic(
            solution, conflict_set, student_exams, exam_students_map, n_slots, temp
        )

        # Pass objective delta (correctly signed float) to selector
        selector.update(idx, improved, d_obj)

        if improved:
            # Always recompute ground truth after an accepted move — no drift possible
            true_conf = count_conflicts(solution, conflict_set)
            true_pen  = calculate_penalty(solution, student_exams)
            current_conflicts = true_conf
            current_penalty   = true_pen

            if (true_conf < best_conflicts or
                    (true_conf == best_conflicts and true_pen < best_penalty)):
                best_solution    = solution[:]
                best_conflicts   = true_conf
                best_penalty     = true_pen
                last_improvement = iteration
                print(f"[IMPROVED] iter={iteration} conflicts={best_conflicts} "
                      f"penalty={best_penalty:.4f} elapsed={time.time()-start_time:.1f}s")

        # Cool down
        temp = max(temp * cooling_rate, 0.001)

        # Restart from best if stuck
        if iteration - last_improvement > STUCK_LIMIT:
            solution          = best_solution[:]
            current_conflicts = best_conflicts
            current_penalty   = best_penalty
            temp              = initial_temp * 0.3
            last_improvement  = iteration

        iteration += 1

        if iteration % 1000 == 0:
            elapsed = time.time() - start_time
            print(f"[ITER {iteration:>8d}] best_conf={best_conflicts} | "
                  f"best_pen={best_penalty:.4f} | temp={temp:.4f} | elapsed={elapsed:.1f}s",
                  flush=True)

    print(selector.stats())
    return best_solution, best_conflicts, best_penalty


# ─────────────────────────── ENTRY POINT ─────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Exam Timetabling Solver (Hyper-Heuristics)")
    parser.add_argument("dataset", nargs="?", default=DATASET_NAME)
    parser.add_argument("--time-limit", type=int, default=TIME_LIMIT)
    parser.add_argument("--seed",    type=int, help="Random seed")
    parser.add_argument("--periods", type=int, help="Override number of time slots")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        print(f"[INFO] Random seed: {args.seed}")

    name   = args.dataset
    folder = DATASET_DIR
    for candidate in [
        DATASET_DIR,
        os.path.join(SCRIPT_DIR, "datasets"),
        os.path.join(SCRIPT_DIR, "..", "datasets"),
        os.path.join(SCRIPT_DIR, "..", "Micro Service",
                     "exam-planning-algorithms", "datasets"),
        "datasets",
    ]:
        if os.path.isdir(candidate):
            folder = candidate
            break

    exam_list, exam_map, student_exams, exam_students_map, conflict_set, n_exams = \
        load_dataset(name, folder)

    t0 = time.time()
    solution, conflicts, penalty = hyper_heuristic_solve(
        n_exams, conflict_set, student_exams, exam_students_map, name,
        time_limit=args.time_limit,
        initial_temp=INITIAL_TEMP,
        cooling_rate=COOLING_RATE,
        n_slots=args.periods,
    )
    elapsed = time.time() - t0

    print(f"[RESULT] Algorithm: Hyper-Heuristics | Time: {elapsed:.1f}s | Conflicts: {conflicts}")


if __name__ == "__main__":
    main()