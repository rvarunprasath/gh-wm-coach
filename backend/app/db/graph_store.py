"""
Embedded Knowledge Graph Engine.
Uses NetworkX with persistent JSON serialization to model personal entities,
family relations, life events, dependencies, financial assets, and goals.
"""

import os
import json
import networkx as nx
from typing import Dict, List, Any, Optional

GRAPH_FILE = os.path.join(os.path.dirname(__file__), "knowledge_graph.json")


class KnowledgeGraphStore:
    def __init__(self, file_path: str = GRAPH_FILE):
        self.file_path = file_path
        self.graph = nx.MultiDiGraph()
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data, multigraph=True, directed=True, edges="links")
                    return
            except Exception as e:
                print(f"[GraphStore] Error loading graph file: {e}. Starting fresh.")
        self.graph = nx.MultiDiGraph()

    def save(self):
        try:
            data = nx.node_link_data(self.graph, edges="links")
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[GraphStore] Error saving graph: {e}")

    def add_node(self, node_id: str, label: str, properties: Optional[Dict[str, Any]] = None):
        """Adds or updates a node with a primary label and arbitrary attributes."""
        self.load()
        props = properties or {}
        props["label"] = label
        if not self.graph.has_node(node_id):
            self.graph.add_node(node_id, **props)
        else:
            self.graph.nodes[node_id].update(props)
        self.save()

    def add_edge(self, source_id: str, target_id: str, relation: str, properties: Optional[Dict[str, Any]] = None):
        """Adds a directed relationship between two nodes."""
        self.load()
        props = properties or {}
        props["relation"] = relation
        self.graph.add_edge(source_id, target_id, **props)
        self.save()

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        if self.graph.has_node(node_id):
            data = dict(self.graph.nodes[node_id])
            data["id"] = node_id
            return data
        return None

    def get_user_subgraph(self, user_id: str = "user_self") -> Dict[str, Any]:
        """
        Returns nodes and links formatted for frontend visualization (e.g. D3 / Cytoscape / SVG graph).
        """
        self.load()
        if not self.graph.has_node(user_id):
            return {"nodes": [], "edges": []}

        # Collect 2-hop neighborhood of user
        nodes_to_include = set([user_id])
        # 1-hop
        for neighbor in self.graph.successors(user_id):
            nodes_to_include.add(neighbor)
            # 2-hop
            for n2 in self.graph.successors(neighbor):
                nodes_to_include.add(n2)
        for predecessor in self.graph.predecessors(user_id):
            nodes_to_include.add(predecessor)

        subgraph_nodes = []
        for nid in nodes_to_include:
            attrs = dict(self.graph.nodes[nid])
            subgraph_nodes.append({
                "id": nid,
                "label": attrs.get("label", "Entity"),
                "name": attrs.get("name", nid),
                "properties": attrs
            })

        subgraph_edges = []
        for u, v, k, attrs in self.graph.edges(keys=True, data=True):
            if u in nodes_to_include and v in nodes_to_include:
                subgraph_edges.append({
                    "id": f"{u}_{v}_{k}",
                    "source": u,
                    "target": v,
                    "relation": attrs.get("relation", "RELATED_TO"),
                    "properties": attrs
                })

        return {
            "nodes": subgraph_nodes,
            "edges": subgraph_edges
        }

    def get_context_summary(self, user_id: str = "user_self") -> str:
        """
        Generates a rich textual summary of user's personal context,
        family members, upcoming life events, and interconnected liabilities/assets.
        Used for GraphRAG prompt grounding.
        """
        self.load()
        if not self.graph.has_node(user_id):
            return "No personal knowledge graph context registered yet."

        user_props = self.graph.nodes[user_id]
        lines = [f"User Profile: {user_props.get('name', 'User')} | Risk Profile: {user_props.get('risk_profile', 'Moderate')}"]

        # Family / Dependents
        dependents = []
        for _, target, data in self.graph.out_edges(user_id, data=True):
            if data.get("relation") == "HAS_DEPENDENT" or self.graph.nodes[target].get("label") == "FamilyMember":
                f_data = self.graph.nodes[target]
                rel = f_data.get("relation", "Dependent")
                age = f"{f_data.get('age', '')} yrs" if f_data.get('age') else ""
                dependents.append(f"{f_data.get('name', target)} ({rel} {age})")
        if dependents:
            lines.append("Dependents & Family: " + ", ".join(dependents))

        # Life Events & Goals
        goals = []
        for _, target, data in self.graph.out_edges(user_id, data=True):
            if data.get("relation") == "PLANS_FOR" or self.graph.nodes[target].get("label") == "LifeEvent":
                g_data = self.graph.nodes[target]
                title = g_data.get("title", g_data.get("name", target))
                yr = g_data.get("target_year", "Future")
                amt = g_data.get("target_amount", "")
                amt_str = f" - ₹{amt:,}" if amt else ""
                goals.append(f"{title} (Target: {yr}{amt_str})")
        if goals:
            lines.append("Key Life Events & Milestones: " + " | ".join(goals))

        # Liabilities / Obligations
        liabilities = []
        for _, target, data in self.graph.out_edges(user_id, data=True):
            if data.get("relation") == "OWES" or self.graph.nodes[target].get("label") == "Liability":
                l_data = self.graph.nodes[target]
                emi = l_data.get("monthly_emi", 0)
                liabilities.append(f"{l_data.get('name', target)}: Outst. ₹{l_data.get('outstanding_amount', 0):,} (EMI ₹{emi:,}/mo)")
        if liabilities:
            lines.append("Active Liabilities: " + ", ".join(liabilities))

        return "\n".join(lines)
