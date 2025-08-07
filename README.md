# Traffic Management System with Human-in-the-Loop

A sophisticated traffic incident management system that uses Neo4j knowledge graphs, LangChain, and LangGraph to generate psychology-based VMS (Variable Message Signs) response plans with human approval workflow.

## Features

- **Neo4j Knowledge Graph**: Road network data with VMS equipment positioning
- **AI-Powered Analysis**: Event extraction, change analysis, and response plan generation
- **Psychology-Based Messaging**: VMS messages designed using cognitive and behavioral psychology
- **Human-in-the-Loop**: Manual approval system for critical traffic management decisions
- **LangSmith Integration**: Performance monitoring and tracking

## Quick Start

1. **Setup Environment**:
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Initialize Database**:
   ```bash
   python scripts/setup_database.py
   ```

3. **Run Demo**:
   ```bash
   python scripts/demo.py
   ```

## Project Structure

- `config/`: Database and LLM configuration
- `src/`: Core application code
- `prompts/`: AI prompts and guidelines
- `tests/`: Unit and integration tests
- `notebooks/`: Development and exploration notebooks
- `scripts/`: Utility scripts
- `monitoring/`: Performance tracking
- `docs/`: Documentation

## Usage

```
python scripts/setup_system.py

python main.py interactive 
```

See `docs/api_reference.md` for detailed API documentation.
