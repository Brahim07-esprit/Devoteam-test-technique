# Demo Video

https://github.com/user-attachments/assets/4a8ceb9e-4b73-46fd-9797-2e8b4a65779b

# Infrastructure Monitoring System

This system combines real-time monitoring with AI-powered analysis to detect anomalies and provide actionable recommendations, demonstrating a practical application of AI in DevOps.

## Overview

This project provides a modular infrastructure monitoring solution with:
- Real-time metrics collection and visualization
- Anomaly detection using statistical methods
- AI-powered recommendations via OpenAI integration
- Interactive agent interface for natural language queries

## Thought process

### 1. Manual Solution
Started by analyzing infrastructure data and creating Pydantic models (`src/core/models.py`) for data validation. Built manual scripts that run from command line to process metrics files and detect anomalies using statistical methods. Engineered prompts to generate AI recommendations, grouping anomalies to avoid excessive API calls.

### 2. Real-time Analyzer
Recognized the need for continuous monitoring rather than batch processing. Implemented real-time data collection and analysis to provide immediate insights into system performance.

### 3. Streamlit Interface + Agent
Considered users without IDE/Python knowledge and created a web interface using Streamlit. Added an interactive agent with LangGraph architecture for natural language interaction, allowing users to query the system conversationally.

## Quick Start (Docker)

```bash
# Clone and setup
git clone <repository-url>
cd project_devoteam
cp env.example .env  # Add your OpenAI API key

# Run with Docker (Dockerfile and docker-compose.yml are at the project root)
docker compose up
```

Access the dashboard at http://localhost:8501

## Running Individual Components

Each component can be run independently using Docker:

### Streamlit Dashboard
```bash
docker compose up streamlit
```

### Agent Interface
```bash
docker compose up agent
```

### Real-time Analyzer
```bash
docker compose up realtime-analyzer
```

### Running Specific Scripts

You can run individual scripts using either dedicated services or custom commands:

#### Option 1: Using dedicated services
```bash
# Run the main pipeline with recommendations
docker compose run main

# Run the standalone analyzer
docker compose run analyzer

# Analyze real-time collected data
docker compose run analyze-realtime
```

#### Option 2: Using custom commands
```bash
# Analyze a specific metrics file
docker compose run --rm streamlit python -m src.core.analyzer data/raw/rapport.json

# Run the main pipeline with recommendations
docker compose run --rm streamlit python scripts/main.py data/raw/rapport.json

# Analyze real-time collected data
docker compose run --rm streamlit python -m src.services.analyze_realtime

# Start the real-time metrics collector
docker compose run --rm streamlit python -m src.services.realtime_analyzer
```

> **Note:**
> - Always run commands from the project root so that `src/` is importable.
> - If you run scripts directly (not as modules), you may need to set `PYTHONPATH=.` or `PYTHONPATH=./src`.

## Components

- **Streamlit Dashboard**: Visualize metrics and recommendations
- **Agent Interface**: Natural language interaction with the system
- **Analyzer**: Core anomaly detection algorithms
- **Realtime Monitor**: Collects system metrics in real-time

## Usage

The agent interface supports commands like:
- "Run the realtime analyzer" - Starts collecting metrics in real-time
- "Show me a graph of CPU usage" - Visualizes CPU metrics
- "Analyze the metrics for anomalies" - Detects issues in collected data
- "Generate recommendations" - Provides AI-powered suggestions
- "Clear metrics" - Resets the metrics file to start fresh

## Project Structure

```
project_devoteam/
├── src/
│   ├── core/           # Core analysis logic and data models
│   ├── agents/         # LangGraph-based agent system
│   ├── services/       # Real-time monitoring components
│   ├── web/            # Dashboard interface (Streamlit)
│   └── utils/          # Utility functions
├── scripts/            # Pipeline orchestration and utility scripts
├── data/
│   ├── raw/            # Raw input data
│   ├── processed/      # Processed data
│   └── outputs/        # Generated outputs and logs
├── docker/             # (optional) Additional Docker configs
├── docker-compose.yml  # At project root
├── Dockerfile          # At project root
├── docs/               # Documentation
├── requirements.txt
├── .env.example
└── README.md
```

## Troubleshooting

**No Data in Dashboard**: Go to the Agent tab and type "run the realtime analyzer"

**OpenAI API Issues**: Check your API key in .env file and restart containers

**Missing Data File**: Place your metrics file in `data/raw/` before running scripts that require input files
