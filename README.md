# Needs Detector

CLI application for continuous needs validation using LLM.

## Installation

```bash
pip install -e .[dev]
```

## Offline Runnable Example Walkthrough

You can test the entire workflow offline using the `--provider mock` argument (which is the default).

### 1. Initialize Project
```bash
needs-detector init my-project
cd my-project
```

### 2. Add Idea & Sources
```bash
# Add an idea
echo "A new way to manage personal tasks easily." > idea.md
needs-detector add-idea idea.md

# Add a source document
echo "Users struggle with complex task managers." > my_source.md
needs-detector add-source my_source.md
```

### 3. Step 1: Draw (Generate Personas)
```bash
needs-detector draw --provider mock
```

### 4. Step 2: Explore (Generate Alternatives)
```bash
needs-detector explore --provider mock
```

### 5. Step 3: Listen (Interview Guide & Records)
```bash
needs-detector interview-guide

# Add a fake interview containing negative keywords for refutation
echo "I tried standard apps but 使わなかった (stopped using it) because it was too hard. 不満 (dissatisfied)." > my_interview.md
needs-detector add-interview my_interview.md
```

### 6. Step 4: Learn (Synthesize)
```bash
needs-detector learn --provider mock
```

### 7. Generate Final Report
```bash
needs-detector report
cat reports/final_report.md
```
