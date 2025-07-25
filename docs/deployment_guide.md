# Deployment Guide

## Prerequisites
- Python 3.8+
- Neo4j Database
- OpenAI/Anthropic API Keys

## Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and configure
4. Run database setup: `python scripts/setup_database.py`

## Configuration
- Configure environment variables in `.env`
- Adjust settings in `config/settings.py`

## Running the System
- Development: Use notebooks in `notebooks/development/`
- Production: Run `python scripts/demo.py`

## Monitoring
- LangSmith integration for tracking
- Performance metrics collection
