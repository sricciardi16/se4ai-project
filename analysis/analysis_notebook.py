# %% [markdown]
# # SE4AI Benchmark Analysis
# Run these cells interactively in VSCodium/VS Code to analyze the benchmark results.

# %%
# ==========================================
# CELL 1: SETUP & DATA LOADING
# ==========================================
import json
from pathlib import Path
# Force matplotlib to not render images in the UI
import matplotlib
# Force matplotlib to not render images in the UI
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import numpy as np

from kroki import kroki_it

# --- Paths ---
BASE_DIR = Path(__file__).parent.resolve()
RESULTS_FILE = BASE_DIR / "benchmark_results.json"

# --- Load Data ---
if not RESULTS_FILE.exists():
    raise FileNotFoundError(f"Could not find {RESULTS_FILE.name}")

with open(RESULTS_FILE, "r", encoding="utf-8") as f:
    benchmark_data = json.load(f)

print(f"✅ Successfully loaded benchmark data.")
print(f"Approaches found: {list(benchmark_data.keys())}")

# --- Global Configuration & Styling ---
CATEGORIES = ["build_failure", "interface_failure", "dependency_violation", "testable"]

COLORS = {
    "build_failure": "#d62728",        # Red
    "interface_failure": "#ff7f0e",    # Orange
    "dependency_violation": "#7f7f7f", # Gray
    "testable": "#2ca02c"              # Green
}

LEGEND_LABELS = {
    "build_failure": "Build Failure",
    "interface_failure": "Interface Failure",
    "dependency_violation": "Dependency Violation (Cheated)",
    "testable": "Testable (Valid)"
}

MODEL_DISPLAY_NAMES = {
    "gemini": "Gemini 3.1 Pro Preview",
    "gpt": "gpt-oss 120b (medium)",
    "glm": "GLM-5",
    "qwen": "Qwen3 Coder 480B Instruct",
    "deepseek": "DeepSeek R1 0528"
}

print("✅ Configuration loaded. Ready for analysis.")


# %%
# ==========================================
# CELL 2: ANALYSIS 1 - ZERO-SHOT CATEGORIES
# ==========================================
print("="*80)
print("ANALYSIS 1: SINGLE PASS (ZERO-SHOT) STATISTICS")
print("="*80)

zero_shot_data = benchmark_data.get("zero_shot", {})
models_to_plot = list(zero_shot_data.keys())

# 1. Calculate Stats
zs_stats = {m: {cat: 0 for cat in CATEGORIES} for m in models_to_plot}

for model, projects in zero_shot_data.items():
    for project_id, metrics in projects.items():
        cat = metrics.get("category", "UNKNOWN")
        if cat in zs_stats[model]:
            zs_stats[model][cat] += 1

# 2. Print Console Table
print(f"\n{'Model'.ljust(28)} | Build Fail | Interface Fail | Cheated | Testable")
print("-" * 80)

for internal_model, counts in zs_stats.items():
    display_name = MODEL_DISPLAY_NAMES.get(internal_model, internal_model)
    short_name = display_name[:26] 
    
    print(f"{short_name.ljust(28)} | "
          f"{str(counts['build_failure']).rjust(10)} | "
          f"{str(counts['interface_failure']).rjust(14)} | "
          f"{str(counts['dependency_violation']).rjust(7)} | "
          f"{str(counts['testable']).rjust(8)}")
print("-" * 80)

# 3. Plot Chart
fig, ax = plt.subplots(figsize=(10, 6))
bottoms = np.zeros(len(models_to_plot))
x_labels = [MODEL_DISPLAY_NAMES.get(m, m).replace(" ", "\n") for m in models_to_plot]

for cat in CATEGORIES:
    values = [zs_stats[m][cat] for m in models_to_plot]
    ax.bar(
        x_labels, 
        values, 
        bottom=bottoms, 
        label=LEGEND_LABELS[cat], 
        color=COLORS[cat], 
        edgecolor='white',
        width=0.6
    )
    bottoms += np.array(values)

ax.set_ylabel('Number of Projects', fontsize=12, fontweight='bold')
ax.set_title('Single Pass Code Generation: Viability by Model', fontsize=14, fontweight='bold', pad=15)
ax.set_yticks(range(0, 28, 3))
ax.yaxis.grid(True, linestyle='--', alpha=0.7)
ax.set_axisbelow(True)
ax.legend(title="Outcome Category", bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
kroki_it(md_file="analysis.md")


# %%
# ==========================================
# CELL 3: ANALYSIS 2 - SINGLE PASS VS AGENTIC
# ==========================================
print("="*85)
print("ANALYSIS 2: SINGLE PASS VS AGENTIC COMPARISON")
print("="*85)

TARGET_MODELS = ["gemini", "gpt", "qwen"]
APPROACHES = ["zero_shot", "agentic"]

# 1. Calculate Stats
comp_stats = {m: {a: {c: 0 for c in CATEGORIES} for a in APPROACHES} for m in TARGET_MODELS}

for approach in APPROACHES:
    approach_data = benchmark_data.get(approach, {})
    for model in TARGET_MODELS:
        model_data = approach_data.get(model, {})
        for project_id, metrics in model_data.items():
            cat = metrics.get("category", "UNKNOWN")
            if cat in comp_stats[model][approach]:
                comp_stats[model][approach][cat] += 1

# 2. Print Console Table
print(f"\n{'Model'.ljust(18)} | {'Approach'.ljust(12)} | Build Fail | Interface Fail | Cheated | Testable")
print("-" * 85)

for model in TARGET_MODELS:
    m_name = MODEL_DISPLAY_NAMES.get(model, model).ljust(18)
    for approach in APPROACHES:
        a_name = "Single Pass" if approach == "zero_shot" else "Agentic"
        a_name = a_name.ljust(12)
        counts = comp_stats[model][approach]
        
        print(f"{m_name if approach == 'zero_shot' else ''.ljust(18)} | "
              f"{a_name} | "
              f"{str(counts['build_failure']).rjust(10)} | "
              f"{str(counts['interface_failure']).rjust(14)} | "
              f"{str(counts['dependency_violation']).rjust(7)} | "
              f"{str(counts['testable']).rjust(8)}")
    print("-" * 85)

# 3. Plot Chart
fig, ax = plt.subplots(figsize=(12, 6))

x_positions = [1, 2,  4, 5,  7, 8]
x_labels = ["Single Pass", "Agentic"] * 3
bottoms = np.zeros(len(x_positions))

for cat in CATEGORIES:
    values = [
        comp_stats["gemini"]["zero_shot"][cat], comp_stats["gemini"]["agentic"][cat],
        comp_stats["gpt"]["zero_shot"][cat], comp_stats["gpt"]["agentic"][cat],
        comp_stats["qwen"]["zero_shot"][cat], comp_stats["qwen"]["agentic"][cat]
    ]
    ax.bar(
        x_positions, 
        values, 
        bottom=bottoms, 
        label=LEGEND_LABELS[cat], 
        color=COLORS[cat], 
        edgecolor='white',
        width=0.8
    )
    bottoms += np.array(values)

ax.set_xticks(x_positions)
ax.set_xticklabels(x_labels, fontsize=10)

ax.text(1.5, -2.5, MODEL_DISPLAY_NAMES["gemini"], ha='center', fontsize=12, fontweight='bold')
ax.text(4.5, -2.5, MODEL_DISPLAY_NAMES["gpt"], ha='center', fontsize=12, fontweight='bold')
ax.text(7.5, -2.5, MODEL_DISPLAY_NAMES["qwen"], ha='center', fontsize=12, fontweight='bold')

ax.set_ylabel('Number of Projects', fontsize=12, fontweight='bold')
ax.set_title('Single Pass vs. Agentic Code Generation', fontsize=14, fontweight='bold', pad=15)
ax.set_yticks(range(0, 28, 3))
ax.yaxis.grid(True, linestyle='--', alpha=0.7)
ax.set_axisbelow(True)

ax.legend(title="Outcome Category", bbox_to_anchor=(1.05, 1), loc='upper left')

plt.subplots_adjust(bottom=0.15)
plt.tight_layout()
kroki_it(md_file="anal.md")

# %%
# ==========================================
# CELL 4: ANALYSIS 3 - SINGLE PASS AVERAGE SCORE
# ==========================================
print("="*80)
print("ANALYSIS 3: SINGLE PASS AVERAGE SUCCESS RATE")
print("="*80)

zero_shot_data = benchmark_data.get("zero_shot", {})

# 1. Calculate Average Scores
avg_scores = {}
for model, projects in zero_shot_data.items():
    if not projects:
        avg_scores[model] = 0.0
        continue
        
    total_score = 0.0
    for project_id, metrics in projects.items():
        # The success_rate is already 0.0 if it failed to build, failed interface, or cheated!
        total_score += metrics.get("success_rate", 0.0)
        
    avg_scores[model] = total_score / len(projects)

# Sort models by score (Highest to Lowest) for a better looking chart
sorted_models = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)

# 2. Print Console Table
print(f"\n{'Model'.ljust(28)} | Average Success Rate (%)")
print("-" * 55)

for internal_model, score in sorted_models:
    display_name = MODEL_DISPLAY_NAMES.get(internal_model, internal_model)
    short_name = display_name[:26] 
    print(f"{short_name.ljust(28)} | {score:>6.2f}%")
print("-" * 55)

# 3. Plot Chart
fig, ax = plt.subplots(figsize=(10, 6))

# Extract sorted data for plotting
x_labels = [MODEL_DISPLAY_NAMES.get(m, m).replace(" ", "\n") for m, _ in sorted_models]
y_values = [score for _, score in sorted_models]

# Create bars (using a nice professional blue)
bars = ax.bar(x_labels, y_values, color="#1f77b4", edgecolor='white', width=0.6)

# Add the exact percentage text on top of each bar
for bar in bars:
    height = bar.get_height()
    ax.annotate(f'{height:.1f}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha='center', va='bottom', fontweight='bold')

# Formatting
ax.set_ylabel('Average Success Rate (%)', fontsize=12, fontweight='bold')
ax.set_title('Single Pass: Average Success Rate by Model', fontsize=14, fontweight='bold', pad=15)
ax.set_ylim(0, 100) # Success rate is always between 0 and 100
ax.yaxis.grid(True, linestyle='--', alpha=0.7)
ax.set_axisbelow(True)

plt.tight_layout()
kroki_it(md_file="anal.md")


# %%
# ==========================================
# CELL 5: ANALYSIS 4 - AVERAGE SCORE COMPARISON
# ==========================================
print("="*80)
print("ANALYSIS 4: AVERAGE SUCCESS RATE (SINGLE PASS VS AGENTIC)")
print("="*80)

TARGET_MODELS = ["gemini", "gpt", "qwen"]
APPROACHES = ["zero_shot", "agentic"]

# 1. Calculate Average Scores
avg_scores_comp = {m: {"zero_shot": 0.0, "agentic": 0.0} for m in TARGET_MODELS}

for approach in APPROACHES:
    approach_data = benchmark_data.get(approach, {})
    for model in TARGET_MODELS:
        model_data = approach_data.get(model, {})
        if not model_data:
            continue
            
        total_score = sum(metrics.get("success_rate", 0.0) for metrics in model_data.values())
        avg_scores_comp[model][approach] = total_score / len(model_data)

# 2. Print Console Table
print(f"\n{'Model'.ljust(20)} | {'Single Pass'.rjust(12)} | {'Agentic'.rjust(12)} | {'Diff'.rjust(8)}")
print("-" * 62)

for model in TARGET_MODELS:
    m_name = MODEL_DISPLAY_NAMES.get(model, model).ljust(20)
    sp_score = avg_scores_comp[model]["zero_shot"]
    ag_score = avg_scores_comp[model]["agentic"]
    
    # Calculate the difference (Did the agentic approach improve the score?)
    diff = ag_score - sp_score
    diff_str = f"+{diff:.1f}" if diff > 0 else f"{diff:.1f}"
    
    print(f"{m_name} | {sp_score:>11.1f}% | {ag_score:>11.1f}% | {diff_str:>7}%")
print("-" * 62)

# 3. Plot Chart
fig, ax = plt.subplots(figsize=(10, 6))

# Set up the X-axis positions for grouped bars
x = np.arange(len(TARGET_MODELS))
width = 0.35  # Width of the bars

sp_values = [avg_scores_comp[m]["zero_shot"] for m in TARGET_MODELS]
ag_values = [avg_scores_comp[m]["agentic"] for m in TARGET_MODELS]

# Create the bars
rects1 = ax.bar(x - width/2, sp_values, width, label='Single Pass', color='#1f77b4', edgecolor='white')
rects2 = ax.bar(x + width/2, ag_values, width, label='Agentic', color='#ff7f0e', edgecolor='white')

# Function to add percentage labels on top of the bars
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

autolabel(rects1)
autolabel(rects2)

# Formatting
ax.set_ylabel('Average Success Rate (%)', fontsize=12, fontweight='bold')
ax.set_title('Average Success Rate: Single Pass vs Agentic', fontsize=14, fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels([MODEL_DISPLAY_NAMES.get(m, m) for m in TARGET_MODELS], fontsize=11, fontweight='bold')
ax.set_ylim(0, 100) # Lock Y-axis to 100%
ax.yaxis.grid(True, linestyle='--', alpha=0.7)
ax.set_axisbelow(True)

# Add legend outside the plot
ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1))

plt.tight_layout()
kroki_it(md_file="anal.md")

# %%
# ==========================================
# CELL 6: ANALYSIS 5 - PROJECT-LEVEL DELTAS
# ==========================================
print("="*80)
print("ANALYSIS 5: PROJECT-LEVEL DELTAS (AGENTIC vs SINGLE PASS)")
print("="*80)

TARGET_MODELS = ["gemini", "gpt", "qwen"]

for model in TARGET_MODELS:
    print(f"\n{'█'*60}")
    print(f" MODEL: {MODEL_DISPLAY_NAMES.get(model, model).upper()}")
    print(f"{'█'*60}")
    
    # Get data for this specific model
    sp_data = benchmark_data.get("zero_shot", {}).get(model, {})
    ag_data = benchmark_data.get("agentic", {}).get(model, {})
    
    # Get all unique projects evaluated by either approach
    all_projects = set(sp_data.keys()).union(set(ag_data.keys()))
    
    if not all_projects:
        print("  [No data found for this model]")
        continue

    # Calculate deltas
    project_deltas = []
    for project_id in all_projects:
        sp_score = sp_data.get(project_id, {}).get("success_rate", 0.0)
        ag_score = ag_data.get(project_id, {}).get("success_rate", 0.0)
        delta = ag_score - sp_score
        
        project_deltas.append({
            "project": project_id,
            "sp_score": sp_score,
            "ag_score": ag_score,
            "delta": delta
        })
        
    # Sort by Delta (Highest improvements at the top, regressions at the bottom)
    # If deltas are equal, sort alphabetically by project name
    project_deltas.sort(key=lambda x: (x["delta"], x["project"]), reverse=True)
    
    # Print the Table
    print(f"{'Project Name'.ljust(20)} | {'Single Pass'.rjust(11)} | {'Agentic'.rjust(11)} | {'Delta'.rjust(9)}")
    print("-" * 60)
    
    for item in project_deltas:
        proj = item["project"].ljust(20)
        sp = f"{item['sp_score']:>10.1f}%"
        ag = f"{item['ag_score']:>10.1f}%"
        
        # Format the delta string with a + sign for positive values
        d_val = item['delta']
        if d_val > 0:
            delta_str = f"+{d_val:.1f}%"
        elif d_val < 0:
            delta_str = f"{d_val:.1f}%"
        else:
            delta_str = "0.0%"
            
        print(f"{proj} | {sp} | {ag} | {delta_str:>8}")

# %%
# ==========================================
# CELL 7: ANALYSIS 6 - DIVERGING DELTA CHARTS (VERTICAL)
# ==========================================
print("="*80)
print("ANALYSIS 6: VERTICAL DIVERGING DELTA CHARTS")
print("="*80)

TARGET_MODELS = ["gemini", "gpt", "qwen"]

# Gather all unique projects
all_projects = set()
for model in TARGET_MODELS:
    sp_data = benchmark_data.get("zero_shot", {}).get(model, {})
    ag_data = benchmark_data.get("agentic", {}).get(model, {})
    all_projects.update(sp_data.keys())
    all_projects.update(ag_data.keys())

for model in TARGET_MODELS:
    sp_data = benchmark_data.get("zero_shot", {}).get(model, {})
    ag_data = benchmark_data.get("agentic", {}).get(model, {})
    
    # Calculate deltas for this specific model
    project_deltas = []
    for proj in all_projects:
        sp_score = sp_data.get(proj, {}).get("success_rate", 0.0)
        ag_score = ag_data.get(proj, {}).get("success_rate", 0.0)
        delta = ag_score - sp_score
        project_deltas.append((proj, delta))
        
    # Sort by Delta (Highest improvements on the left, regressions on the right)
    project_deltas.sort(key=lambda x: (x[1], x[0]), reverse=True)
    
    sorted_projs = [x[0] for x in project_deltas]
    deltas = [x[1] for x in project_deltas]
    
    # Assign colors
    colors = []
    for d in deltas:
        if d > 0:
            colors.append('#2ca02c') # Green
        elif d < 0:
            colors.append('#d62728') # Red
        else:
            colors.append('#cccccc') # Light Gray

    # Create a distinct figure for this model
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Plot vertical bars
    x_positions = np.arange(len(sorted_projs))
    bars = ax.bar(x_positions, deltas, color=colors, edgecolor='white', width=0.7)
    
    # Draw a solid black line across the middle (Zero Delta)
    ax.axhline(0, color='black', linewidth=1.5)
    
    # Formatting
    display_name = MODEL_DISPLAY_NAMES.get(model, model)
    ax.set_title(f'Performance Delta: Agentic vs. Single Pass\nModel: {display_name}', 
                 fontsize=16, fontweight='bold', pad=15)
    ax.set_ylabel('Delta (%)', fontsize=12, fontweight='bold')
    ax.set_ylim(-105, 115) # Give a little extra room for the text labels
    
    # X-axis formatting (Rotate project names so they fit)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(sorted_projs, rotation=45, ha='right', fontsize=10)
    
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    # Add text labels above/below the bars
    for bar, delta in zip(bars, deltas):
        if delta == 0:
            continue # Skip labeling 0
            
        y_offset = 3 if delta > 0 else -3
        va_align = 'bottom' if delta > 0 else 'top'
        
        ax.annotate(f'{delta:+.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, delta),
                    xytext=(0, y_offset),
                    textcoords="offset points",
                    ha='center', va=va_align, fontsize=8, fontweight='bold', rotation=90)

    plt.tight_layout()
    
    # Render the chart for this specific model
    print(f"Rendering chart for {display_name}...")
    kroki_it(md_file="anal.md")

print("\n[SUCCESS] All 3 distinct charts generated.")



# %%
# ==========================================
# CELL 8: ANALYSIS 7 - AGENTIC STABILITY (COMPLETED VS HALTED)
# ==========================================
print("="*80)
print("ANALYSIS 7: AGENTIC STABILITY (COMPLETED VS HALTED)")
print("="*80)

STORY_METRICS_FILE = BASE_DIR / "story_metrics.json"

if not STORY_METRICS_FILE.exists():
    print(f"[ERROR] Could not find {STORY_METRICS_FILE.name}. Run extract_story_metrics.py first.")
else:
    with open(STORY_METRICS_FILE, "r", encoding="utf-8") as f:
        story_data = json.load(f)

    TARGET_MODELS = ["gemini", "gpt", "qwen"]
    
    # 1. Calculate Stats
    stability_stats = {m: {"completed": 0, "halted": 0} for m in TARGET_MODELS}
    
    for model in TARGET_MODELS:
        model_data = story_data.get(model, {})
        for project_id, metrics in model_data.items():
            status = metrics.get("status", "UNKNOWN")
            if status == "COMPLETED_SUCCESSFULLY":
                stability_stats[model]["completed"] += 1
            else:
                # Groups HALTED_MAX_ITERATIONS and HALTED_EARLY together
                stability_stats[model]["halted"] += 1

    # 2. Print Console Table
    print(f"\n{'Model'.ljust(20)} | {'Completed'.rjust(10)} | {'Halted'.rjust(10)} | {'Completion Rate'.rjust(15)}")
    print("-" * 65)
    
    for model in TARGET_MODELS:
        m_name = MODEL_DISPLAY_NAMES.get(model, model).ljust(20)
        completed = stability_stats[model]["completed"]
        halted = stability_stats[model]["halted"]
        total = completed + halted
        
        comp_rate = (completed / total * 100) if total > 0 else 0.0
        
        print(f"{m_name} | {str(completed).rjust(10)} | {str(halted).rjust(10)} | {f'{comp_rate:.1f}%'.rjust(15)}")
    print("-" * 65)

    # 3. Plot Chart
    fig, ax = plt.subplots(figsize=(8, 6))
    
    x_labels = [MODEL_DISPLAY_NAMES.get(m, m).replace(" ", "\n") for m in TARGET_MODELS]
    completed_vals = [stability_stats[m]["completed"] for m in TARGET_MODELS]
    halted_vals = [stability_stats[m]["halted"] for m in TARGET_MODELS]
    
    # Plot Completed (Green)
    bars_comp = ax.bar(x_labels, completed_vals, label='Completed Successfully', color='#2ca02c', edgecolor='white', width=0.5)
    
    # Plot Halted (Red) on top of Completed
    bars_halt = ax.bar(x_labels, halted_vals, bottom=completed_vals, label='Halted (Death Spiral)', color='#d62728', edgecolor='white', width=0.5)
    
    # Add text annotations inside the bars
    for bar in bars_comp:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height / 2),
                        ha='center', va='center', color='white', fontweight='bold', fontsize=12)
                        
    for bar, bottom in zip(bars_halt, completed_vals):
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, bottom + height / 2),
                        ha='center', va='center', color='white', fontweight='bold', fontsize=12)

    # Formatting
    ax.set_ylabel('Number of Projects', fontsize=12, fontweight='bold')
    ax.set_title('Agentic Stability: Completed vs. Halted Projects', fontsize=14, fontweight='bold', pad=15)
    ax.set_yticks(range(0, 28, 3)) # Assuming ~27 projects max
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    # Add legend outside the plot
    ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1))

    plt.tight_layout()
    kroki_it(md_file="anal.md")


# %%
# ==========================================
# CELL 9: ANALYSIS 8 - THE "EQUALIZER" EFFECT (DEEP DIVE)
# ==========================================
import statistics
import itertools

print("="*80)
print("ANALYSIS 8: DOES THE BASE MODEL STILL MATTER IN AGENTIC? (DEEP DIVE)")
print("="*80)

TARGET_MODELS = ["gemini", "gpt", "qwen"]
APPROACHES = ["zero_shot", "agentic"]

# 1. Calculate Average Scores
scores = {"zero_shot": {}, "agentic": {}}

for approach in APPROACHES:
    approach_data = benchmark_data.get(approach, {})
    for model in TARGET_MODELS:
        model_data = approach_data.get(model, {})
        if not model_data:
            scores[approach][model] = 0.0
            continue
            
        total_score = sum(metrics.get("success_rate", 0.0) for metrics in model_data.values())
        scores[approach][model] = total_score / len(model_data)

# 2. Calculate Statistics
stats = {}
for approach in APPROACHES:
    model_scores = list(scores[approach].values())
    
    # Standard Deviation (Measures how spread out the scores are)
    stdev = statistics.stdev(model_scores) if len(model_scores) > 1 else 0.0
    
    # Pairwise Gaps (Compare every model to every other model)
    pairs = list(itertools.combinations(TARGET_MODELS, 2))
    pairwise_gaps = {}
    for m1, m2 in pairs:
        gap = abs(scores[approach][m1] - scores[approach][m2])
        pairwise_gaps[f"{m1} vs {m2}"] = gap
        
    stats[approach] = {
        "stdev": stdev,
        "pairwise_gaps": pairwise_gaps
    }

# 3. Print the Data Report
for approach in APPROACHES:
    app_name = "SINGLE PASS (ZERO-SHOT)" if approach == "zero_shot" else "AGENTIC FACTORY"
    print(f"\n--- {app_name} ---")
    
    # Print individual scores
    for model in TARGET_MODELS:
        print(f"  {MODEL_DISPLAY_NAMES.get(model, model).ljust(25)}: {scores[approach][model]:>5.1f}%")
        
    print("\n  Pairwise Gaps:")
    for pair, gap in stats[approach]["pairwise_gaps"].items():
        m1, m2 = pair.split(" vs ")
        n1 = MODEL_DISPLAY_NAMES.get(m1, m1)
        n2 = MODEL_DISPLAY_NAMES.get(m2, m2)
        print(f"    - {n1} vs {n2}: {gap:.1f}%")
        
    print(f"\n  📊 Standard Deviation: {stats[approach]['stdev']:.2f}")
    print("-" * 60)

# 4. The Conclusion
sp_stdev = stats["zero_shot"]["stdev"]
ag_stdev = stats["agentic"]["stdev"]

print("\n" + "="*80)
if ag_stdev < sp_stdev:
    reduction = ((sp_stdev - ag_stdev) / sp_stdev) * 100 if sp_stdev > 0 else 0
    print(f"💡 CONCLUSION: The Agentic architecture REDUCED the variance between models by {reduction:.1f}%.")
    print("   The Standard Deviation dropped, meaning the models' scores clustered closer together.")
    print("   This strongly suggests the framework acts as an 'equalizer'.")
elif ag_stdev > sp_stdev:
    increase = ((ag_stdev - sp_stdev) / sp_stdev) * 100 if sp_stdev > 0 else 0
    print(f"💡 CONCLUSION: The Agentic architecture INCREASED the variance between models by {increase:.1f}%.")
    print("   The Standard Deviation rose, meaning the gap between good and bad models widened.")
    print("   This suggests the framework amplifies the intelligence of the base model.")
else:
    print("💡 CONCLUSION: The variance between models remained exactly the same.")
print("="*80)

# %%
# ==========================================
# CELL 10: ANALYSIS 9 - TOP 3 WORSENED PROJECTS (REGRESSIONS)
# ==========================================
print("="*80)
print("ANALYSIS 9: TOP 3 WORSENED PROJECTS (SINGLE PASS -> AGENTIC)")
print("="*80)

# Including GLM as requested
TARGET_MODELS_EXT = ["gemini", "gpt", "qwen", "glm"]

for model in TARGET_MODELS_EXT:
    print(f"\n{'█'*60}")
    print(f" MODEL: {MODEL_DISPLAY_NAMES.get(model, model).upper()}")
    print(f"{'█'*60}")
    
    sp_data = benchmark_data.get("zero_shot", {}).get(model, {})
    ag_data = benchmark_data.get("agentic", {}).get(model, {})
    
    # Find projects that exist in both approaches for a fair comparison
    common_projects = set(sp_data.keys()).intersection(set(ag_data.keys()))
    
    if not common_projects:
        print("  [No overlapping data found for this model]")
        continue

    regressions = []
    
    for project_id in common_projects:
        sp_score = sp_data[project_id].get("success_rate", 0.0)
        ag_score = ag_data[project_id].get("success_rate", 0.0)
        delta = ag_score - sp_score
        
        # We only care about projects that got WORSE
        if delta < 0:
            regressions.append({
                "project": project_id,
                "sp_score": sp_score,
                "ag_score": ag_score,
                "delta": delta
            })
            
    # Sort by Delta ascending (most negative first)
    regressions.sort(key=lambda x: x["delta"])
    
    # Take the top 3 worst regressions
    top_3_worsened = regressions[:3]
    
    if not top_3_worsened:
        print("  🎉 No projects worsened! The Agentic approach only improved or maintained scores.")
        continue
        
    print(f"{'Project Name'.ljust(20)} | {'Single Pass'.rjust(11)} | {'Agentic'.rjust(11)} | {'Loss'.rjust(9)}")
    print("-" * 60)
    
    for item in top_3_worsened:
        proj = item["project"].ljust(20)
        sp = f"{item['sp_score']:>10.1f}%"
        ag = f"{item['ag_score']:>10.1f}%"
        loss = f"{item['delta']:.1f}%"
        
        print(f"{proj} | {sp} | {ag} | {loss:>8}")

# %%
