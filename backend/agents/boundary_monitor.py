from typing import Any, Dict
from backend.agents.base_agent import BaseAgent

class BoundaryMonitorAgent(BaseAgent):
    """Monitors administrative boundaries and alerts on encroachment."""

    def __init__(self):
        super().__init__("BoundaryMonitor")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Monitoring boundaries")
        boundaries = input_data.get("boundaries", [])
        alerts = []

        for boundary in boundaries:
            if boundary.get("encroachment_detected", False):
                alerts.append({
                    "boundary_id": boundary.get("id"),
                    "severity": boundary.get("severity", "medium"),
                    "message": f"Encroachment detected at boundary {boundary.get('id')}"
                })

        return {
            "alerts": alerts,
            "total_alerts": len(alerts),
            "status": "critical" if len(alerts) > 0 else "normal"
        }
