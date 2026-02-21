# 🎓 Exam Timetabling Optimization — Algorithm Showdown

> **Can we schedule hundreds of exams without a single conflict? Let's find out.**

We're tackling one of the classic problems in computer science: **Exam Timetabling** (Planification des Examens). The challenge is simple to explain but hard to solve — assign every exam to a time slot so that **no student has two exams at the same time**.

---

## 🎯 Our Objectives

| Priority | Constraint | Description |
|----------|-----------|-------------|
| 🔴 **#1 — Hard Constraint** | Zero Conflicts | No student should have 2 exams at the same time. Non-negotiable. |
| 🟡 **#2 — Soft Constraint** | Student Comfort | Spread exams out as much as possible. No back-to-back exam days. |

---

## 🏁 The Great Algorithm Race

We're each implementing a **different optimization algorithm**, then running them all on the **same machine** with the **same dataset** to crown the fastest and most efficient approach.

| # | Algorithm | Status |
|---|-----------|--------|
| 🔥 | **Recuit Simulé** *(Simulated Annealing)* | `In Progress` |
| 🚫 | **Recherche Tabou** *(Tabu Search)* | `In Progress` |
| 🔀 | **Shuffling & Hyper-heuristiques** | `In Progress` |
| 🧬 | **Algorithmes Génétiques** *(Genetic Algorithms)* | `In Progress` |
| 🐜 | **Colonie de Fourmis** *(Ant Colony Optimization)* | `In Progress` |

---

## 📁 Project Structure
```
Opti-Exam-Project/
│
├── datasets/
│   ├── sta-f-83.crs          # St. Andrews — small dataset
│   ├── sta-f-83.stu
│   ├── car-s-91.crs          # Carleton — large dataset
│   └── car-s-91.stu
│
├── algorithms/
│   ├── 1_recuit_simule.py
│   ├── 2_recherche_tabou.py
│   ├── 3_hyper_heuristique.py
│   ├── 4_algorithme_genetique.py
│   └── 5_colonie_fourmis.py
│
└── README.md
```

---

## 📦 The Datasets — Toronto Benchmark

We're using the well-known **Toronto Benchmark** datasets, found in the `/datasets` folder.

###  `sta-f-83` — St. Andrews University *(Small)*
We're using this dataset during **development and debugging**. It's small and runs fast, making it perfect for testing whether our algorithm actually works before throwing the big data at it.

###  `car-s-91` — Carleton University *(Large)*
This is our **final benchmark**. We're running every algorithm on this dataset for the official comparison. It's massive — this is where we'll truly see which algorithm holds up under pressure.

---

### 📄 Understanding the Files

Each dataset comes with two files:

- **`.crs` (Courses file)** — Lists every exam and how many students are enrolled in it.
- **`.stu` (Students file)** — Lists each student's exams. If a student is in Exam A and Exam B → those two **cannot** be scheduled at the same time. This is where conflicts come from!

---

## ⚙️ Environment & Prerequisites

To make sure we all get fair, reproducible results on the **same environment** during the final test:

- **Language:** `Python 3.10+` *(or update here if someone uses Java/C++)*
- **Libraries:** *(list any specific libraries your algorithm needs)*
- **Machine:** We'll run the final comparison on a single, agreed-upon machine.

---

## 🛠️ How We Work on This Repo

1. **Pick your algorithm** from the list above.
2. **Create your branch** before writing any code:
```bash
   git checkout -b feature-[your-algo-name]
   # Example: git checkout -b feature-tabu-search
```
3. Go to `/algorithms` and work on your file.
4. Your code **must read** the `.crs` and `.stu` files from the `/datasets` folder.

---

## 📤 Required Output Format

To make our final comparison clean and fair, **every algorithm must print this exact format** at the end:
```
[RESULT] Algorithm: <Name> | Time: <X.Xs> | Conflicts: <N>
```

**Example:**
```
[RESULT] Algorithm: Tabu Search | Time: 14.2s | Conflicts: 0
```

> ⚠️ Please don't change the format — we're parsing these results for our comparison table!

---

## 📊 Final Results

> *We'll fill this in once everyone finishes their implementation!*

| Algorithm | Dataset | Time (seconds) | Conflicts |
|-----------|---------|----------------|-----------|
| 🔥 Recuit Simulé | `car-s-91` | `N/A` | `N/A` |
| 🚫 Recherche Tabou | `car-s-91` | `N/A` | `N/A` |
| 🔀 Hyper-heuristiques | `car-s-91` | `N/A` | `N/A` |
| 🧬 Algo Génétique | `car-s-91` | `N/A` | `N/A` |
| 🐜 Colonie de Fourmis | `car-s-91` | `N/A` | `N/A` |

---

## 👥 Team

| Member | Algorithm |
|--------|-----------|
| [Aymen Abidi](https://github.com/aymen74407) | Recuit Simulé |
| [Asma Sellami](https://github.com/asmasellami) | Recherche Tabou |
| [Salem Ajimi](https://github.com/Salem-ops220) | Hyper-heuristiques |
| [Mayssen Jemmali](https://github.com/MayssenJemmali) | Algo Génétique |
| [Oumaima Houimel](https://github.com/OumaimaHouimell) | Colonie de Fourmis |

---

<div align="center">

**Good luck to everyone. May the fastest algorithm win. 🚀**

</div>