from resume_processing import main
from llm_model import extract_all_resumes
from resume_processing import main
from load_data_neo4j import run_resume_graph_pipeline

def control_flow():
    print("Control got from monitor & sent to resume_processing")
    resume_text = main()
    print(resume_text)
    print("/n")
    llm_response = extract_all_resumes(resume_text)
    run_resume_graph_pipeline(llm_response)
    
    


