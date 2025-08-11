# Traffic Management System with Human-in-the-Loop

A traffic incident management system that uses Neo4j knowledge graphs, LangChain, and LangGraph to generate VMS (Variable Message Signs) response plans with human approval workflow.

## Features

- **Neo4j Knowledge Graph**: Road network data with VMS equipment positioning
- **AI-Powered Analysis**: Event extraction, change analysis, and response plan generation
- **Psychology-Based Messaging**: VMS messages designed using cognitive and behavioral psychology
- **Human-in-the-Loop**: Manual approval system for critical traffic management decisions
- **LangSmith Integration**: Performance monitoring and tracking
  
## Latest update
- rpgv2human_2_agent.ipynb is the latest jupyter notebook, has 2 agents, one for plan generation and second to handle human feedback processing. Also utilizing interrupt now instead of input for human feedback.(Features have not been updated to main.py)
- rpgv2human.ipynb is the same as main.py

## Quick Start

1. **Setup Environment**:
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Setup system**:
   ```bash
   python scripts/setup_system.py
   ```
3. **Setup Graph**:

   Run All Knowledge_Graph_Creator.ipynb in archive after changing file paths to files to generate graph

4. **Run Demo**:
   ```bash
   python main.py interactive #custom query input
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



## Issues
- Chance of event_analyzed becoming false after human feedback causing endless loop
- Should be an issue of using input instead of interrupt during human feedback causing memory loss (input was used as it was a simple implementation for jupyter notebook tests)
- Have not extensively tested human feedback after adding auto update function
- main.py has not been tested fully, most tests were done in rpgjv2human.ipynb, might have issues
- The should_continue function used to control flow is very messy and needs refinement, is the cause for most of the above issues.
- Sometimes deprecated error occurs for gds.graph.drop, llm probebly did not add YIELD graphName (is a non issue as there deprecated function is the schema return function)
- Some of this issues may have been fixed in rpgv2human_2_agent.ipynb, interrupt was used instead for human in the loop, seperate agent for feedback processing to reduce confusion to the LLM in the system prompts.

## Next Step
- Rerouting logic added to VMS messages
- More detailed link properties
- More detailed Agency plans, time of arrival, time of departure .ie.
- Outline a proper fixed input template
- Look into combining plan and plan command nodes
- More refined outline of Affected Equipment Range, currently only by congestion length. No 3/3, 5/5 rule.
