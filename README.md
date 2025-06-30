https://github.com/user-attachments/assets/4a8ceb9e-4b73-46fd-9797-2e8b4a65779b

# Infrastructure Monitoring System

This system combines real-time monitoring with AI-powered analysis to detect anomalies and provide actionable recommendations, demonstrating a practical application of AI in DevOps.

## Overview

This project provides a modular infrastructure monitoring solution with:
- Real-time metrics collection and visualization
- Anomaly detection using statistical methods
- AI-powered recommendations via OpenAI integration
- Interactive agent interface for natural language queries

## Quick Start (Docker)

```bash
# Clone and setup
git clone <repository-url>
cd project_devoteam
cp env.example .env  # Add your OpenAI API key

# Run with Docker
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
docker compose run --rm streamlit python analyzer.py data/rapport.json

# Run the main pipeline with recommendations
docker compose run --rm streamlit python main.py data/rapport.json

# Analyze real-time collected data
docker compose run --rm streamlit python -m realtime_analysis.analyze_realtime

# Start the real-time metrics collector
docker compose run --rm streamlit python -m realtime_analysis.realtime_analyzer
```

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
├── agent/               # LangGraph-based agent system
├── realtime_analysis/   # Real-time monitoring components
├── streamlit/           # Dashboard interface
├── analyzer.py          # Core analysis logic
├── models.py            # Data models
└── main.py              # Pipeline orchestration
```

## Troubleshooting

**No Data in Dashboard**: Go to the Agent tab and type "run the realtime analyzer"

**OpenAI API Issues**: Check your API key in .env file and restart containers

**Missing Data File**: Create a data directory with `mkdir -p data` before running scripts that require input files 
