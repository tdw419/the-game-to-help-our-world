"""
Security Vulnerability Scanner for Requirements Manager
"""
import requests
import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SecurityScanner:
    """Scan packages for known security vulnerabilities"""
    
    def __init__(self):
        self.vulnerability_databases = {
            'safety': 'https://pyup.io/api/v1/vulnerabilities/',
            'osv': 'https://api.osv.dev/v1/query',
            'snyk': 'https://snyk.io/api/v1/'
        }
        self.cache = {}
        self.cache_duration = timedelta(hours=24)
    
    def scan_installed_packages(self) -> Dict[str, List[Dict]]:
        """Scan all installed packages for vulnerabilities"""
        try:
            # Get installed packages
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'list', '--format=json'
            ], capture_output=True, text=True, check=True)
            
            packages = json.loads(result.stdout)
            vulnerabilities = {}
            
            for package in packages:
                name = package['name']
                version = package['version']
                
                vulns = self.check_package_vulnerabilities(name, version)
                if vulns:
                    vulnerabilities[f"{name}=={version}"] = vulns
            
            return vulnerabilities
            
        except Exception as e:
            logger.error(f"Failed to scan packages: {e}")
            return {}
    
    def check_package_vulnerabilities(self, package: str, version: str) -> List[Dict]:
        """Check specific package version for vulnerabilities"""
        cache_key = f"{package}::{version}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_data
        
        vulnerabilities = []
        
        # Check multiple databases
        vulnerabilities.extend(self._check_safety_db(package, version))
        vulnerabilities.extend(self._check_osv_db(package, version))
        
        # Cache results
        self.cache[cache_key] = (datetime.now(), vulnerabilities)
        
        return vulnerabilities
    
    def _check_safety_db(self, package: str, version: str) -> List[Dict]:
        """Check PyUp.io Safety database"""
        try:
            url = f"https://pyup.io/api/v1/vulnerabilities/{package}/"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                vulnerabilities = []
                
                for vuln in data.get('vulnerabilities', []):
                    # Check if current version is affected
                    affected_versions = vuln.get('specs', [])
                    if self._is_version_affected(version, affected_versions):
                        vulnerabilities.append({
                            'id': vuln.get('id'),
                            'summary': vuln.get('advisory'),
                            'severity': self._parse_severity(vuln.get('cve')),
                            'affected_versions': affected_versions,
                            'source': 'safety',
                            'cve': vuln.get('cve'),
                            'more_info': vuln.get('more_info_url')
                        })
                
                return vulnerabilities
                
        except Exception as e:
            logger.warning(f"Safety DB check failed for {package}: {e}")
        
        return []
    
    def _check_osv_db(self, package: str, version: str) -> List[Dict]:
        """Check OSV (Open Source Vulnerabilities) database"""
        try:
            url = "https://api.osv.dev/v1/query"
            payload = {
                "package": {
                    "name": package,
                    "ecosystem": "PyPI"
                },
                "version": version
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                vulnerabilities = []
                
                for vuln in data.get('vulns', []):
                    vulnerabilities.append({
                        'id': vuln.get('id'),
                        'summary': vuln.get('summary', 'No summary available'),
                        'severity': self._parse_osv_severity(vuln),
                        'affected_versions': self._extract_affected_versions(vuln),
                        'source': 'osv',
                        'published': vuln.get('published'),
                        'more_info': f"https://osv.dev/vulnerability/{vuln.get('id')}"
                    })
                
                return vulnerabilities
                
        except Exception as e:
            logger.warning(f"OSV DB check failed for {package}: {e}")
        
        return []
    
    def _is_version_affected(self, version: str, affected_specs: List[str]) -> bool:
        """Check if version matches affected version specifications"""
        try:
            from packaging import version as pkg_version
            from packaging.specifiers import SpecifierSet
            
            current_version = pkg_version.parse(version)
            
            for spec in affected_specs:
                specifier_set = SpecifierSet(spec)
                if current_version in specifier_set:
                    return True
            
            return False
            
        except Exception:
            # Fallback to simple string matching
            return version in affected_specs
    
    def _parse_severity(self,