import os
import sys
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from src.core.analyzer import InfrastructureAnalyzer

load_dotenv()


def generate_recommendations(analysis_data):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    anomaly_summary = {
        "total_anomalies": analysis_data['total_anomalies'],
        "critical_severity": analysis_data['critical_count'],
        "type_distribution": analysis_data['anomaly_breakdown'],
        "total_metrics_analyzed": analysis_data['total_metrics']
    }

    critical_metrics = []
    for anomaly in analysis_data['sample_anomalies'][:5]:
        critical_metrics.append({
            "type": anomaly['type'],
            "value": anomaly['value'],
            "description": anomaly['description']
        })

    service_impact = analysis_data['service_issues']

    template = """You are an expert infrastructure engineer analyzing system anomalies and providing actionable recommendations.

Analyze the following infrastructure issues and provide specific, prioritized recommendations.

ANOMALY SUMMARY:
{anomaly_summary}

CRITICAL METRICS:
{critical_metrics}

SERVICE IMPACT:
{service_impact}

Based on this analysis, provide recommendations following these guidelines:

1. IMMEDIATE ACTIONS (Priority 1-2): Address critical issues that need attention within hours
2. HIGH PRIORITY (Priority 3-5): Important optimizations to prevent escalation
3. MEDIUM PRIORITY (Priority 6+): Preventive measures and long-term improvements

For each recommendation, provide:
- Clear description of the issue
- Specific action to take
- Expected impact (quantified when possible)
- Implementation steps (commands/configuration when applicable)
- Affected services
- Metrics to monitor after implementation

Focus on:
- Thermal management (high temperatures detected)
- Service reliability (API Gateway issues)
- Error rate reduction
- Resource optimization
- Scalability improvements

Format your response as a structured list of recommendations, prioritized by urgency and impact.
Be specific with technical details, commands, and configuration changes.

IMPORTANT: Return your response as a valid JSON object with this exact structure:
{{
    "timestamp": "{timestamp}",
    "severity": "high",
    "anomalies_detected": {total_anomalies},
    "recommendations": [
        {{
            "priority": 1,
            "category": "immediate_action|optimization|scaling|monitoring|maintenance|configuration|infrastructure",
            "issue": "description of the issue",
            "action": "specific action to take",
            "impact": "expected impact",
            "implementation": "implementation steps",
            "affected_services": ["service1", "service2"],
            "metrics_to_monitor": ["metric1", "metric2"]
        }}
    ],
    "metrics_summary": {{
        "critical_metrics": ["list of critical metric types"],
        "trending_concerns": ["list of trending issues"]
    }}
}}"""

    prompt = template.format(
        anomaly_summary=json.dumps(anomaly_summary, indent=2),
        critical_metrics=json.dumps(critical_metrics, indent=2),
        service_impact=json.dumps(service_impact, indent=2),
        timestamp=datetime.now().isoformat(),
        total_anomalies=analysis_data['total_anomalies']
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <input_file.json>")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found")
        sys.exit(1)

    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    print(f"\nAnalyzing infrastructure metrics from {input_file}...")

    analyzer = InfrastructureAnalyzer()
    metrics = analyzer.load_data(input_file)
    analysis = analyzer.detect_anomalies(metrics)

    print("\n=== Recommendation Generation Node ===")
    print("Generating recommendations...")
    print(f"Anomaly Analysis:")
    print(f"  - Total anomalies: {analysis['total_anomalies']}")
    print(f"  - Critical severity: {analysis['critical_count']}")
    try:
        recommendations = generate_recommendations(analysis)

        output_file = f"recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(recommendations, f, indent=2)

        print(f"\nRecommendations saved to {output_file}")
        print(f"\nSummary:")
        print(f"- Severity: {recommendations['severity']}")
        print(f"- Total recommendations: {len(recommendations['recommendations'])}")
        print(f"\nTop 3 actions:")
        for i, rec in enumerate(recommendations['recommendations'][:3], 1):
            print(f"{i}. {rec['action']}")

    except Exception as e:
        print(f"Error generating recommendations: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
