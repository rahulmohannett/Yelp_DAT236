"""
AI-powered restaurant recommendation chatbot using LangChain, LangGraph, and Tavily.
"""
from typing import List, Dict, Any, Optional, TypedDict
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from app.config import settings
from app.models import Restaurant, UserPreference, Review


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
    user_id: int
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

    def __init__(self, db: Session):
        self.db = db
        # Set to gemini-2.0-flash per Lab 1 requirements
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
        user_id: int,
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
        prefs = (
            self.db.query(UserPreference)
            .filter(UserPreference.user_id == state["user_id"])
            .first()
        )
        preferences = None
        if prefs:
            preferences = {
                "cuisine_preferences": prefs.cuisine_preferences or [],
                "price_range": prefs.price_range,
                "dietary_needs": prefs.dietary_needs or [],
                "location": prefs.location,
                "ambiance_preferences": prefs.ambiance_preferences or [],
                "sort_preference": prefs.sort_preference,
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

        # Fill gaps from saved preferences
        prefs = state.get("preferences")
        if prefs:
            if "cuisine_type" not in filters and prefs.get("cuisine_preferences"):
                filters["cuisine_type"] = prefs["cuisine_preferences"][0]
            if "price_range" not in filters and prefs.get("price_range"):
                filters["price_range"] = prefs["price_range"]
            if "location" not in filters and prefs.get("location"):
                filters["location"] = prefs["location"]
            if "dietary_needs" not in filters and prefs.get("dietary_needs"):
                filters["dietary_needs"] = prefs["dietary_needs"][0]

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
        query = self.db.query(Restaurant)

        if filters.get("location"):
            query = query.filter(
                or_(
                    Restaurant.city.ilike(f"%{filters['location']}%"),
                    Restaurant.state.ilike(f"%{filters['location']}%"),
                )
            )

        return {"restaurants": query.all()}

    async def node_rank_restaurants(self, state: GraphState) -> dict:
        restaurants = state["restaurants"]
        filters = state["filters"]
        prefs = state.get("preferences")

        scored = []
        for r in restaurants:
            score = 10.0

            # Cuisine match
            if filters.get("cuisine_type"):
                if filters["cuisine_type"].lower() not in (r.cuisine_type or "").lower():
                    score *= 0.1

            # Dietary hard constraint
            if filters.get("dietary_needs"):
                if "vegan" in filters["dietary_needs"].lower() and "steakhouse" in (r.cuisine_type or "").lower():
                    score *= 0.0

            # Price match
            if filters.get("price_range") and r.price_range != filters["price_range"]:
                score *= 0.5

            # Rating bonus
            avg_rating = (
                self.db.query(func.avg(Review.rating))
                .filter(Review.restaurant_id == r.id)
                .scalar()
            )
            if avg_rating:
                score += float(avg_rating) * 2

            # Preference tie-breaker
            if prefs and r.cuisine_type in (prefs.get("cuisine_preferences") or []):
                score += 1.0

            if score > 0:
                scored.append((r, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        ranked = [r for r, _ in scored]

        recommendations = [
            {
                "restaurant": self._format_restaurant(r),
                "reason": self._generate_reason(r, filters, prefs),
            }
            for r in ranked[:5]
        ]

        return {"ranked_restaurants": ranked, "recommendations": recommendations}

    async def node_generate_response(self, state: GraphState) -> dict:
        ctx = f"User query: {state['message']}\n\n"

        if state.get("preferences"):
            ctx += f"User preferences: {state['preferences']}\n\n"
        if state.get("tavily_results"):
            ctx += f"Live Web Info:\n{state['tavily_results']}\n\n"

        ctx += "Top recommended restaurants:\n"
        for i, r in enumerate(state["ranked_restaurants"][:5], 1):
            avg = (
                self.db.query(func.avg(Review.rating))
                .filter(Review.restaurant_id == r.id)
                .scalar()
            )
            rating_str = f"{avg:.1f}★" if avg else "No ratings"
            ctx += f"{i}. {r.name} ({r.cuisine_type}, {r.price_range}) - {rating_str}\n"

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
    def _format_restaurant(self, restaurant: Restaurant) -> Dict[str, Any]:
        avg_rating = (
            self.db.query(func.avg(Review.rating))
            .filter(Review.restaurant_id == restaurant.id)
            .scalar()
        )
        review_count = (
            self.db.query(func.count(Review.id))
            .filter(Review.restaurant_id == restaurant.id)
            .scalar()
        )
        return {
            "id": restaurant.id,
            "name": restaurant.name,
            "cuisine_type": restaurant.cuisine_type,
            "price_range": restaurant.price_range,
            "address": restaurant.address,
            "city": restaurant.city,
            "average_rating": float(avg_rating) if avg_rating else None,
            "review_count": review_count or 0,
            "created_at": restaurant.created_at.isoformat() if restaurant.created_at else None,
            "updated_at": restaurant.updated_at.isoformat() if restaurant.updated_at else None
        }

    def _generate_reason(
        self,
        restaurant: Restaurant,
        filters: Dict[str, Any],
        preferences: Optional[Dict[str, Any]],
    ) -> str:
        reasons = []

        if filters.get("cuisine_type") and restaurant.cuisine_type:
            if filters["cuisine_type"].lower() in restaurant.cuisine_type.lower():
                reasons.append(f"Matches your {restaurant.cuisine_type} preference")

        if filters.get("price_range") and restaurant.price_range == filters["price_range"]:
            reasons.append("Within your price range")

        avg = (
            self.db.query(func.avg(Review.rating))
            .filter(Review.restaurant_id == restaurant.id)
            .scalar()
        )
        if avg and avg >= 4.5:
            reasons.append("Highly rated")

        if filters.get("occasion"):
            reasons.append(f"Great for {filters['occasion']} occasions")

        return "; ".join(reasons) if reasons else "Popular choice"