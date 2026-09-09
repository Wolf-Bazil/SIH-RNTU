from typing import Any, Dict, List

from backend.agents.base_agent import BaseAgent

# Plain-language meaning of each driver, so an explanation can be read by a
# fisherman or a district officer rather than only by the model's author.
_DRIVER_TEXT = {
    "sst": ("Sea surface temperature",
            "Warm water is the fuel for a cyclone. Above about 28 °C a system can "
            "strengthen quickly."),
    "wind": ("Surface wind speed",
             "How hard the wind is blowing right now at 10 m above the sea."),
    "precipitation": ("Rainfall rate",
                      "Heavy rain adds flooding risk on the coast and inland."),
    "rainfall": ("Rainfall rate",
                 "Heavy rain adds flooding risk on the coast and inland."),
    "wave_height": ("Significant wave height",
                    "How high the sea is running. Above 3 m, INCOIS issues a high "
                    "wave warning."),
    "pressure_deficit": ("Pressure deficit",
                         "How far below normal the air pressure has fallen. A deeper "
                         "low means a stronger system."),
    "sst_suitability": ("SST suitability",
                        "How close the water temperature is to the band fish shoal in."),
    "sea_state_suitability": ("Sea state suitability",
                              "Whether small craft can actually work in this sea."),
}


class XAIAuditorAgent(BaseAgent):
    """Explains an index by ranking what actually drove it.

    Takes the ``components`` dict an agent returned and reports each driver's
    share of the final score, so the explanation reflects the computation that
    ran rather than the fixed weights the previous placeholder always reported.
    """

    def __init__(self):
        super().__init__("XAIAuditor")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Generating XAI explanation")

        components: Dict[str, float] = input_data.get("components") or {}
        weights: Dict[str, float] = input_data.get("weights") or {}
        score = input_data.get("score")
        index_name = input_data.get("index", "index")

        if not components:
            return {
                "explanation": {
                    "summary": "No component breakdown was supplied, so this result "
                               "cannot be attributed to individual drivers.",
                    "factors": [],
                },
                "live": False,
            }

        # Contribution is the weighted value; share is that as a fraction of the
        # total, which is what "why is the number this high" actually asks.
        contributions = {
            name: weights.get(name, 1.0) * float(value)
            for name, value in components.items()
        }
        total = sum(contributions.values())

        factors: List[Dict[str, Any]] = []
        for name, contribution in sorted(contributions.items(),
                                         key=lambda kv: kv[1], reverse=True):
            label, meaning = _DRIVER_TEXT.get(name, (name.replace("_", " ").title(), ""))
            share = (contribution / total) if total > 0 else 0.0
            value = float(components[name])
            factors.append({
                "name": label,
                "key": name,
                "normalised_value": round(value, 4),
                "share_of_result": round(share, 4),
                "influence": "high" if share >= 0.5 else "medium" if share >= 0.2 else "low",
                "meaning": meaning,
            })

        top = factors[0]
        summary = (
            f"{index_name} is driven mainly by {top['name'].lower()}, which accounts "
            f"for {top['share_of_result'] * 100:.0f}% of the result."
        )
        if score is not None:
            summary = f"The score is {float(score):.2f}. " + summary

        return {
            "index": index_name,
            "score": score,
            "explanation": {"summary": summary, "factors": factors},
            "observed_at": input_data.get("observed_at"),
            "live": True,
        }
