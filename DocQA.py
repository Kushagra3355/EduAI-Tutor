from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from typing import TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


class GraphState(TypedDict):
    query: str
    messages: List[BaseMessage]
    response: str
    context: List[str]


class DocumentQA:

    def __init__(
        self,
        llm_model: str = "gpt-4o-mini",
        faiss_path: str = "faiss_index_local",
        embed_model: str = "text-embedding-3-small",
    ):
        self.llm = ChatOpenAI(model=llm_model)
        self.vectorstore = FAISS.load_local(
            faiss_path,
            embeddings=OpenAIEmbeddings(model=embed_model),
            allow_dangerous_deserialization=True,
        )
        self.graph = self.build_graph()

    def retriever_node(self, state: GraphState) -> GraphState:
        if not self.vectorstore:
            print("Warning: Vectorstore not initialized")
            state["context"] = []
            return state
        docs = self.vectorstore.similarity_search(state["query"], k=2)
        state["context"] = [doc.page_content for doc in docs]
        return state

    def memory_node(self, state: GraphState) -> GraphState:
        query = state["query"]
        state["messages"].append(HumanMessage(content=query))
        return state

    def llm_node(self, state: GraphState) -> GraphState:

        system_prompt = """You are a helpful and learned teacher. You help the users understand a study material in a simple manner
        based on their questions and the context retrieved. Keep the explaination simple, to the point and precise , give suitable examples for 
        the explaination also if possible."""
        context = "\n\n".join(state["context"])
        messages = [
            {"role": "system", "content": system_prompt},
            *state["messages"],
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion:\n{state['query']}",
            },
        ]
        response = self.llm.invoke(messages)
        state["messages"].append(AIMessage(content=response.content))
        state["response"] = response.content
        return state

    def build_graph(self):

        builder = StateGraph(GraphState)
        builder.add_node("memory", self.memory_node)
        builder.add_node("retriever", self.retriever_node)
        builder.add_node("llm", self.llm_node)

        builder.set_entry_point("memory")
        builder.add_edge("memory", "retriever")
        builder.add_edge("retriever", "llm")
        builder.set_finish_point("llm")
        return builder.compile()

    def init_state(self) -> GraphState:
        return {
            "query": "",
            "messages": [],
            "context": [],
            "response": "",
        }

    def run(self, query: str) -> GraphState:
        state = self.init_state()
        state["query"] = query
        return self.graph.invoke(state)
