import random
import time
from collections import defaultdict

# =========================
# READ DATASET
# =========================

def read_crs(path):
    exams = []
    with open(path) as f:
        for line in f:
            exam, _ = line.split()
            exams.append(int(exam))
    return exams


def read_stu(path):
    students = []
    with open(path) as f:
        for line in f:
            exams = [int(x) for x in line.split()]
            students.append(exams)
    return students


# =========================
# BUILD CONFLICT GRAPH
# =========================

def build_conflicts(students):
    conflicts = defaultdict(set)

    for exams in students:
        for i in range(len(exams)):
            for j in range(i + 1, len(exams)):
                a = exams[i]
                b = exams[j]
                conflicts[a].add(b)
                conflicts[b].add(a)

    return conflicts


# =========================
# INITIAL SOLUTION
# =========================

def initial_solution(exams, timeslots=20):
    return {exam: random.randint(0, timeslots - 1) for exam in exams}


# =========================
# COST = number of conflicts
# =========================

def cost(solution, conflicts):
    c = 0
    for exam in solution:
        for neigh in conflicts[exam]:
            if solution[exam] == solution[neigh]:
                c += 1
    return c // 2  # double counted


# =========================
# TABU SEARCH
# =========================

def tabu_search(exams, conflicts, iterations=500, tabu_size=50, timeslots=20):
    solution = initial_solution(exams, timeslots)
    best = solution.copy()
    best_cost = cost(solution, conflicts)

    tabu_list = []

    for _ in range(iterations):

        best_move = None
        best_move_cost = float("inf")

        # explore neighbors
        for exam in exams:
            current_slot = solution[exam]

            for slot in range(timeslots):
                if slot == current_slot:
                    continue

                move = (exam, slot)

                if move in tabu_list:
                    continue

                # try move
                solution[exam] = slot
                c = cost(solution, conflicts)

                if c < best_move_cost:
                    best_move_cost = c
                    best_move = move

                # revert
                solution[exam] = current_slot

        if best_move is None:
            break

        # apply best move
        exam, slot = best_move
        solution[exam] = slot

        tabu_list.append(best_move)
        if len(tabu_list) > tabu_size:
            tabu_list.pop(0)

        c = cost(solution, conflicts)
        if c < best_cost:
            best_cost = c
            best = solution.copy()

    return best, best_cost


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    start = time.time()

    exams = read_crs("datasets/sta-f-83.crs")
    students = read_stu("datasets/sta-f-83.stu")

    conflicts = build_conflicts(students)

    best, best_cost = tabu_search(exams, conflicts)

    end = time.time()

    print(f"[RESULT] Algorithm: Tabu Search | Time: {round(end-start,2)}s | Conflicts: {best_cost}")