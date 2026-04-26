"""
AI-powered restaurant recommendation chatbot using LangChain, LangGraph, and Tavily.
"""
from typing import List, Dict, Any, Optional, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from bson import ObjectId

from app.config import settings
from app.models import RESTAURANTS, USER_PREFERENCES, REVIEWS, to_str_id


class QueryFilters(BaseModel):
    """Structured output for search criteria extracted from user message."""
    cuisine_type: Optional[str] = Field(None, description="Type of cuisine (Italian, Mexican, Japanese, etc.)")
    price_range: Optional[str] = Field(None, description="Price range: $, $$, $$$, $$$$")
    dietary_needs: Optional[str] = Field(None, description="Dietary restrictions (vegan, vegetarian, gluten-free, etc.)")
    occasion: Optional[str] = Field(None, description="Type of occasion (romantic, casual, business, family, etc.)")
    ambiance: Optional[str] = Field(None, description="Desired atmosphere (romantic, casual, upscale, cozy, etc.)")
    location: Optional[str] = Field(None, description="City or area")
    requires_web_search: bool = Field(False, description="Set to True if the query asks for trending places, live info, or currently open restaurants.")


class GraphState(TypedDict):
    user_id: str                        # MongoDB ObjectId string
    message: str
    conversation_history: List[Dict[str, str]]
    preferences: Optional[Dict[str, Any]]
    filters: Dict[str, Any]
    requires_web_search: bool
    tavily_results: str
    restaurants: List[Any]
    ranked_restaurants: List[Any]
    recommendations: List[Dict[str, Any]]
    response_text: str


class RestaurantChatbot:
    """AI chatbot for restaurant recommendations with LangGraph pipeline."""

    def __init__(self, db):
        self.db = db                    # Motor async database instance
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=settings.GOOGLE_API_KEY,
            temperature=0.7,
        )
        self.structured_llm = self.llm.with_structured_output(QueryFilters)
        self.tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)
        self.graph = self._build_graph()

    # ------------------------------------------------------------------ graph
    def _build_graph(self):
        wf = StateGraph(GraphState)

        wf.add_node("load_preferences", self.node_load_preferences)
        wf.add_node("extract_filters", self.node_extract_filters)
        wf.add_node("tavily_search", self.node_tavily_search)
        wf.add_node("db_search", self.node_db_search)
        wf.add_node("rank_restaurants", self.node_rank_restaurants)
        wf.add_node("generate_response", self.node_generate_response)

        wf.add_edge(START, "load_preferences")
        wf.add_edge("load_preferences", "extract_filters")
        wf.add_conditional_edges(
            "extract_filters",
            lambda s: "tavily_search" if s.get("requires_web_search") else "db_search",
        )
        wf.add_edge("tavily_search", "db_search")
        wf.add_edge("db_search", "rank_restaurants")
        wf.add_edge("rank_restaurants", "generate_response")
        wf.add_edge("generate_response", END)

        return wf.compile()

    # -------------------------------------------------------------- entry point
    async def process_query(
        self,
        user_id: str,
        message: str,
        conversation_history: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        initial_state: GraphState = {
            "user_id": user_id,
            "message": message,
            "conversation_history": conversation_history,
            "preferences": None,
            "filters": {},
            "requires_web_search": False,
            "tavily_results": "",
            "restaurants": [],
            "ranked_restaurants": [],
            "recommendations": [],
            "response_text": "",
        }

        final = await self.graph.ainvoke(initial_state)
        return {
            "message": final["response_text"],
            "recommendations": final["recommendations"],
        }

    # ------------------------------------------------------------------ nodes
    async def node_load_preferences(self, state: GraphState) -> dict:
        try:
            oid = ObjectId(state["user_id"])
        except Exception:
            return {"preferences": None}

        prefs = await self.db[USER_PREFERENCES].find_one({"user_id": oid})
        preferences = None
        if prefs:
            preferences = {
                "cuisine_preferences": prefs.get("cuisine_preferences") or [],
                "price_range": prefs.get("price_range"),
                "dietary_needs": prefs.get("dietary_needs") or [],
                "location": prefs.get("location"),
                "ambiance_preferences": prefs.get("ambiance_preferences") or [],
                "sort_preference": prefs.get("sort_preference"),
            }
        return {"preferences": preferences}

    async def node_extract_filters(self, state: GraphState) -> dict:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Extract restaurant search criteria from the user's message. "
                       "If the user asks about trending, currently open, or live info, set requires_web_search=True."),
            ("human", "{message}"),
        ])
        chain = prompt | self.structured_llm
        output: QueryFilters = await chain.ainvoke({"message": state["message"]})

        filters = output.model_dump(exclude_none=True)
        requires_web = filters.pop("requires_web_search", False)

        return {"filters": filters, "requires_web_search": requires_web}

    async def node_tavily_search(self, state: GraphState) -> dict:
        query = f"restaurants {state['message']}"
        if state["filters"].get("location"):
            query += f" in {state['filters']['location']}"
        try:
            results = self.tavily.search(query=query, search_depth="basic")
            context = "\n".join(
                f"- {r['title']}: {r['content']}" for r in results.get("results", [])
            )
        except Exception as e:
            context = f"Web search failed: {e}"
        return {"tavily_results": context}

    async def node_db_search(self, state: GraphState) -> dict:
        filters = state["filters"]
        query = {}
        import re

        if filters.get("location"):
            raw_location = filters["location"].strip().lower()
            if raw_location not in {"near me", "nearby", "me"}:
                pattern = re.compile(filters["location"], re.IGNORECASE)
                query["$or"] = [{"city": pattern}, {"state": pattern}]

        restaurants = await self.db[RESTAURANTS].find(query).to_list(100)
        # Normalize _id → id
        restaurants = [to_str_id(r) for r in restaurants]
        return {"restaurants": restaurants}

    async def node_rank_restaurants(self, state: GraphState) -> dict:
        restaurants = state["restaurants"]
        filters = state["filters"]
        prefs = state.get("preferences")

        scored = []
        for r in restaurants:
            score = 10.0

            # Cuisine match - hard requirement when user specifies cuisine
            if filters.get("cuisine_type"):
                user_cuisine = filters["cuisine_type"].lower()
                rest_cuisine = (r.get("cuisine_type") or "").lower()
                # Allow common synonyms (sushi -> japanese)
                cuisine_synonyms = {
                    "sushi": "japanese",
                    "ramen": "japanese",
                    "pasta": "italian",
                    "pizza": "italian",
                    "tacos": "mexican",
                    "burritos": "mexican",
                    "burger": "american",
                    "burgers": "american",
                    "steak": "american",
                    "curry": "indian",
                    "noodles": "chinese",
                }
                normalized_user = cuisine_synonyms.get(user_cuisine, user_cuisine)
                if normalized_user not in rest_cuisine and user_cuisine not in rest_cuisine:
                    continue  # Skip this restaurant entirely

            # Dietary hard constraint
            if filters.get("dietary_needs"):
                if "vegan" in filters["dietary_needs"].lower() and \
                   "steakhouse" in (r.get("cuisine_type") or "").lower():
                    score *= 0.0

            # Price match
            if filters.get("price_range") and r.get("price_range") != filters["price_range"]:
                score *= 0.5

            # Rating bonus from reviews
            avg_rating = await self._get_avg_rating(r["id"])
            if avg_rating:
                score += avg_rating * 2

            # Preference tie-breaker
            if prefs and r.get("cuisine_type") in (prefs.get("cuisine_preferences") or []):
                score += 1.0

            if score > 0:
                scored.append((r, score, avg_rating))

        scored.sort(key=lambda x: x[1], reverse=True)

        recommendations = [
            {
                "restaurant": self._format_restaurant(r, avg),
                "reason": self._generate_reason(r, filters, prefs, avg),
            }
            for r, _, avg in scored[:3]
        ]

        return {
            "ranked_restaurants": [r for r, _, _ in scored[:3]],
            "recommendations": recommendations,
        }

    async def node_generate_response(self, state: GraphState) -> dict:
        ctx = f"User query: {state['message']}\n\n"

        if state.get("preferences"):
            ctx += f"User preferences: {state['preferences']}\n\n"
        if state.get("tavily_results"):
            ctx += f"Live Web Info:\n{state['tavily_results']}\n\n"

        ctx += "Top recommended restaurants:\n"
        for i, r in enumerate(state["ranked_restaurants"], 1):
            avg = await self._get_avg_rating(r["id"])
            rating_str = f"{avg:.1f}★" if avg else "No ratings"
            ctx += f"{i}. {r['name']} ({r.get('cuisine_type')}, {r.get('price_range')}) - {rating_str}\n"

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a friendly restaurant recommendation assistant.\n"
                "Provide helpful, conversational responses about restaurant recommendations.\n"
                "If web search info is present, synthesize it to inform the user about trends or live status.\n"
                "Be warm and personable. Explain why you're recommending each restaurant.\n"
                "Keep responses concise but informative.",
            ),
            ("human", "{context}"),
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({"context": ctx})
        return {"response_text": response.content}

    # ------------------------------------------------------------ helpers
    async def _get_avg_rating(self, restaurant_id: str) -> Optional[float]:
        """Fetch average rating for a restaurant from MongoDB reviews."""
        try:
            oid = ObjectId(restaurant_id)
        except Exception:
            return None
        reviews = await self.db[REVIEWS].find(
            {"restaurant_id": oid}, {"rating": 1}
        ).to_list(None)
        ratings = [r["rating"] for r in reviews if "rating" in r]
        return sum(ratings) / len(ratings) if ratings else None

    def _format_restaurant(self, restaurant: dict, avg_rating: Optional[float]) -> Dict[str, Any]:
        return {
            "id": restaurant["id"],
            "name": restaurant.get("name"),
            "cuisine_type": restaurant.get("cuisine_type"),
            "price_range": restaurant.get("price_range"),
            "address": restaurant.get("address"),
            "city": restaurant.get("city"),
            "state": restaurant.get("state"),
            "zip_code": restaurant.get("zip_code"),
            "phone": restaurant.get("phone"),
            "website": restaurant.get("website"),
            "hours": restaurant.get("hours"),
            "amenities": restaurant.get("amenities", []),
            "average_rating": avg_rating,
            "review_count": 0,          # populated by rank node already
            "photos": restaurant.get("photos", []),
            "created_at": restaurant["created_at"].isoformat() if hasattr(restaurant.get("created_at"), "isoformat") else str(restaurant.get("created_at", "")),
            "updated_at": restaurant["updated_at"].isoformat() if hasattr(restaurant.get("updated_at"), "isoformat") else str(restaurant.get("updated_at", "")),
        }

    def _generate_reason(
        self,
        restaurant: dict,
        filters: Dict[str, Any],
        preferences: Optional[Dict[str, Any]],
        avg_rating: Optional[float],
    ) -> str:
        reasons = []

        if filters.get("cuisine_type") and restaurant.get("cuisine_type"):
            if filters["cuisine_type"].lower() in restaurant["cuisine_type"].lower():
                reasons.append(f"Matches your {restaurant['cuisine_type']} preference")

        if filters.get("price_range") and restaurant.get("price_range") == filters["price_range"]:
            reasons.append("Within your price range")

        if avg_rating and avg_rating >= 4.5:
            reasons.append("Highly rated")

        if filters.get("occasion"):
            reasons.append(f"Great for {filters['occasion']} occasions")

        return "; ".join(reasons) if reasons else "Popular choice"