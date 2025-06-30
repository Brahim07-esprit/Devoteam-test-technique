from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, MessagesState, START
from openai import OpenAI
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import subprocess
import time
import re
import sys
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import json
import io
from contextlib import redirect_stdout

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analyzer import InfrastructureAnalyzer

import main

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

@tool
def run_analyzer(input_file: str = "realtime_metrics.json") -> str:
    """
    Run the infrastructure analyzer on the specified input file.
    
    Args:
        input_file: Path to the JSON file with infrastructure metrics
    """
    if not os.path.exists(input_file):
        return f"Error: File {input_file} not found"
    
    try:
        analyzer = InfrastructureAnalyzer()
        metrics = analyzer.load_data(input_file)
        analysis = analyzer.detect_anomalies(metrics)
        
        result = f"\nAnalysis Summary:\n"
        result += f"  - Total metrics analyzed: {analysis['total_metrics']}\n"
        result += f"  - Total anomalies detected: {analysis['total_anomalies']}\n"
        result += f"  - Critical severity count: {analysis['critical_count']}\n\n"
        
        result += "Severity Distribution:\n"
        for severity, count in analysis['severity_distribution'].items():
            result += f"  - {severity.capitalize()}: {count}\n"
        
        result += "\nAnomaly Type Distribution:\n"
        sorted_types = sorted(analysis['anomaly_breakdown'].items(), key=lambda x: x[1], reverse=True)
        for atype, count in sorted_types[:5]:
            result += f"  - {atype}: {count}\n"
        
        if analysis['service_issues']:
            result += "\nService Issues:\n"
            for service, count in analysis['service_issues'].items():
                result += f"  - {service}: {count} issues\n"
        
        return result
    except Exception as e:
        return f"Error analyzing metrics: {str(e)}"

@tool
def run_full_pipeline(input_file: str = "realtime_metrics.json") -> str:
    """
    Run the full infrastructure analysis pipeline including recommendations.
    
    Args:
        input_file: Path to the JSON file with infrastructure metrics
    """
    if not os.path.exists(input_file):
        return f"Error: File {input_file} not found"
    
    try:
        f = io.StringIO()
        with redirect_stdout(f):
            # Set up sys.argv for main.py
            sys.argv = ['main.py', input_file]
            main.main()
        
        output = f.getvalue()
        return output
    except Exception as e:
        return f"Error running full pipeline: {str(e)}"

@tool
def generate_metric_graph(metric_name: str, input_file: str = "realtime_metrics.json") -> str:
    """
    Generate a graph for the specified metric from the infrastructure data.
    
    Args:
        metric_name: The name of the metric to graph (e.g., cpu_usage, memory_usage, etc.)
        input_file: Path to the JSON file with infrastructure metrics
    """
    valid_metrics = [
        'cpu_usage', 'memory_usage', 'latency_ms', 'disk_usage',
        'network_in_kbps', 'network_out_kbps', 'io_wait', 'thread_count',
        'active_connections', 'error_rate', 'uptime_seconds',
        'temperature_celsius', 'power_consumption_watts'
    ]
    
    if metric_name not in valid_metrics:
        return f"Error: Invalid metric name '{metric_name}'. Valid metrics are: {', '.join(valid_metrics)}"
    
    if not os.path.exists(input_file):
        return f"Error: File {input_file} not found"
    
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        if not data:
            return f"Error: No data found in {input_file}. Please run the realtime analyzer first to collect some data."
        
        df = pd.DataFrame(data)
        
        if 'service_status' in df.columns:
            try:
                df['database_status'] = df['service_status'].apply(lambda x: x['database'])
                df['api_gateway_status'] = df['service_status'].apply(lambda x: x['api_gateway'])
                df['cache_status'] = df['service_status'].apply(lambda x: x['cache'])
                
                df.drop(columns=['service_status'], inplace=True)
            except:
                pass
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(by='timestamp', ascending=True).reset_index(drop=True)
        
        plt.figure(figsize=(12, 6))
        plt.plot(df['timestamp'], df[metric_name])
        plt.xlabel('Timestamp')
        plt.ylabel(metric_name.replace('_', ' ').title())
        plt.title(f'{metric_name.replace("_", " ").title()} Over Time')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return f"Graph generated for {metric_name}. Here's the base64 encoded image:\n{image_base64}"
    except Exception as e:
        return f"Error generating graph: {str(e)}"

@tool
def list_available_metrics(input_file: str = "realtime_metrics.json") -> str:
    """
    List all available metrics in the data file.
    
    Args:
        input_file: Path to the JSON file with infrastructure metrics
    """
    if not os.path.exists(input_file):
        return f"Error: File {input_file} not found"
    
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
            
        if not data:
            return "No metrics data available yet. Please run the realtime analyzer first to collect data."
            
        df = pd.DataFrame(data)
        
        columns = [col for col in df.columns if col != 'service_status']
        
        if 'service_status' in df.columns:
            try:
                sample = df['service_status'].iloc[0]
                for key in sample.keys():
                    columns.append(f"{key}_status")
            except:
                pass
        
        return f"Available metrics: {', '.join(columns)}"
    except Exception as e:
        return f"Error listing metrics: {str(e)}"

@tool
def clear_metrics(input_file: str = "realtime_metrics.json") -> str:
    """
    Clear the metrics file by replacing it with an empty array.
    Use this to reset the metrics collection.
    
    Args:
        input_file: Path to the JSON file with infrastructure metrics to clear
    """
    try:
        with open(input_file, 'w') as f:
            json.dump([], f)
        return f"Successfully cleared metrics in {input_file}. The file now contains an empty array."
    except Exception as e:
        return f"Error clearing metrics file: {str(e)}"

@tool
def run_realtime_analyzer() -> str:
    """
    Run the realtime analyzer to collect current system metrics.
    This will start monitoring the system in real-time and save metrics to realtime_metrics.json.
    """
    try:
        
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'realtime_analysis', 'realtime_analyzer.py')
        
        try:
            subprocess.run(['pkill', '-9', '-f', 'realtime_analysis/realtime_analyzer.py'], stderr=subprocess.DEVNULL)
            print("Killed any existing monitoring processes")
            time.sleep(1)
        except:
            pass
        
        output_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'realtime_metrics.json')
        with open(output_file, 'w') as f:
            json.dump([], f)
        print(f"Created empty file before starting analyzer: {output_file}")
        
        cmd = f"nohup python3 {script_path} > realtime_analyzer.log 2>&1 &"
        subprocess.run(cmd, shell=True, check=True)
        
        time.sleep(2)
        
        check_cmd = "ps aux | grep -v grep | grep realtime_analysis/realtime_analyzer.py"
        result = subprocess.run(check_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if not result.stdout.strip():
            return "Error: Failed to start the realtime analyzer process. Check realtime_analyzer.log for details."
        
        return """I'm starting the real-time monitoring process now.

The monitoring process has been launched and is actively collecting metrics about your system's performance. All previous data has been cleared, and new metrics will use the current Paris time (UTC+2).

The metrics include:
- CPU usage
- Memory usage
- Disk usage
- Network I/O
- Temperature
- And more...

You can now use the 'list_available_metrics' command to see all available metrics, or 'generate_metric_graph' to visualize a specific metric.

The monitoring will continue running in the background until you close this application."""
    except Exception as e:
        return f"Error starting realtime analyzer: {str(e)}"

llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools([
    run_analyzer, 
    run_full_pipeline, 
    generate_metric_graph, 
    list_available_metrics,
    run_realtime_analyzer
])

def router(state):
    """Router node that determines which action to take based on user query"""
    print("Router node processing...")
    
    last_message = state["messages"][-1].content
    
    routing_prompt = f"""
    You are an infrastructure monitoring assistant. Based on the user's query, determine which action to take.
    
    User query: {last_message}
    
    Choose one of the following actions:
    1. "analyze" - If the user wants to analyze EXISTING infrastructure metrics without recommendations
    2. "full_pipeline" - If the user wants to run the full analysis with recommendations
    3. "graph" - If the user wants to visualize a specific metric
    4. "list_metrics" - If the user wants to know what metrics are available
    5. "realtime_analyzer" - If the user wants to START or RUN real-time monitoring or collection of new metrics
    6. "clear_metrics" - If the user wants to clear, reset, or delete metrics data
    7. "general" - For general questions or if none of the above apply
    
    IMPORTANT: If the user mentions "run the realtime analyzer", "start monitoring", "collect metrics", or similar phrases about STARTING a process, choose "realtime_analyzer", NOT "analyze".
    
    Respond with just the action name, nothing else.
    """
    
    response = llm.invoke(routing_prompt)
    route = response.content.strip().lower()
    
    print(f"Routing decision: {route}")
    
    if "realtime" in route or "monitor" in route:
        return {"next": "realtime_analyzer_node"}
    elif "analyze" in route:
        return {"next": "analyze_node"}
    elif "full" in route or "pipeline" in route:
        return {"next": "full_pipeline_node"}
    elif "graph" in route:
        return {"next": "graph_node"}
    elif "list" in route or "metrics" in route and "clear" not in route:
        return {"next": "list_metrics_node"}
    elif "clear" in route or "reset" in route or "delete" in route:
        return {"next": "clear_metrics_node"}
    else:
        return {"next": "general_node"}

def analyze_node(state):
    """Run the analyzer on the metrics data"""
    print("Running analyzer...")
    
    query = state["messages"][-1].content
    
    tool_response = run_analyzer.invoke({})
    
    response_content = f"""I've analyzed the real-time metrics data collected so far.

{tool_response}

Based on this analysis, I can provide more detailed insights or generate visualizations for specific metrics. Let me know if you'd like to see graphs of any particular metrics or if you'd like me to run the full analysis pipeline with recommendations."""
    
    state["messages"].append(AIMessage(content=response_content))
    
    return state

def full_pipeline_node(state):
    """Run the full pipeline including recommendations"""
    print("Running full pipeline...")
    
    query = state["messages"][-1].content
    
    tool_response = run_full_pipeline.invoke({})
    
    response_content = f"""I've run the full analysis pipeline on your real-time metrics data.

The analysis has detected various anomalies and generated recommendations to address them.

Here's a summary of the analysis:
{tool_response}

The detailed recommendations have been saved to a JSON file. You can view them in the Recommendations page of the dashboard."""
    
    state["messages"].append(AIMessage(content=response_content))
    
    return state

def graph_node(state):
    """Generate a graph for a specific metric"""
    print("Generating graph...")
    
    query = state["messages"][-1].content
    
    extract_prompt = f"""
    Extract the specific metric name from the user query that they want to visualize in a graph.
    
    User query: "{query}"
    
    Available metrics:
    - cpu_usage
    - memory_usage
    - latency_ms
    - disk_usage
    - network_in_kbps
    - network_out_kbps
    - io_wait
    - thread_count
    - active_connections
    - error_rate
    - uptime_seconds
    - temperature_celsius
    - power_consumption_watts
    
    Return ONLY the exact metric name from the list above that best matches what the user is asking for.
    If you're unsure, return "cpu_usage" as the default.
    """
    
    metric_response = llm.invoke(extract_prompt)
    metric_name = metric_response.content.strip().lower()
    
    print(f"Extracted metric: {metric_name}")
    
    tool_response = generate_metric_graph.invoke({
        "metric_name": metric_name
    })
    
    if "Error" in tool_response:
        response_content = f"I'm sorry, I couldn't generate a graph for {metric_name}. {tool_response}"
    else:
        base64_match = re.search(r"Here's the base64 encoded image:\n([A-Za-z0-9+/=]+)", tool_response)
        if base64_match:
            base64_data = base64_match.group(1)
            response_content = f"""I've generated a graph showing {metric_name.replace('_', ' ')} over time.

The graph shows how {metric_name.replace('_', ' ')} varies across the monitoring period. This visualization can help identify patterns, spikes, or anomalies in your infrastructure.

Here's the base64 encoded image:
{base64_data}"""
        else:
            response_content = f"I generated a graph for {metric_name}, but couldn't extract the image data."
    
    state["messages"].append(AIMessage(content=response_content))
    return state

def list_metrics_node(state):
    """List available metrics"""
    print("Listing metrics...")
    
    tool_response = list_available_metrics.invoke({})
    
    response_content = f"""Here are all the metrics available in your monitoring data:

{tool_response}

You can ask me to show you a graph of any of these metrics, or to analyze the data for anomalies."""
    
    state["messages"].append(AIMessage(content=response_content))
    
    return state

def realtime_analyzer_node(state):
    """Run the realtime analyzer"""
    print("Running realtime analyzer...")
    
    tool_response = run_realtime_analyzer.invoke({})
    
    response_content = tool_response
    
    state["messages"].append(AIMessage(content=response_content))
    return state

def clear_metrics_node(state):
    """Clear the metrics file"""
    print("Clearing metrics file...")
    
    tool_response = clear_metrics.invoke({})
    
    response_content = f"""I've cleared the metrics file. {tool_response}

You can now start fresh with new metrics collection by asking me to run the realtime analyzer."""
    
    state["messages"].append(AIMessage(content=response_content))
    return state

def general_node(state):
    """Handle general questions"""
    print("Handling general query...")
    
    query = state["messages"][-1].content
    response = llm.invoke(f"""
    You are an infrastructure monitoring assistant. Answer the user's question:
    
    {query}
    
    If they're asking about infrastructure metrics, analysis, or visualization, suggest they try asking for:
    - Analysis of infrastructure metrics
    - Running the full analysis pipeline with recommendations
    - Generating a graph for a specific metric (like CPU usage, memory usage, etc.)
    - Listing available metrics
    """)
    
    state["messages"].append(AIMessage(content=response.content))

    return state

def define_graph():
    workflow = StateGraph(MessagesState)
    
    workflow.add_node("router", router)
    workflow.add_node("analyze_node", analyze_node)
    workflow.add_node("full_pipeline_node", full_pipeline_node)
    workflow.add_node("graph_node", graph_node)
    workflow.add_node("list_metrics_node", list_metrics_node)
    workflow.add_node("realtime_analyzer_node", realtime_analyzer_node)
    workflow.add_node("clear_metrics_node", clear_metrics_node)
    workflow.add_node("general_node", general_node)
    
    workflow.add_edge(START, "router")
    workflow.add_conditional_edges(
        "router",
        lambda x: x["next"],
        {
            "analyze_node": "analyze_node",
            "full_pipeline_node": "full_pipeline_node",
            "graph_node": "graph_node",
            "list_metrics_node": "list_metrics_node",
            "realtime_analyzer_node": "realtime_analyzer_node",
            "clear_metrics_node": "clear_metrics_node",
            "general_node": "general_node"
        }
    )
    workflow.add_edge("analyze_node", END)
    workflow.add_edge("full_pipeline_node", END)
    workflow.add_edge("graph_node", END)
    workflow.add_edge("list_metrics_node", END)
    workflow.add_edge("realtime_analyzer_node", END)
    workflow.add_edge("clear_metrics_node", END)
    workflow.add_edge("general_node", END)
    
    return workflow.compile()

compiled_graph = define_graph()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
    else:
        user_input = "Show me a graph of CPU usage over time"
    
    initial_state = {"messages": [HumanMessage(content=user_input)]}
    result = compiled_graph.invoke(initial_state)
    
    print("\nAgent Response:")
    print("-" * 50)
    for message in result["messages"]:
        if message.type == "human":
            print(f"User: {message.content}")
        else:
            print(f"Agent: {message.content}")