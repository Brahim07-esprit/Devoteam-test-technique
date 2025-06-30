import os
import sys
from datetime import datetime
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer import InfrastructureAnalyzer
from main import generate_recommendations


def analyze_realtime_data():
    metrics_file = "realtime_metrics.json"
    
    if not os.path.exists(metrics_file):
        print(f"Error: {metrics_file} not found!")
        print("Make sure realtime_simple.py is running and has collected some data.")
        return
    
    print(f"Analyzing real-time infrastructure metrics from {metrics_file}...")
    
    analyzer = InfrastructureAnalyzer()
    metrics = analyzer.load_data(metrics_file)
    
    if len(metrics) < 5:
        print(f"\nWarning: Only {len(metrics)} metrics found. Run the monitor longer for better analysis.")
    
    analysis = analyzer.detect_anomalies(metrics)
    
    if analysis['total_anomalies'] > 0:
        print("\n=== Recommendation Generation Node ===")
        print("Generating recommendations with GPT-4o-mini...")
        print(f"Anomaly Analysis:")
        print(f"  - Total anomalies: {analysis['total_anomalies']}")
        print(f"  - Critical severity: {analysis['critical_count']}")
        
        try:
            recommendations = generate_recommendations(analysis)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"realtime_report_{timestamp}.json"
            with open(report_file, 'w') as f:
                json.dump(recommendations, f, indent=2)
            
            print(f"\nReport saved to {report_file}")
            print(f"\nSummary:")
            print(f"- Severity: {recommendations['severity']}")
            print(f"- Total recommendations: {len(recommendations['recommendations'])}")
            print(f"\nTop 3 actions:")
            for i, rec in enumerate(recommendations['recommendations'][:3], 1):
                print(f"{i}. {rec['action']}")
                
        except Exception as e:
            print(f"\nError generating recommendations: {e}")
    else:
        print("\nNo anomalies detected! Your system is running smoothly.")


if __name__ == "__main__":
    analyze_realtime_data()