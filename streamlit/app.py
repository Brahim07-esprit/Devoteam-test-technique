from models import Metrics, ServiceStatus
import streamlit as st
import os
import json
import subprocess
import atexit
import time
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys
from io import BytesIO

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Infrastructure Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


if 'metrics_initialized' not in st.session_state:
    st.session_state.metrics_initialized = False

    try:
        subprocess.run(['pkill', '-9', '-f', 'realtime_analysis/realtime_analyzer.py'], stderr=subprocess.DEVNULL)
        print("Killed any existing monitoring processes at initial startup")
        time.sleep(1)
    except BaseException:
        pass


def initialize_metrics_file():
    if not st.session_state.metrics_initialized:
        metrics_file = "realtime_metrics.json"

        with open(metrics_file, 'w') as f:
            json.dump([], f)
        print("Created/emptied realtime_metrics.json at startup")

        st.session_state.metrics_initialized = True


def cleanup_processes():
    try:
        subprocess.run(['pkill', '-9', '-f', 'realtime_analysis/realtime_analyzer.py'], stderr=subprocess.DEVNULL)
        print("Killed any existing monitoring processes at exit")
    except BaseException:
        pass


atexit.register(cleanup_processes)

initialize_metrics_file()


def is_realtime_analyzer_running():
    try:
        result = subprocess.run("ps aux | grep -v grep | grep realtime_analysis/realtime_analyzer.py",
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        if result.stdout.strip():
            return True
        return False
    except BaseException:
        return False


@st.cache_data(ttl=2)
def load_metrics_data(file_path):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        st.error(f"Error loading metrics: {str(e)}")
        return []


def validate_metrics_data(data):
    try:
        valid_items = []
        invalid_items = []

        for item in data:
            try:
                if isinstance(item.get('timestamp'), str):
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))

                if 'service_status' in item and isinstance(item['service_status'], dict):
                    service_status = ServiceStatus(**item['service_status'])
                    item['service_status'] = service_status.model_dump()

                metrics = Metrics(**item)
                valid_items.append(item)
            except Exception as e:
                invalid_items.append((item, str(e)))

        return {
            'valid': len(invalid_items) == 0,
            'valid_count': len(valid_items),
            'invalid_count': len(invalid_items),
            'valid_items': valid_items,
            'invalid_items': invalid_items
        }
    except Exception as e:
        return {
            'valid': False,
            'error': str(e),
            'valid_count': 0,
            'invalid_count': len(data) if isinstance(data, list) else 0
        }


def show_metrics_dashboard(data_source="realtime"):
    st.title("Infrastructure Metrics Dashboard")

    if data_source == "realtime":
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("REFRESH METRICS", type="primary", use_container_width=True):
                load_metrics_data.clear()
                st.rerun()

        with col2:
            st.write(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

    if data_source == "realtime":
        analyzer_running = is_realtime_analyzer_running()

        # Display status
        if analyzer_running:
            st.success("Realtime analyzer is running and collecting metrics")
        else:
            st.info("ℹRealtime analyzer is not running. Go to the Agent tab and ask to 'run the realtime analyzer'")

    df = None
    data = None

    if data_source == "realtime":
        data = load_metrics_data("realtime_metrics.json")

        if not data:
            st.warning("No realtime metrics data available yet. Start the realtime analyzer to collect data.")
            return

        df = pd.DataFrame(data)
    else:
        if 'uploaded_data' in st.session_state and st.session_state.uploaded_data:
            data = st.session_state.uploaded_data
            df = pd.DataFrame(data)
        else:
            st.warning("No data uploaded. Please upload a JSON file in the Import Data tab.")
            return

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df = df.sort_values('timestamp').reset_index(drop=True)

    if 'service_status' in df.columns:
        try:
            df['database_status'] = df['service_status'].apply(lambda x: x['database'] if isinstance(x, dict) else x.get('database', 'unknown'))
            df['api_gateway_status'] = df['service_status'].apply(lambda x: x['api_gateway'] if isinstance(x, dict) else x.get('api_gateway', 'unknown'))
            df['cache_status'] = df['service_status'].apply(lambda x: x['cache'] if isinstance(x, dict) else x.get('cache', 'unknown'))

            df = df.drop(columns=['service_status'])
        except Exception as e:
            st.warning(f"Could not parse service status fields: {str(e)}")

    st.subheader("System Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if 'cpu_usage' in df.columns:
            latest_cpu = df['cpu_usage'].iloc[-1]
            avg_cpu = df['cpu_usage'].mean()
            delta = latest_cpu - avg_cpu
            st.metric("CPU Usage", f"{latest_cpu:.1f}%", f"{delta:.1f}%")

    with col2:
        if 'memory_usage' in df.columns:
            latest_mem = df['memory_usage'].iloc[-1]
            avg_mem = df['memory_usage'].mean()
            delta = latest_mem - avg_mem
            st.metric("Memory Usage", f"{latest_mem:.1f}%", f"{delta:.1f}%")

    with col3:
        if 'disk_usage' in df.columns:
            latest_disk = df['disk_usage'].iloc[-1]
            st.metric("Disk Usage", f"{latest_disk:.1f}%")

    with col4:
        if 'temperature_celsius' in df.columns:
            latest_temp = df['temperature_celsius'].iloc[-1]
            st.metric("Temperature", f"{latest_temp:.1f}°C")

    if len(df) > 0:
        st.info(f"Showing {len(df)} data points from {df['timestamp'].min().strftime('%H:%M:%S')} to {df['timestamp'].max().strftime('%H:%M:%S')}")

    st.subheader("Metrics Visualization")

    available_metrics = [col for col in df.columns if col != 'timestamp' and df[col].dtype in ['float64', 'int64']]

    col1, col2 = st.columns([1, 3])

    with col1:
        selected_metrics = st.multiselect(
            "Select metrics to display",
            available_metrics,
            default=['cpu_usage', 'memory_usage', 'disk_usage'] if all(m in available_metrics for m in ['cpu_usage', 'memory_usage', 'disk_usage']) else available_metrics[:3]
        )

    with col2:
        if selected_metrics:
            fig, ax = plt.subplots(figsize=(10, 6))

            for metric in selected_metrics:
                ax.plot(df['timestamp'], df[metric], label=metric.replace('_', ' ').title())

            ax.set_xlabel('Timestamp')
            ax.set_ylabel('Value')
            ax.set_title('System Metrics Over Time')
            ax.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()

            st.pyplot(fig)

    st.subheader("Generate AI Recommendations")
    st.write("Use our AI to analyze your data and generate recommendations for infrastructure improvements.")

    if st.button("Generate Recommendations", key=f"gen_rec_{data_source}"):
        with st.spinner("Analyzing data and generating recommendations..."):
            try:
                temp_file = f"temp_{data_source}_metrics.json"

                serializable_data = []
                for item in data:
                    serializable_item = item.copy()

                    if isinstance(serializable_item.get('timestamp'), datetime):
                        serializable_item['timestamp'] = serializable_item['timestamp'].isoformat()

                    serializable_data.append(serializable_item)

                with open(temp_file, 'w') as f:
                    json.dump(serializable_data, f, cls=DateTimeEncoder)

                result = subprocess.run(
                    ["python", "main.py", temp_file],
                    capture_output=True,
                    text=True,
                    check=True
                )

                if "Recommendations saved to" in result.stdout:
                    output_file = None
                    for line in result.stdout.split("\n"):
                        if "Recommendations saved to" in line:
                            output_file = line.split("Recommendations saved to ")[1].strip()
                            break

                    if output_file and os.path.exists(output_file):
                        with open(output_file, "r") as f:
                            recommendations = json.load(f)

                        st.success(f"Recommendations generated successfully!")

                        st.subheader("AI-Generated Recommendations")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Severity", recommendations.get('severity', 'N/A').upper())
                        with col2:
                            st.metric("Anomalies Detected", recommendations.get('anomalies_detected', 0))
                        with col3:
                            st.metric("Total Recommendations", len(recommendations.get('recommendations', [])))

                        for i, rec in enumerate(recommendations.get('recommendations', []), 1):
                            with st.expander(f"{i}. Priority {rec.get('priority', 'N/A')} - {rec.get('action', 'No action')}"):
                                st.markdown(f"**Category:** {rec.get('category', 'N/A').replace('_', ' ').title()}")
                                st.markdown(f"**Issue:** {rec.get('issue', 'N/A')}")
                                st.markdown(f"**Action:** {rec.get('action', 'N/A')}")
                                st.markdown(f"**Impact:** {rec.get('impact', 'N/A')}")
                                st.markdown(f"**Implementation:**")
                                st.code(rec.get('implementation', 'N/A'))
                                st.markdown(f"**Affected Services:** {', '.join(rec.get('affected_services', ['None']))}")
                                st.markdown(f"**Metrics to Monitor:** {', '.join(rec.get('metrics_to_monitor', ['None']))}")

                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    else:
                        st.error("Recommendations file not found. Check the console output for errors.")
                else:
                    st.error("Failed to generate recommendations. Check the console output for errors.")
                    st.code(result.stdout)
                    st.code(result.stderr)
            except Exception as e:
                st.error(f"Error generating recommendations: {str(e)}")
                if os.path.exists(temp_file):
                    os.remove(temp_file)


def show_import_data():
    st.title("Import Metrics Data")
    st.write("Upload a JSON file with infrastructure metrics data to visualize and analyze.")

    uploaded_file = st.file_uploader("Choose a JSON file", type=["json"])

    if uploaded_file is not None:
        try:
            data = json.loads(uploaded_file.getvalue().decode())

            validation_result = validate_metrics_data(data)

            if validation_result['valid']:
                st.success(f"Valid metrics data: {validation_result['valid_count']} records loaded successfully")

                st.session_state.uploaded_data = data

                if st.button("View Dashboard"):
                    st.session_state.active_tab = "imported_dashboard"
                    st.rerun()
            else:
                st.error(f"Invalid metrics data: {validation_result['invalid_count']} invalid records found")

                if 'invalid_items' in validation_result and validation_result['invalid_items']:
                    with st.expander("View validation errors"):
                        for i, (item, error) in enumerate(validation_result['invalid_items']):
                            st.write(f"Error in item {i+1}: {error}")
                            st.json(item)

                if validation_result['valid_count'] > 0:
                    if st.button(f"Use {validation_result['valid_count']} valid records only"):
                        st.session_state.uploaded_data = validation_result['valid_items']
                        st.success(f"Using {validation_result['valid_count']} valid records")

                        if st.button("View Dashboard"):
                            st.session_state.active_tab = "imported_dashboard"
                            st.rerun()
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")


def show_agent_chat():
    from agent.analyzer_agent import compiled_graph, HumanMessage

    st.title("AI Infrastructure Assistant")

    analyzer_running = is_realtime_analyzer_running()

    if analyzer_running:
        st.success("Realtime analyzer is running and collecting metrics")
    else:
        st.info("ℹRealtime analyzer is not running. Ask the agent to 'run the realtime analyzer' to start collecting metrics.")

    st.markdown("""
    This agent can help you monitor your infrastructure metrics in real-time, analyze data, and generate recommendations.

    Common commands:

    * "Run the realtime analyzer" - Start collecting real-time metrics
    * "Analyze the metrics" - Analyze collected metrics for anomalies
    * "Generate a graph of CPU usage" - Visualize specific metrics
    * "Run the full pipeline" - Generate recommendations based on analysis
    """)

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "👋 Hello! I'm your Infrastructure Monitoring Assistant.\n\nI can help you with:\n\n* Starting real-time monitoring of your system\n* Analyzing infrastructure metrics\n* Running the full analysis pipeline with recommendations\n* Generating graphs for specific metrics\n* Listing available metrics\n\nHow can I assist you today?"}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and "base64" in message["content"]:
                content = message["content"]
                parts = content.split("base64 encoded image:\n")

                if len(parts) > 1:
                    text_part = parts[0]
                    base64_part = parts[1]

                    st.write(text_part)

                    st.image(f"data:image/png;base64,{base64_part}")
                else:
                    st.write(content)
            else:
                st.write(message["content"])

    if prompt := st.chat_input("What would you like to know about your infrastructure?"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                initial_state = {"messages": [HumanMessage(content=prompt)]}
                result = compiled_graph.invoke(initial_state)

                response_content = result["messages"][-1].content

                if "base64 encoded image:" in response_content:
                    parts = response_content.split("base64 encoded image:\n")
                    text_part = parts[0]
                    base64_part = parts[1]

                    st.write(text_part)

                    st.image(f"data:image/png;base64,{base64_part}")
                else:
                    st.write(response_content)

        st.session_state.messages.append({"role": "assistant", "content": response_content})


def main():
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "agent"

    st.sidebar.title("Navigation")

    if st.sidebar.button("Agent"):
        st.session_state.active_tab = "agent"
        st.rerun()

    if st.sidebar.button("Realtime Dashboard"):
        st.session_state.active_tab = "realtime_dashboard"
        st.rerun()

    if st.sidebar.button("Import Data"):
        st.session_state.active_tab = "import_data"
        st.rerun()

    if 'uploaded_data' in st.session_state and st.session_state.uploaded_data:
        if st.sidebar.button("Imported Dashboard"):
            st.session_state.active_tab = "imported_dashboard"
            st.rerun()

    if st.session_state.active_tab == "agent":
        show_agent_chat()
    elif st.session_state.active_tab == "realtime_dashboard":
        show_metrics_dashboard(data_source="realtime")
    elif st.session_state.active_tab == "import_data":
        show_import_data()
    elif st.session_state.active_tab == "imported_dashboard":
        if 'uploaded_data' in st.session_state and st.session_state.uploaded_data:
            show_metrics_dashboard(data_source="imported")
        else:
            st.warning("No imported data available. Please go to Import Data tab first.")
            st.session_state.active_tab = "import_data"
            st.rerun()


if __name__ == "__main__":
    main()
