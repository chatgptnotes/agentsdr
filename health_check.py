"""
AgentSDR Health Check System
Comprehensive system health monitoring and diagnostics
"""

import os
import json
import requests
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    component: str
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: datetime
    details: Optional[Dict] = None

class AgentSDRHealthCheck:
    """Comprehensive health monitoring for AgentSDR system"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
    
    def check_database_connection(self) -> HealthCheckResult:
        """Check Supabase database connectivity"""
        start_time = time.time()
        
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
            
            if not supabase_url or not supabase_key:
                return HealthCheckResult(
                    component="database",
                    status=HealthStatus.CRITICAL,
                    message="Supabase credentials not configured",
                    response_time_ms=0,
                    timestamp=datetime.now(timezone.utc)
                )
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            # Test connection with organizations table
            response = requests.get(
                f"{supabase_url}/rest/v1/organizations?limit=1",
                headers=headers,
                timeout=5
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 404]:
                # Test write capability
                test_org = {
                    'name': f'health_check_test_{int(time.time())}',
                    'status': 'active',
                    'plan_type': 'trial'
                }
                
                write_response = requests.post(
                    f"{supabase_url}/rest/v1/organizations",
                    headers=headers,
                    json=test_org,
                    timeout=5
                )
                
                # Clean up test data
                if write_response.status_code == 201:
                    test_data = write_response.json()
                    if test_data:
                        test_id = test_data[0]['id']
                        requests.delete(
                            f"{supabase_url}/rest/v1/organizations?id=eq.{test_id}",
                            headers=headers
                        )
                
                return HealthCheckResult(
                    component="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection and operations successful",
                    response_time_ms=response_time,
                    timestamp=datetime.now(timezone.utc),
                    details={
                        'read_status': response.status_code,
                        'write_status': write_response.status_code,
                        'supabase_url': supabase_url.split('@')[0] + '@***'  # Mask sensitive part
                    }
                )
            else:
                return HealthCheckResult(
                    component="database",
                    status=HealthStatus.CRITICAL,
                    message=f"Database connection failed: HTTP {response.status_code}",
                    response_time_ms=response_time,
                    timestamp=datetime.now(timezone.utc)
                )
                
        except requests.exceptions.Timeout:
            return HealthCheckResult(
                component="database",
                status=HealthStatus.CRITICAL,
                message="Database connection timeout",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc)
            )
        except Exception as e:
            return HealthCheckResult(
                component="database",
                status=HealthStatus.CRITICAL,
                message=f"Database error: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc)
            )
    
    def check_ai_integration(self) -> HealthCheckResult:
        """Check OpenAI API integration"""
        start_time = time.time()
        
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                return HealthCheckResult(
                    component="ai_integration",
                    status=HealthStatus.WARNING,
                    message="OpenAI API key not configured - AI features disabled",
                    response_time_ms=0,
                    timestamp=datetime.now(timezone.utc)
                )
            
            import openai
            openai.api_key = api_key
            
            # Test with minimal request
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
                timeout=10
            )
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                component="ai_integration",
                status=HealthStatus.HEALTHY,
                message="OpenAI API connection successful",
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details={
                    'model_used': 'gpt-3.5-turbo',
                    'api_key_prefix': api_key[:7] + '...',
                    'usage': response.get('usage', {})
                }
            )
            
        except ImportError:
            return HealthCheckResult(
                component="ai_integration",
                status=HealthStatus.WARNING,
                message="OpenAI library not installed",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc)
            )
        except Exception as e:
            return HealthCheckResult(
                component="ai_integration",
                status=HealthStatus.CRITICAL,
                message=f"OpenAI API error: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc)
            )
    
    def check_core_modules(self) -> HealthCheckResult:
        """Check that all core AgentSDR modules can be imported"""
        start_time = time.time()
        
        modules_to_check = [
            'briefing_engine',
            'followup_manager',
            'crm_sync',
            'proposal_generator',
            'opportunity_intelligence',
            'meeting_prep'
        ]
        
        failed_imports = []
        successful_imports = []
        
        for module_name in modules_to_check:
            try:
                __import__(module_name)
                successful_imports.append(module_name)
            except Exception as e:
                failed_imports.append(f"{module_name}: {str(e)}")
        
        response_time = (time.time() - start_time) * 1000
        
        if not failed_imports:
            return HealthCheckResult(
                component="core_modules",
                status=HealthStatus.HEALTHY,
                message="All core modules imported successfully",
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details={
                    'successful_imports': successful_imports,
                    'total_modules': len(modules_to_check)
                }
            )
        elif len(failed_imports) < len(modules_to_check):
            return HealthCheckResult(
                component="core_modules",
                status=HealthStatus.WARNING,
                message=f"Some modules failed to import: {len(failed_imports)}/{len(modules_to_check)}",
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details={
                    'successful_imports': successful_imports,
                    'failed_imports': failed_imports
                }
            )
        else:
            return HealthCheckResult(
                component="core_modules",
                status=HealthStatus.CRITICAL,
                message="All core modules failed to import",
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details={'failed_imports': failed_imports}
            )
    
    def check_whatsapp_integration(self) -> HealthCheckResult:
        """Check WhatsApp Business API integration"""
        start_time = time.time()
        
        try:
            api_token = os.getenv('WHATSAPP_BUSINESS_API_TOKEN')
            phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
            
            if not api_token or not phone_number_id:
                return HealthCheckResult(
                    component="whatsapp_integration",
                    status=HealthStatus.WARNING,
                    message="WhatsApp Business API not configured",
                    response_time_ms=0,
                    timestamp=datetime.now(timezone.utc)
                )
            
            # Test API accessibility
            headers = {'Authorization': f'Bearer {api_token}'}
            
            response = requests.get(
                f"https://graph.facebook.com/v18.0/{phone_number_id}",
                headers=headers,
                timeout=10
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                phone_info = response.json()
                return HealthCheckResult(
                    component="whatsapp_integration",
                    status=HealthStatus.HEALTHY,
                    message="WhatsApp Business API accessible",
                    response_time_ms=response_time,
                    timestamp=datetime.now(timezone.utc),
                    details={
                        'phone_number': phone_info.get('display_phone_number', 'Unknown'),
                        'status': phone_info.get('quality_rating', 'Unknown')
                    }
                )
            else:
                return HealthCheckResult(
                    component="whatsapp_integration",
                    status=HealthStatus.CRITICAL,
                    message=f"WhatsApp API error: HTTP {response.status_code}",
                    response_time_ms=response_time,
                    timestamp=datetime.now(timezone.utc)
                )
                
        except Exception as e:
            return HealthCheckResult(
                component="whatsapp_integration",
                status=HealthStatus.CRITICAL,
                message=f"WhatsApp integration error: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc)
            )
    
    def check_system_resources(self) -> HealthCheckResult:
        """Check system resource usage"""
        start_time = time.time()
        
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on resource usage
            status = HealthStatus.HEALTHY
            warnings = []
            
            if cpu_percent > 80:
                status = HealthStatus.WARNING
                warnings.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 85:
                status = HealthStatus.WARNING
                warnings.append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > 90:
                status = HealthStatus.CRITICAL
                warnings.append(f"Critical disk usage: {disk.percent}%")
            
            message = "System resources normal"
            if warnings:
                message = "; ".join(warnings)
            
            return HealthCheckResult(
                component="system_resources",
                status=status,
                message=message,
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details={
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': round(memory.available / (1024**3), 2),
                    'disk_percent': disk.percent,
                    'disk_free_gb': round(disk.free / (1024**3), 2)
                }
            )
            
        except ImportError:
            return HealthCheckResult(
                component="system_resources",
                status=HealthStatus.WARNING,
                message="psutil not installed - cannot monitor system resources",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc)
            )
        except Exception as e:
            return HealthCheckResult(
                component="system_resources",
                status=HealthStatus.WARNING,
                message=f"System resource check error: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc)
            )
    
    def check_environment_config(self) -> HealthCheckResult:
        """Check environment configuration completeness"""
        start_time = time.time()
        
        # Required environment variables
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_SERVICE_KEY',
            'SUPABASE_ANON_KEY',
            'SECRET_KEY'
        ]
        
        # Optional but recommended variables
        optional_vars = [
            'OPENAI_API_KEY',
            'WHATSAPP_BUSINESS_API_TOKEN',
            'SENDGRID_API_KEY'
        ]
        
        missing_required = []
        missing_optional = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
        
        response_time = (time.time() - start_time) * 1000
        
        if missing_required:
            return HealthCheckResult(
                component="environment_config",
                status=HealthStatus.CRITICAL,
                message=f"Missing required environment variables: {', '.join(missing_required)}",
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details={
                    'missing_required': missing_required,
                    'missing_optional': missing_optional
                }
            )
        elif missing_optional:
            return HealthCheckResult(
                component="environment_config",
                status=HealthStatus.WARNING,
                message=f"Missing optional environment variables: {', '.join(missing_optional)}",
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details={
                    'missing_optional': missing_optional,
                    'configured_required': len(required_vars),
                    'configured_optional': len(optional_vars) - len(missing_optional)
                }
            )
        else:
            return HealthCheckResult(
                component="environment_config",
                status=HealthStatus.HEALTHY,
                message="All environment variables configured",
                response_time_ms=response_time,
                timestamp=datetime.now(timezone.utc),
                details={
                    'configured_required': len(required_vars),
                    'configured_optional': len(optional_vars)
                }
            )
    
    def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive report"""
        self.start_time = time.time()
        self.results = []
        
        # Run all health checks
        health_checks = [
            self.check_environment_config,
            self.check_database_connection,
            self.check_core_modules,
            self.check_ai_integration,
            self.check_whatsapp_integration,
            self.check_system_resources
        ]
        
        for check_function in health_checks:
            try:
                result = check_function()
                self.results.append(result)
            except Exception as e:
                # Create error result for failed health check
                error_result = HealthCheckResult(
                    component=check_function.__name__.replace('check_', ''),
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {str(e)}",
                    response_time_ms=0,
                    timestamp=datetime.now(timezone.utc)
                )
                self.results.append(error_result)
        
        # Calculate overall health status
        status_counts = {status: 0 for status in HealthStatus}
        for result in self.results:
            status_counts[result.status] += 1
        
        # Determine overall status
        if status_counts[HealthStatus.CRITICAL] > 0:
            overall_status = HealthStatus.CRITICAL
        elif status_counts[HealthStatus.WARNING] > 0:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY
        
        total_time = (time.time() - self.start_time) * 1000
        
        # Create comprehensive report
        report = {
            'overall_status': overall_status.value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_check_time_ms': round(total_time, 2),
            'summary': {
                'total_checks': len(self.results),
                'healthy': status_counts[HealthStatus.HEALTHY],
                'warnings': status_counts[HealthStatus.WARNING],
                'critical': status_counts[HealthStatus.CRITICAL],
                'unknown': status_counts[HealthStatus.UNKNOWN]
            },
            'checks': [asdict(result) for result in self.results],
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []
        
        for result in self.results:
            if result.status == HealthStatus.CRITICAL:
                if result.component == 'database':
                    recommendations.append("Fix database connection issues immediately - core functionality is affected")
                elif result.component == 'core_modules':
                    recommendations.append("Resolve module import errors - check dependencies and Python path")
                elif result.component == 'environment_config':
                    recommendations.append("Configure missing required environment variables")
            
            elif result.status == HealthStatus.WARNING:
                if result.component == 'ai_integration':
                    recommendations.append("Configure OpenAI API for enhanced AI features")
                elif result.component == 'whatsapp_integration':
                    recommendations.append("Set up WhatsApp Business API for mobile notifications")
                elif result.component == 'system_resources':
                    recommendations.append("Monitor system resource usage - consider scaling if needed")
        
        # Add general recommendations
        if not recommendations:
            recommendations.append("System is healthy - consider monitoring setup for production")
        
        return recommendations

def create_health_endpoint():
    """Create Flask health check endpoint"""
    from flask import jsonify
    
    def health_check():
        health_checker = AgentSDRHealthCheck()
        report = health_checker.run_comprehensive_health_check()
        
        # Return appropriate HTTP status code
        if report['overall_status'] == 'critical':
            status_code = 503  # Service Unavailable
        elif report['overall_status'] == 'warning':
            status_code = 200  # OK but with warnings
        else:
            status_code = 200  # OK
        
        return jsonify(report), status_code
    
    return health_check

# CLI interface for health checks
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='AgentSDR Health Check')
    parser.add_argument('--component', help='Check specific component only')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--summary', action='store_true', help='Show summary only')
    
    args = parser.parse_args()
    
    health_checker = AgentSDRHealthCheck()
    
    if args.component:
        # Check specific component
        component_methods = {
            'database': health_checker.check_database_connection,
            'ai': health_checker.check_ai_integration,
            'modules': health_checker.check_core_modules,
            'whatsapp': health_checker.check_whatsapp_integration,
            'resources': health_checker.check_system_resources,
            'config': health_checker.check_environment_config
        }
        
        if args.component in component_methods:
            result = component_methods[args.component]()
            if args.json:
                print(json.dumps(asdict(result), indent=2, default=str))
            else:
                print(f"Component: {result.component}")
                print(f"Status: {result.status.value}")
                print(f"Message: {result.message}")
                print(f"Response Time: {result.response_time_ms:.2f}ms")
        else:
            print(f"Unknown component: {args.component}")
            print(f"Available components: {', '.join(component_methods.keys())}")
    else:
        # Run comprehensive health check
        report = health_checker.run_comprehensive_health_check()
        
        if args.json:
            print(json.dumps(report, indent=2, default=str))
        elif args.summary:
            print(f"Overall Status: {report['overall_status'].upper()}")
            print(f"Total Checks: {report['summary']['total_checks']}")
            print(f"Healthy: {report['summary']['healthy']}")
            print(f"Warnings: {report['summary']['warnings']}")
            print(f"Critical: {report['summary']['critical']}")
        else:
            print("AgentSDR Health Check Report")
            print("=" * 40)
            print(f"Overall Status: {report['overall_status'].upper()}")
            print(f"Check Time: {report['total_check_time_ms']:.2f}ms")
            print()
            
            for check in report['checks']:
                status_emoji = {
                    'healthy': '✅',
                    'warning': '⚠️',
                    'critical': '❌',
                    'unknown': '❓'
                }.get(check['status'], '❓')
                
                print(f"{status_emoji} {check['component']}: {check['message']}")
            
            if report['recommendations']:
                print("\nRecommendations:")
                for i, rec in enumerate(report['recommendations'], 1):
                    print(f"{i}. {rec}")