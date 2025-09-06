from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from typing import TypedDict, List
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings


class GraphState(TypedDict):
    context: List[str]
    response: str


class notes_generator:

    def __init__(
        self,
        llm_model: str = "gpt-5",
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
        docs = self.vectorstore.similarity_search("", k=1000)
        state["context"] = [doc.page_content for doc in docs]
        return state

    def llm_node(self, state: GraphState):
        context = "\n\n".join(state["context"])
        prompt = PromptTemplate(
            template="""You are an academic expert who specializes in summarizing educational content into clear, structured notes for students.

Your task is to generate well detailed study notes from the provided context. The notes should follow these rules:
- Use bullet points for clarity.
- Include definitions, key facts, important concepts, and examples where applicable.
- Use simple and clear language for easy understanding.
- Preserve important technical terminology, formulas, or figures if present.
- Avoid copying the context verbatim — rephrase and simplify where appropriate.
- Organize content logically with proper indentation and formatting.
- Do not use '#' 

 Context:
{context}

Now generate the notes below:
""",
            input_variables=["context"],
        )
        formatted_prompt = prompt.format(context=context)
        response = self.llm.invoke(formatted_prompt)
        state["response"] = response.content
        return state

    def build_graph(self):

        builder = StateGraph(GraphState)
        builder.add_node("llm", self.llm_node)
        builder.add_node("retriever", self.retriever_node)

        builder.set_entry_point("retriever")
        builder.add_edge("retriever", "llm")
        builder.set_finish_point("llm")

        return builder.compile()

    def init_state(self) -> GraphState:
        return {"context": [], "response": ""}

    def run(self, state: GraphState) -> GraphState:
        return self.graph.invoke(state)

