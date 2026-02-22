import random
import time

# ===============================
# PARAMÈTRES ACO
# ===============================
N_ANTS = 20        # plus d'ants pour meilleure exploration
N_ITERATIONS = 50
ALPHA = 1          # influence des phéromones
BETA = 3           # influence de l'attractivité (plus forte pour éviter conflits)
RHO = 0.3          # taux d'évaporation réduit pour renforcer les bonnes solutions
Q = 100
MAX_SLOTS = 10     # nombre maximum de créneaux

# ===============================
# LECTURE DES FICHIERS
# ===============================
def read_crs(filename):
    """
    Lecture du fichier .crs
    Renvoie : matrice de conflit n_exams x n_exams
    """
    exams = []
    with open(filename, 'r') as f:
        for line in f:
            exams.append(list(map(int, line.strip().split())))
    
    n = len(exams)
    conflict_matrix = [[0]*n for _ in range(n)]
    
    for i in range(n):
        for j in range(i+1, n):
            if len(set(exams[i]) & set(exams[j])) > 0:
                conflict_matrix[i][j] = 1
                conflict_matrix[j][i] = 1
    return conflict_matrix

# ===============================
# FONCTION DE COUT
# ===============================
def compute_cost(solution, conflict_matrix):
    cost = 0
    n = len(solution)
    for i in range(n):
        for j in range(i+1, n):
            if solution[i] == solution[j] and conflict_matrix[i][j] > 0:
                cost += conflict_matrix[i][j]
    return cost

# ===============================
# INIT PHÉROMONES
# ===============================
def init_pheromones(n, max_slot):
    return [[1.0 for _ in range(max_slot)] for _ in range(n)]

# ===============================
# CONSTRUCTION SOLUTION 
# ===============================
def construct_solution(n, max_slot, pheromones, conflict_matrix):
    solution = [-1]*n
    for exam in range(n):
        probabilities = []
        for slot in range(max_slot):
            # pénaliser les slots avec conflits
            conflict_penalty = sum(conflict_matrix[exam][j] for j in range(n) if solution[j]==slot)
            tau = pheromones[exam][slot] ** ALPHA
            eta = (1.0 / (1 + conflict_penalty)) ** BETA
            probabilities.append(tau * eta)

        total = sum(probabilities)
        probabilities = [p / total for p in probabilities]

        r = random.random()
        cumulative = 0
        for slot, prob in enumerate(probabilities):
            cumulative += prob
            if r <= cumulative:
                solution[exam] = slot
                break
    return solution

# ===============================
# MISE À JOUR PHÉROMONES 
# ===============================
def update_pheromones(pheromones, solutions, costs):
    n = len(pheromones)
    max_slot = len(pheromones[0])
    
    # Évaporation
    for i in range(n):
        for j in range(max_slot):
            pheromones[i][j] *= (1 - RHO)

    # Dépôt : favoriser les solutions avec moins de conflits
    min_cost = min(costs)
    for sol, cost in zip(solutions, costs):
        weight = Q / (1 + cost - min_cost + 1)  # meilleure solution → plus de phéromones
        for exam, slot in enumerate(sol):
            pheromones[exam][slot] += weight

# ===============================
# ALGORITHME ACO 
# ===============================
def ant_colony(conflict_matrix):
    n = len(conflict_matrix)
    pheromones = init_pheromones(n, MAX_SLOTS)
    
    best_solution = None
    best_cost = float('inf')
    
    start = time.time()
    for iteration in range(N_ITERATIONS):
        solutions = []
        costs = []

        for ant in range(N_ANTS):
            sol = construct_solution(n, MAX_SLOTS, pheromones, conflict_matrix)
            cost = compute_cost(sol, conflict_matrix)
            solutions.append(sol)
            costs.append(cost)

            if cost < best_cost:
                best_cost = cost
                best_solution = sol

        update_pheromones(pheromones, solutions, costs)
        print(f"Iteration {iteration+1} | Best cost: {best_cost}")

    end = time.time()
    slots_used = len(set(best_solution))
    print(f"\n[RESULT] Algorithm: ACO | Time: {round(end-start,2)}s | Conflicts: {best_cost} | Slots used: {slots_used}")
    
    return best_solution, best_cost

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    # Remplace ici par le nom de ton fichier déjà uploadé
    crs_file = "sta-f-83.crs"  
    conflict_matrix = read_crs(crs_file)

    print("Nombre d'examens :", len(conflict_matrix))

    best_solution, best_cost = ant_colony(conflict_matrix)