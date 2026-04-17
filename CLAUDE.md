# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a web test automation tool (TestTool) that automatically analyzes web page elements, generates test points, executes tests, and produces detailed reports. It uses Playwright for browser automation.

## Common Commands
### Setup
1. Activate virtual environment:
   ```bash
   cd web_test_tool
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Unix
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

### Run the tool
```bash
python main.py
```
Follow prompts to enter test URL, select account type, and choose tests to run.

### Run generated pytest tests
```bash
pytest tests/test_page_elements.py -v
```

## Architecture
### Core Modules
- `main.py`: Entry point. Handles user input (URL, account selection), coordinates analysis, test generation, and test execution.
- `page_analyzer.py`: Analyzes web page elements (buttons, inputs, links, forms, etc.) to generate prioritized test points.
- `test_runner.py`: Executes selected tests using Playwright. Handles test selection, execution, logging, failure screenshots, and HTML report generation.
- `pytest_generator.py`: Generates pytest-compatible test files in the `tests/` directory from the analyzed test points.

### Configuration
- `config.ini`: Stores tool configuration (browser type, timeouts, output directories, log level, etc.)

### Output Directories
- `screenshots/`: Screenshots of test failures
- `reports/`: HTML test execution reports
- `tests/`: Generated pytest test files
- `test.log`: Detailed execution logs
