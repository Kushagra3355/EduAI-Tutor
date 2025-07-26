from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from typing import TypedDict, List
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


class GraphState(TypedDict):
    context: List[str]
    response: str


class mcqs_generator:

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
        docs = self.vectorstore.similarity_search("", k=1000)
        state["context"] = [doc.page_content for doc in docs]
        return state

    def llm_node(self, state: GraphState):
        context = "\n\n".join(state["context"])
        prompt = PromptTemplate(
            template="""You are an expert question paper setter for academic exams.

Generate 10 multiple choice questions (MCQs) based on the following context. Each question must have:
- Exactly 4 options (labeled A, B, C, D)
- Only one correct answer
- No repetition of questions
- The difficulty should be a mix of basic understanding and conceptual reasoning
- Do not use '#'

After listing all 10 questions, display the **correct answer** for each at the end in the format:
Answer Key:
1. A
2. C
...
10. B

Context:
{context}

Generate the questions now:
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
