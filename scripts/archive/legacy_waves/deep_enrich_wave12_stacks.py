import json, re, urllib.request, ssl
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

with open('data/wave12_final_pure_tech_32.json') as f:
    roles = json.load(f)

options = Options()
options.add_argument('--headless=new')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
driver = webdriver.Chrome(options=options)

print(f"Deeply inspecting and extracting accurate tech stacks for {len(roles)} roles...")

for idx, r in enumerate(roles, 1):
    u = r['url']
    t = r['title']
    c = r['company']
    
    try:
        driver.get(u)
        time_sleep = 2
        import time
        time.sleep(time_sleep)
        b_text = driver.find_element('tag name', 'body').text
        t_full = (t + " " + b_text).lower()

        stack_items = []
        if any(k in t_full for k in ['c#', '.net', 'asp.net', 'dotnet']): stack_items.append('C#/.NET Core')
        if any(k in t_full for k in ['azure', 'azure cloud']): stack_items.append('Azure Cloud')
        if any(k in t_full for k in ['node', 'nodejs', 'node.js']): stack_items.append('Node.js')
        if 'typescript' in t_full: stack_items.append('TypeScript')
        if any(k in t_full for k in ['microservices', 'distributed systems']): stack_items.append('Microservices/Distributed Systems')
        if any(k in t_full for k in ['rest', 'grpc', 'api']): stack_items.append('REST/gRPC APIs')
        if any(k in t_full for k in ['kafka', 'event-driven', 'rabbit', 'messaging']): stack_items.append('Kafka/Event Streaming')
        if any(k in t_full for k in ['sql', 'postgres', 'postgresql', 'cosmos', 'mysql', 'mongodb']): stack_items.append('SQL/NoSQL Databases')
        if any(k in t_full for k in ['ai agent', 'llm', 'langchain', 'langgraph', 'mcp']): stack_items.append('AI Agent Workflows')
        if any(k in t_full for k in ['java', 'spring', 'springboot']): stack_items.append('Java/Spring Boot')
        if any(k in t_full for k in ['react', 'next.js', 'frontend']): stack_items.append('React.js')
        if any(k in t_full for k in ['golang', ' go ']): stack_items.append('Go')
        if any(k in t_full for k in ['aws', 'cloud architecture', 'gcp']): stack_items.append('Cloud Architecture')
        if any(k in t_full for k in ['kubernetes', 'docker', 'containers']): stack_items.append('Docker/Kubernetes')

        if not stack_items:
            stack_items = ['Backend Architecture', 'Microservices', 'REST APIs', 'Cloud Services']

        tech_stack_str = ", ".join(stack_items[:5])
        r['tech_stack'] = tech_stack_str
        print(f"[{idx:2d}] {c} - {t} -> {tech_stack_str}")
    except Exception as e:
        print(f"[{idx:2d}] Error for {c}: {e}")

driver.quit()

with open('data/wave12_final_pure_tech_32.json', 'w') as f:
    json.dump(roles, f, indent=2)

print("Saved enriched stacks to data/wave12_final_pure_tech_32.json")
