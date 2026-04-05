import streamlit as st
import os
from langchain_community.graphs import Neo4jGraph
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()
neo4j_user = os.getenv("neo4j_user")
neo4j_password = os.getenv("neo4j_password")
google_api_neo4j = os.getenv("google_api_neo4j")

@st.cache_resource
def start_monitor():
    subprocess.Popen([sys.executable, "monitor.py"])

start_monitor()

# PAGE SETTINGS
st.set_page_config(
    page_title="Candidate Analyzer",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Candidate Analyzer Bot")



# CONNECT TO NEO4J


@st.cache_resource
def connect_graph():

    graph = Neo4jGraph(url="bolt://localhost:7687",username=neo4j_user,password=neo4j_password)
    graph.refresh_schema()


#schema = graph.get_schema()
#prompt = cypher_prompt.format(
#schema=schema,
#question=user_query)

    #llm used in chain
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, google_api_key=google_api_neo4j)

    cypher_prompt = PromptTemplate(
        input_variables=["schema", "question"],
        template="""You are a Neo4j Cypher expert.

Schema:
{schema}

Nodes: Person, Skill, SoftSkill, Company, Role, Education

Relationships:
(:Person)-[:HAS_TECH_SKILL]->(:Skill)
(:Person)-[:HAS_SOFT_SKILL]->(:SoftSkill)
(:Person)-[:WORKED_AT]->(:Company)
(:Person)-[:HELD_ROLE]->(:Role)
(:Person)-[:STUDIED_AT]->(:Education)

Rules:
- ALWAYS use toLower() and CONTAINS for string matching
- NEVER use = for string comparisons
- Use MATCH and WHERE

Return rules:
- If question asks for persons → RETURN p.name
- If question asks for skills → RETURN s.name
- If question asks for roles → RETURN r.name
- If question asks for both roles and skills → RETURN r.name, s.name
Examples:

Question: what are Jacky Wilson skills
Cypher:
MATCH (p:Person)-[:HAS_TECH_SKILL]->(s:Skill)
WHERE toLower(p.name) CONTAINS toLower("jacky wilson")
RETURN s.name

Question: give roles of kamalganth
Cypher:
MATCH (p:Person)-[:HELD_ROLE]->(r:Role)
WHERE toLower(p.name) CONTAINS toLower("kamalganth")
RETURN r.name

Question: give roles and skills of kamalganth
Cypher:
MATCH (p:Person)
WHERE toLower(p.name) CONTAINS toLower("kamalganth")
OPTIONAL MATCH (p)-[:HELD_ROLE]->(r:Role)
OPTIONAL MATCH (p)-[:HAS_TECH_SKILL]->(s:Skill)
RETURN r.name, s.name

Question: find persons with graphic design skill
Cypher:
CALL db.index.fulltext.queryNodes("SkillFullTextIndex", "graphic design~") 
YIELD node AS s
MATCH (p:Person)-[:HAS_TECH_SKILL]->(s)
RETURN p.name

Question: find persons who worked at mozilla
Cypher:
MATCH (p:Person)-[:WORKED_AT]->(c:Company)
WHERE toLower(c.name) CONTAINS toLower("mozilla")
RETURN p.name

Question: find persons with management soft skill
Cypher:
MATCH (p:Person)-[:HAS_SOFT_SKILL]->(s:SoftSkill)
WHERE toLower(s.name) CONTAINS toLower("management")
RETURN p.name

Question: find all persons
Cypher:
MATCH (p:Person)
RETURN p.name

Question: {question}
Cypher:"""
    )

    chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        cypher_prompt=cypher_prompt,
        verbose=True,# verbal logs in terminal
        allow_dangerous_requests=False, # full cypher #includes DDL in True
        return_direct=True #direct database output 
    )

    return chain


chain = connect_graph()

# CHAT HISTORY
#Stores previous chat messages
if "messages" not in st.session_state:
    st.session_state.messages = []
#loop;s through to diplay bubbles
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): #display bubble
        st.markdown(msg["content"])


# USER INPUT

question = st.chat_input("Ask about candidates, skills, experience...")#chat input bxo

if question: #when submitted question

    st.chat_message("user").markdown(question) #Shows the user message
    st.session_state.messages.append({"role": "user", "content": question}) #Stores it in chat history

    with st.spinner("Thinking...."):
        try:
            result = chain.invoke({"query": question})#injects question
            raw = result.get("result") or result.get("context", []) #Gets database output

            if isinstance(raw, list): #Check if results are a list
                if len(raw) == 0:
                    answer = "No results found."
                else:
                    rows = []

                    for r in raw: #get the vlaues from raw output
                        if r:
                            row = " | ".join(str(v) for v in r.values() if v)#converting values to string 
                            rows.append(row)

                    answer = "\n\n".join(rows)
            else:
                answer = str(raw)#hadling if not in list 

        except Exception as e:
            answer = f"Error: {e}"

    with st.chat_message("assistant"): #Displays answe
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer}) #Adds reply to chat history