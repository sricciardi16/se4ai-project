# SE4AI Project: Orchestrated vs. Single-Pass Code Generation

This repository contains a framework for evaluating Large Language Models (LLMs) on repository-level source code generation. The benchmark targets a set of well-known Python repositories. 

The project evaluates and compares two distinct generation methods: a standard **single-pass** (zero-shot) approach, and an **orchestrated, iterative architecture**.

---

## 📂 Directory Structure

The repository is organized into distinct modules for data management, code generation, execution, and analysis:

### Benchmark Data

* **`data/`**: Contains the core dataset, including natural-language `specifications/` (the prompts fed to the LLMs) and `metadata/` (import names, dependencies, and original Git SHAs).
* **`tests_gen/`**: The ground-truth benchmark test suites. These tests use anonymized library imports and are used to evaluate the generated code.
* **`tests/`**: The intermediate calibrated tests using the original library names, preserved for provenance.

### Code Generation

* **`zero_shot_runner/`**: Scripts to prompt LLMs using a single-pass generation approach, outputting multi-file repositories.
* **`code_factory/`**: Scripts and configurations for the orchestrated, iterative generation approach, which divides the generation task into distinct, sequential roles.

### Evaluation & Execution
* **`eval_engine/`**: A deterministic Docker sandbox. It mounts generated code in a read-only environment, installs required dependencies, executes `pytest`, and extracts structured execution metrics.
* **`evaluation_runner/`**: Wrapper scripts that route the generated repositories into the evaluation engine and compile the resulting scorecards.

### Analysis & Processing
* **`analysis/`**: Scripts for data aggregation, AST-based dependency checking (to detect if models bypassed instructions by importing the original libraries), and a notebook (`analysis_notebook.py`) for generating comparative visualizations.
* **`data_processing/`**: The automated pipeline used to initially bootstrap, filter, calibrate, and format the benchmark dataset from legacy tests.

---

## 📦 Reproducibility and Raw Data

To maintain a clean version control history, large machine-generated artifacts and downloaded source code are not tracked in this repository.

**Accessing the Raw Data:**
The raw generated Python files, execution logs, and downloaded ground-truth repositories are available as a `.zip` archive on the **[Releases](../../releases)** page. 

To run the full analysis pipeline locally, download the archive and extract the folders (`evaluations/`, `repositories/`, etc.) directly into the root of this project. Note that the aggregated JSON metrics are already included in the `analysis/` directory, allowing for immediate visualization without downloading the raw data.



## ⚙️ Prerequisites

To run the evaluation engine and analysis scripts, you will need:
* **Python 3.10+**
* **Docker** (Required for the `eval_engine` sandbox)
* Required Python packages: `matplotlib`, `pyyaml`, `numpy` (A `requirements.txt` or standard virtual environment is recommended).

*Note: To run the code generation scripts (`zero_shot_runner` or `code_factory`), you must have the `Chase` framework configured locally with valid LLM API keys.*

---

## 🚀 Quick Start & Usage

### 1. Viewing the Analysis (No generation required)
The aggregated results are already included in the repository. To view the charts and metrics comparing the orchestrated architecture to the single-pass approach:
```bash
# Run the interactive analysis notebook (or execute it in VS Code / VSCodium)
python analysis/analysis_notebook.py
```

### 2. Running the Evaluation Engine
If you have downloaded the raw generated code from the Releases page and wish to re-evaluate a project inside the secure Docker sandbox:
```bash
# Evaluate a single generated repository
python evaluation_runner/evaluate_single.py --source-dir evaluations/zero_shot/gpt/generated_code/tabulate

# Evaluate an entire experiment batch
python evaluation_runner/evaluate_experiment.py --experiment-dir evaluations/agentic/gemini
```

### 3. Running Code Generation
To generate new code using the provided specifications (requires Chase configuration):
```bash
# Single-Pass Generation
python zero_shot_runner/generate_zero_shot.py --model gemini

# Orchestrated Architecture Generation
python code_factory/generate_agentic.py --model gemini
```

---

## 📚 References

The initial test logic used to bootstrap and calibrate this benchmark was sourced from the [RAL Bench](https://github.com/Wwstarry/RAL-Bench) dataset.