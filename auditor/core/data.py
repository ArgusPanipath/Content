"""
Data Layer - Mock implementations for Graph DB and Vulnerability Indexer
These are stubs that simulate real database interactions.
"""
import logging
import random
from typing import List, Dict, Optional
from auditor.config import MOCK_PACKAGE_CLUSTERS, MOCK_CVE_DATABASE

logger = logging.getLogger(__name__)


class GraphDB:
    """
    Mock Graph Database (Neo4j stub).
    Simulates querying the dependency graph for package clusters.
    """
    
    def __init__(self):
        """Initialize the mock graph database."""
        self.clusters = MOCK_PACKAGE_CLUSTERS
        logger.info("📊 GraphDB initialized (Mock)")
    
    def get_clusters(self, limit: Optional[int] = None) -> List[str]:
        """
        Get package clusters from the graph database.
        
        In production, this would execute a Cypher query like:
        MATCH (p:Package)-[:DEPENDS_ON*]->(d:Package)
        WHERE p.vulnerability_score > 7
        RETURN COLLECT(DISTINCT p.name + '@' + p.version) as clusters
        
        Args:
            limit: Optional limit on number of clusters to return
            
        Returns:
            List[str]: List of package identifiers (e.g., "react@16.0.0")
        """
        logger.debug(f"🔍 Querying graph database for clusters (limit={limit})")
        
        # Simulate some variability - return random subset each time
        available_clusters = self.clusters.copy()
        random.shuffle(available_clusters)
        
        if limit:
            result = available_clusters[:limit]
        else:
            result = available_clusters
        
        logger.info(f"📊 Graph query returned {len(result)} clusters")
        return result
    
    def get_package_dependencies(self, package_id: str) -> List[str]:
        """
        Get dependencies for a specific package.
        
        Args:
            package_id: Package identifier (e.g., "react@16.0.0")
            
        Returns:
            List[str]: List of dependency package identifiers
        """
        # Mock implementation - return random dependencies
        logger.debug(f"🔍 Querying dependencies for {package_id}")
        
        # Extract package name without version
        package_name = package_id.split('@')[0]
        
        # Return some random packages as dependencies
        deps = random.sample(self.clusters, min(5, len(self.clusters)))
        logger.debug(f"📊 Found {len(deps)} dependencies for {package_id}")
        
        return deps


class VulnerabilityIndexer:
    """
    Mock RAG-based Vulnerability Indexer.
    Simulates querying a vector database for known CVEs.
    """
    
    def __init__(self):
        """Initialize the mock vulnerability indexer."""
        self.cve_database = MOCK_CVE_DATABASE
        logger.info("🔐 VulnerabilityIndexer initialized (Mock)")
    
    def get_known_cves(self, package_name: str) -> List[str]:
        """
        Get known CVEs for a package.
        
        In production, this would:
        1. Generate embeddings for the package name
        2. Query vector database for similar vulnerability reports
        3. Return ranked list of relevant CVEs
        
        Args:
            package_name: Package name (without version, e.g., "react")
            
        Returns:
            List[str]: List of CVE identifiers
        """
        logger.debug(f"🔍 Querying vulnerability index for {package_name}")
        
        # Extract base package name (handle scoped packages like @babel/core)
        base_name = package_name.split('@')[-1].split('/')[0]
        
        # Look up in mock database
        cves = self.cve_database.get(base_name, [])
        
        if cves:
            logger.info(f"🔐 Found {len(cves)} known CVEs for {package_name}")
        else:
            logger.debug(f"✅ No known CVEs for {package_name}")
        
        return cves
    
    def get_vulnerability_details(self, cve_id: str) -> Dict[str, str]:
        """
        Get detailed information about a specific CVE.
        
        Args:
            cve_id: CVE identifier (e.g., "CVE-2021-23840")
            
        Returns:
            Dict[str, str]: Mock vulnerability details
        """
        logger.debug(f"🔍 Fetching details for {cve_id}")
        
        # Mock vulnerability details
        return {
            "cve_id": cve_id,
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "description": f"Mock vulnerability description for {cve_id}",
            "cvss_score": round(random.uniform(4.0, 9.5), 1),
            "published_date": "2021-01-01",
            "references": [f"https://nvd.nist.gov/vuln/detail/{cve_id}"]
        }
