import boto3
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re

class AIAnalysisService:
    def __init__(self, region: str = 'us-east-2'):
        self.region = region
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=region)
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    
    def analyze_resource_health(self, resource: Dict, logs: List[Dict] = None) -> Dict:
        """Analyze resource health and provide recommendations"""
        try:
            # Prepare context for AI analysis
            context = self._prepare_resource_context(resource, logs)
            
            # Create analysis prompt
            prompt = self._create_health_analysis_prompt(context)
            
            # Get AI analysis
            ai_response = self._call_bedrock(prompt)
            
            # Parse and structure the response
            analysis = self._parse_ai_response(ai_response, resource)
            
            return analysis
            
        except Exception as e:
            print(f"Error in AI analysis: {e}")
            return self._fallback_analysis(resource)
    
    def analyze_logs(self, logs: List[Dict], service_type: str = "general") -> Dict:
        """Analyze logs for patterns and anomalies"""
        try:
            if not logs:
                return {"status": "no_logs", "message": "No logs available for analysis"}
            
            # Prepare log context
            log_context = self._prepare_log_context(logs, service_type)
            
            # Create log analysis prompt
            prompt = self._create_log_analysis_prompt(log_context, service_type)
            
            # Get AI analysis
            ai_response = self._call_bedrock(prompt)
            
            # Parse log analysis response
            analysis = self._parse_log_analysis_response(ai_response, logs)
            
            return analysis
            
        except Exception as e:
            print(f"Error in log analysis: {e}")
            return self._fallback_log_analysis(logs)
    
    def generate_alert_recommendations(self, resource: Dict, issue_type: str, metadata: Dict = None) -> Dict:
        """Generate recommendations for resolving specific issues"""
        try:
            # Create recommendation prompt
            prompt = self._create_recommendation_prompt(resource, issue_type, metadata)
            
            # Get AI recommendations
            ai_response = self._call_bedrock(prompt)
            
            # Parse recommendations
            recommendations = self._parse_recommendations_response(ai_response, resource, issue_type)
            
            return recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return self._fallback_recommendations(resource, issue_type)
    
    def _prepare_resource_context(self, resource: Dict, logs: List[Dict] = None) -> str:
        """Prepare resource context for AI analysis"""
        context_parts = []
        
        # Basic resource info
        context_parts.append(f"Resource Type: {resource.get('resource_type', 'Unknown')}")
        context_parts.append(f"Resource ID: {resource.get('resource_id', 'Unknown')}")
        context_parts.append(f"Name: {resource.get('name', 'Unknown')}")
        context_parts.append(f"Status: {resource.get('status', 'Unknown')}")
        context_parts.append(f"Region: {resource.get('region', 'Unknown')}")
        
        # Metadata
        metadata = resource.get('metadata', {})
        if metadata:
            context_parts.append("\\nMetadata:")
            for key, value in metadata.items():
                if key != 'tags':  # Skip tags for brevity
                    context_parts.append(f"  {key}: {value}")
        
        # Recent logs if available
        if logs:
            context_parts.append(f"\\nRecent Logs ({len(logs)} entries):")
            for log in logs[-5:]:  # Last 5 logs
                timestamp = log.get('timestamp', 'Unknown')
                level = log.get('level', 'INFO')
                message = log.get('message', '')[:200]  # Truncate long messages
                context_parts.append(f"  [{timestamp}] {level}: {message}")
        
        return "\\n".join(context_parts)
    
    def _prepare_log_context(self, logs: List[Dict], service_type: str) -> str:
        """Prepare log context for analysis"""
        context_parts = []
        
        context_parts.append(f"Service Type: {service_type}")
        context_parts.append(f"Total Log Entries: {len(logs)}")
        
        # Categorize logs by level
        levels = {}
        for log in logs:
            level = log.get('level', 'INFO')
            levels[level] = levels.get(level, 0) + 1
        
        context_parts.append("Log Level Distribution:")
        for level, count in levels.items():
            context_parts.append(f"  {level}: {count}")
        
        # Recent error/warning logs
        error_logs = [log for log in logs if log.get('level', '').upper() in ['ERROR', 'CRITICAL', 'FATAL']]
        warning_logs = [log for log in logs if log.get('level', '').upper() in ['WARNING', 'WARN']]
        
        if error_logs:
            context_parts.append(f"\\nRecent Error Logs ({len(error_logs)}):")
            for log in error_logs[-3:]:
                timestamp = log.get('timestamp', 'Unknown')
                message = log.get('message', '')[:300]
                context_parts.append(f"  [{timestamp}] ERROR: {message}")
        
        if warning_logs:
            context_parts.append(f"\\nRecent Warning Logs ({len(warning_logs)}):")
            for log in warning_logs[-3:]:
                timestamp = log.get('timestamp', 'Unknown')
                message = log.get('message', '')[:300]
                context_parts.append(f"  [{timestamp}] WARNING: {message}")
        
        return "\\n".join(context_parts)
    
    def _create_health_analysis_prompt(self, context: str) -> str:
        """Create prompt for resource health analysis"""
        return f"""You are an expert AWS infrastructure analyst. Analyze the following AWS resource and provide a comprehensive health assessment.

Resource Information:
{context}

Please provide your analysis in the following JSON format:
{{
    "health_status": "healthy|warning|critical",
    "confidence": 0.0-1.0,
    "issues": [
        {{
            "type": "performance|availability|security|cost|configuration",
            "severity": "low|medium|high|critical",
            "description": "Clear description of the issue",
            "impact": "Potential impact on the system"
        }}
    ],
    "recommendations": [
        {{
            "priority": "low|medium|high|critical",
            "action": "Specific action to take",
            "rationale": "Why this action is recommended",
            "urgency": "immediate|short_term|long_term"
        }}
    ],
    "metrics_to_monitor": [
        "List of specific metrics to monitor for this resource"
    ],
    "summary": "Brief overall assessment"
}}

Focus on:
1. Current health status based on the provided information
2. Potential issues or risks
3. Actionable recommendations
4. Key metrics to monitor
5. Security considerations if applicable

Provide practical, specific recommendations rather than generic advice."""
    
    def _create_log_analysis_prompt(self, log_context: str, service_type: str) -> str:
        """Create prompt for log analysis"""
        return f"""You are an expert system administrator and log analyst. Analyze the following logs from a {service_type} service to identify patterns, anomalies, and potential issues.

Log Analysis Context:
{log_context}

Please provide your analysis in the following JSON format:
{{
    "overall_health": "healthy|degraded|critical",
    "anomalies": [
        {{
            "type": "error_spike|performance_degradation|security_incident|unusual_pattern",
            "severity": "low|medium|high|critical",
            "description": "What was detected",
            "frequency": "How often this occurs",
            "first_seen": "When this pattern started",
            "potential_causes": ["List of possible causes"]
        }}
    ],
    "patterns": [
        {{
            "pattern": "Description of the pattern",
            "significance": "Why this pattern is important",
            "recommendation": "What to do about it"
        }}
    ],
    "alerts": [
        {{
            "type": "immediate|scheduled|informational",
            "message": "Alert message",
            "action_required": "What action is needed"
        }}
    ],
    "summary": "Overall log analysis summary",
    "next_steps": ["Immediate actions to take"]
}}

Focus on:
1. Error patterns and their frequency
2. Performance indicators
3. Security-related events
4. Unusual or anomalous behavior
5. Trends that might indicate future problems"""
    
    def _create_recommendation_prompt(self, resource: Dict, issue_type: str, metadata: Dict = None) -> str:
        """Create prompt for generating specific recommendations"""
        resource_info = f"""
Resource Type: {resource.get('resource_type', 'Unknown')}
Resource ID: {resource.get('resource_id', 'Unknown')}
Current Status: {resource.get('status', 'Unknown')}
Issue Type: {issue_type}
"""
        
        if metadata:
            resource_info += f"\\nAdditional Context: {json.dumps(metadata, indent=2)}"
        
        return f"""You are an expert AWS solutions architect. Provide specific, actionable recommendations to resolve the following issue.

{resource_info}

Please provide detailed recommendations in the following JSON format:
{{
    "immediate_actions": [
        {{
            "step": "Specific step to take immediately",
            "command": "AWS CLI command or console action (if applicable)",
            "expected_result": "What should happen",
            "risk_level": "low|medium|high"
        }}
    ],
    "root_cause_analysis": {{
        "likely_causes": ["List of most probable causes"],
        "investigation_steps": ["Steps to confirm the root cause"],
        "tools_to_use": ["AWS services or tools to help diagnose"]
    }},
    "prevention_measures": [
        {{
            "measure": "Preventive action",
            "implementation": "How to implement",
            "monitoring": "How to monitor effectiveness"
        }}
    ],
    "estimated_resolution_time": "time estimate",
    "escalation_criteria": "When to escalate this issue",
    "documentation_links": ["Relevant AWS documentation URLs"]
}}

Provide AWS-specific, practical guidance that considers:
1. AWS best practices
2. Cost implications
3. Security considerations
4. Minimal service disruption
5. Long-term reliability"""
    
    def _call_bedrock(self, prompt: str) -> str:
        """Call Amazon Bedrock for AI analysis"""
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 4000,
                    "temperature": 0.1
                })
            )
            
            result = json.loads(response['body'].read())
            return result['content'][0]['text']
            
        except Exception as e:
            print(f"Error calling Bedrock: {e}")
            raise
    
    def _parse_ai_response(self, ai_response: str, resource: Dict) -> Dict:
        """Parse AI response for resource health analysis"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\\{.*\\}', ai_response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Fallback parsing
                analysis = self._fallback_parse_response(ai_response, resource)
            
            # Add metadata
            analysis['analysis_timestamp'] = datetime.now().isoformat()
            analysis['resource_id'] = resource.get('resource_id')
            analysis['resource_type'] = resource.get('resource_type')
            
            return analysis
            
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return self._fallback_analysis(resource)
    
    def _parse_log_analysis_response(self, ai_response: str, logs: List[Dict]) -> Dict:
        """Parse AI response for log analysis"""
        try:
            # Try to extract JSON
            json_match = re.search(r'\\{.*\\}', ai_response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = self._fallback_log_analysis(logs)
            
            analysis['analysis_timestamp'] = datetime.now().isoformat()
            analysis['logs_analyzed'] = len(logs)
            
            return analysis
            
        except Exception as e:
            print(f"Error parsing log analysis response: {e}")
            return self._fallback_log_analysis(logs)
    
    def _parse_recommendations_response(self, ai_response: str, resource: Dict, issue_type: str) -> Dict:
        """Parse AI response for recommendations"""
        try:
            # Try to extract JSON
            json_match = re.search(r'\\{.*\\}', ai_response, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
            else:
                recommendations = self._fallback_recommendations(resource, issue_type)
            
            recommendations['generated_timestamp'] = datetime.now().isoformat()
            recommendations['resource_id'] = resource.get('resource_id')
            recommendations['issue_type'] = issue_type
            
            return recommendations
            
        except Exception as e:
            print(f"Error parsing recommendations response: {e}")
            return self._fallback_recommendations(resource, issue_type)
    
    def _fallback_analysis(self, resource: Dict) -> Dict:
        """Fallback analysis when AI fails"""
        health_status = "unknown"
        issues = []
        
        # Basic heuristics
        if resource.get('status') in ['stopped', 'terminated', 'failed']:
            health_status = "critical"
            issues.append({
                "type": "availability",
                "severity": "critical",
                "description": f"Resource is in {resource.get('status')} state",
                "impact": "Service unavailable"
            })
        elif resource.get('metadata', {}).get('health_status') == 'unhealthy':
            health_status = "warning"
            issues.append({
                "type": "availability",
                "severity": "medium",
                "description": "Resource health check indicates issues",
                "impact": "Potential service degradation"
            })
        else:
            health_status = "healthy"
        
        return {
            "health_status": health_status,
            "confidence": 0.6,
            "issues": issues,
            "recommendations": [],
            "metrics_to_monitor": ["Basic health metrics"],
            "summary": "Fallback analysis - AI analysis unavailable",
            "analysis_timestamp": datetime.now().isoformat(),
            "resource_id": resource.get('resource_id'),
            "resource_type": resource.get('resource_type')
        }
    
    def _fallback_log_analysis(self, logs: List[Dict]) -> Dict:
        """Fallback log analysis when AI fails"""
        error_count = sum(1 for log in logs if log.get('level', '').upper() in ['ERROR', 'CRITICAL', 'FATAL'])
        warning_count = sum(1 for log in logs if log.get('level', '').upper() in ['WARNING', 'WARN'])
        
        if error_count > 0:
            overall_health = "critical" if error_count > 5 else "degraded"
        elif warning_count > 10:
            overall_health = "degraded"
        else:
            overall_health = "healthy"
        
        return {
            "overall_health": overall_health,
            "anomalies": [],
            "patterns": [],
            "alerts": [],
            "summary": f"Fallback analysis: {error_count} errors, {warning_count} warnings",
            "next_steps": ["Review error logs manually"],
            "analysis_timestamp": datetime.now().isoformat(),
            "logs_analyzed": len(logs)
        }
    
    def _fallback_recommendations(self, resource: Dict, issue_type: str) -> Dict:
        """Fallback recommendations when AI fails"""
        return {
            "immediate_actions": [{
                "step": "Check AWS console for detailed status",
                "command": "aws {} describe-* --region {}".format(
                    resource.get('resource_type', '').lower().replace('_', '-'),
                    resource.get('region', 'us-east-1')
                ),
                "expected_result": "Detailed resource status",
                "risk_level": "low"
            }],
            "root_cause_analysis": {
                "likely_causes": ["Resource configuration issue", "Service limit exceeded", "Network connectivity"],
                "investigation_steps": ["Check resource configuration", "Review CloudTrail logs", "Verify service limits"],
                "tools_to_use": ["AWS Console", "CloudWatch", "CloudTrail"]
            },
            "prevention_measures": [],
            "estimated_resolution_time": "Unknown",
            "escalation_criteria": "If issue persists for more than 1 hour",
            "documentation_links": [],
            "generated_timestamp": datetime.now().isoformat(),
            "resource_id": resource.get('resource_id'),
            "issue_type": issue_type
        }
    
    def _fallback_parse_response(self, response: str, resource: Dict) -> Dict:
        """Parse non-JSON AI responses"""
        # Simple keyword-based parsing
        health_status = "unknown"
        if "critical" in response.lower():
            health_status = "critical"
        elif "warning" in response.lower() or "issue" in response.lower():
            health_status = "warning"
        elif "healthy" in response.lower() or "good" in response.lower():
            health_status = "healthy"
        
        return {
            "health_status": health_status,
            "confidence": 0.5,
            "issues": [],
            "recommendations": [],
            "metrics_to_monitor": [],
            "summary": response[:500],  # First 500 chars
            "analysis_timestamp": datetime.now().isoformat(),
            "resource_id": resource.get('resource_id'),
            "resource_type": resource.get('resource_type')
        }

