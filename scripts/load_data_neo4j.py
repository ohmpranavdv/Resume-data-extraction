def run_resume_graph_pipeline(llm_response):

    from neo4j import GraphDatabase
    from llm_model import extract_all_resumes
    #from langchain_query import run_langchain_query
    #Uniform Resource Identifier (I) /Locator (L)

    URI = "bolt://localhost:7687"
    USERNAME = "neo4j"
    PASSWORD = "password"

    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))


    def create_schema(session):

        constraints = [
            """
            CREATE CONSTRAINT person_name IF NOT EXISTS
            FOR (p:Person)
            REQUIRE p.name IS UNIQUE
            """,
            """
            CREATE CONSTRAINT skill_name IF NOT EXISTS
            FOR (s:Skill)
            REQUIRE s.name IS UNIQUE
            """,
            """
            CREATE CONSTRAINT softskill_name IF NOT EXISTS
            FOR (s:SoftSkill)
            REQUIRE s.name IS UNIQUE
            """,
            """
            CREATE CONSTRAINT company_name IF NOT EXISTS
            FOR (c:Company)
            REQUIRE c.name IS UNIQUE
            """,
            """
            CREATE CONSTRAINT role_name IF NOT EXISTS
            FOR (r:Role)
            REQUIRE r.name IS UNIQUE
            """,
            """
            CREATE CONSTRAINT education_name IF NOT EXISTS
            FOR (e:Education)
            REQUIRE e.name IS UNIQUE
            """
        ]

        for query in constraints:
            session.run(query)


    def insert_data(session, data):

        for person in data:

            name = person["name"]

            session.run(
                "MERGE (p:Person {name:$name})",
                name=name
            )

            for skill in person["skills"]["technical"]:
                session.run("""
                MATCH (p:Person {name:$name})
                MERGE (s:Skill {name:$skill})
                MERGE (p)-[:HAS_TECH_SKILL]->(s)
                """, name=name, skill=skill)

            for skill in person["skills"]["soft"]:
                session.run("""
                MATCH (p:Person {name:$name})
                MERGE (s:SoftSkill {name:$skill})
                MERGE (p)-[:HAS_SOFT_SKILL]->(s)
                """, name=name, skill=skill)

            for company in person["companies"]:
                session.run("""
                MATCH (p:Person {name:$name})
                MERGE (c:Company {name:$company})
                MERGE (p)-[:WORKED_AT]->(c)
                """, name=name, company=company)

            for role in person["roles"]:
                session.run("""
                MATCH (p:Person {name:$name})
                MERGE (r:Role {name:$role})
                MERGE (p)-[:HELD_ROLE]->(r)
                """, name=name, role=role)

            for edu in person["education"]:
                session.run("""
                MATCH (p:Person {name:$name})
                MERGE (e:Education {name:$edu})
                MERGE (p)-[:STUDIED_AT]->(e)
                """, name=name, edu=edu)




    print("Extracting structured data using Gemini...")

    extracted_data=llm_response ###########


    with driver.session() as session:

        print("Creating schema...")
        create_schema(session)

        print("Inserting extracted data into Neo4j...")
        insert_data(session, extracted_data)

        print("Data successfully inserted!")


    # Start LangChain Query System
   