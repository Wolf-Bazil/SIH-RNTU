from typing import Any, Dict, List, Tuple
import heapq
import numpy as np
from backend.agents.base_agent import BaseAgent

class EcoRoutePlannerAgent(BaseAgent):
    """
    Computes optimal eco-friendly routes using a modified A* algorithm.
    J_route = Σ [ d(s_i, s_{i+1}) * (1 + ω * E(s_i, s_{i+1})) ]
    where d is distance, E is environmental cost, ω is weight.
    """

    def __init__(self, omega: float = 0.5):
        super().__init__("EcoRoutePlanner")
        self.omega = omega

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Euclidean distance heuristic."""
        return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

    def _environmental_cost(self, a: Tuple[int, int], b: Tuple[int, int], env_grid: np.ndarray) -> float:
        """Average environmental cost between two points."""
        x1, y1 = a
        x2, y2 = b
        if 0 <= x1 < env_grid.shape[0] and 0 <= y1 < env_grid.shape[1] and \
           0 <= x2 < env_grid.shape[0] and 0 <= y2 < env_grid.shape[1]:
            return (env_grid[x1, y1] + env_grid[x2, y2]) / 2
        return 0.0

    def modified_a_star(self, grid: np.ndarray, start: Tuple[int, int],
                        goal: Tuple[int, int], env_grid: np.ndarray) -> List[Tuple[int, int]]:
        """
        Modified A* algorithm minimizing J_route.
        J_route = Σ d(s_i, s_{i+1}) * (1 + ω * E(s_i, s_{i+1}))
        """
        rows, cols = grid.shape
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, goal)}

        neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1),
                     (-1, -1), (-1, 1), (1, -1), (1, 1)]

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]

            for dx, dy in neighbors:
                neighbor = (current[0] + dx, current[1] + dy)

                if not (0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols):
                    continue
                if grid[neighbor[0], neighbor[1]] == 1:  # Obstacle
                    continue

                # Distance between current and neighbor
                d = np.sqrt(dx**2 + dy**2)

                # Environmental cost
                E = self._environmental_cost(current, neighbor, env_grid)

                # J_route cost for this step
                step_cost = d * (1 + self.omega * E)

                tentative_g = g_score[current] + step_cost

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return []  # No path found

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Computing eco-friendly route using modified A*")
        grid = np.array(input_data.get("grid", np.zeros((50, 50))))
        env_grid = np.array(input_data.get("environmental_grid", np.random.random((50, 50))))
        start = tuple(input_data.get("start", (0, 0)))
        goal = tuple(input_data.get("goal", (49, 49)))

        path = self.modified_a_star(grid, start, goal, env_grid)

        # Calculate total J_route cost
        total_cost = 0.0
        for i in range(len(path) - 1):
            d = self._heuristic(path[i], path[i+1])
            E = self._environmental_cost(path[i], path[i+1], env_grid)
            total_cost += d * (1 + self.omega * E)

        return {
            "path": path,
            "path_length": len(path),
            "total_cost_J_route": total_cost,
            "found": len(path) > 0
        }
