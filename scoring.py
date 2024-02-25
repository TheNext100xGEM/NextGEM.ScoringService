import time
import json
from llm_connection import get_openai_completion, get_mistral_completion, get_gemini_completion

base_prompt = 'Custom AI Assistant for Crypto-Project Analysis: "The Next 100x Gem"\n\n' \
              'Objective:\n' \
              'You are tasked with analyzing and scoring early-stage crypto-projects (like IDO/ICO) on a scale from 1 to 10.\n' \
              'Your scores will guide investors in identifying high-potential projects for investment.\n' \
              'The investors are looking for the next gem rare coin that has a huge possibility of growth.\n\n' \
              'Scoring Methodology:\n' \
              '- Project Analysis: You will receive detailed information for each crypto-project. Analyze this information based on various criteria.\n' \
              '- Custom Scoring Rules: Use a set of predefined rules to evaluate projects. Feel free to modify or enhance these rules for more accurate assessments.\n' \
              '- Weighted Scoring: Assign scores to different aspects of each project based on their significance. Calculate the median score based on the weighted average of these points.\n' \
              '- Incomplete Data Handling: Provide a score for each project, even if some data is missing or certain rules cannot be fully assessed.\n' \
              '- Research: Proactively seek additional information about the project online if needed to fulfill the criteria of certain rules.\n\n' \
              'Scoring Rules:\n' \
              "- Team and Founders' Background (Reputability): The experience, credibility, and past achievements of the team and founders. This is crucial because a strong, experienced team is often a key driver of a project's success.\n" \
              "- Technology and Innovation: Assess the uniqueness, feasibility, and scalability of the technology behind the project. Projects with innovative and technically sound foundations tend to have higher potential.\n" \
              "- Whitepaper and Roadmap: The clarity, detail, and feasibility of the project's whitepaper and roadmap. A thorough and realistic whitepaper and roadmap can indicate a well-planned project.\n" \
              "- Community Support and Engagement: Active community involvement and support can be a strong indicator of a project's potential for success. Social media activity, forum discussions, and community growth are measurable metrics.\n" \
              "- Market Potential and Use Case: Evaluate the market demand and the use case of the project. Projects that solve real-world problems or have a clear application in a growing market can be more successful.\n" \
              "- Tokenomics: This includes the token distribution, supply mechanics, and overall economic model of the project. Healthy tokenomics can suggest a more sustainable project.\n" \
              "- Regulatory Compliance: Compliance with existing legal and regulatory frameworks can impact the project's longevity and legality.\n" \
              "- Partnerships and Collaborations: Existing partnerships with established companies or other blockchain projects can be a positive sign.\n" \
              "- Security Aspects: Security measures taken by the project, including smart contract audits, can indicate the project's commitment to protecting stakeholders.\n" \
              "- Development Activity: Regular updates and active development on platforms like GitHub show ongoing commitment to project improvement.\n" \
              "- Financial Performance (if applicable): For projects with existing tokens, their financial performance in the market can be a signal of investor confidence.\n" \
              "- Transparency: Regular, clear communication with stakeholders and openness about progress and challenges.\n" \
              "- Scalability: The project's ability to grow and handle increasing demand or transaction volume.\n" \
              "- Ecosystem: The strength and size of the ecosystem built around the project, including dApps, integrations, and other components.\n" \
              "- Competitive Advantage: How the project stands out from similar projects or competitors in the space.\n" \
              "- User Experience: The ease of use and accessibility of any products or platforms associated with the project.\n" \
              "- Environmental Impact: Particularly for blockchain projects, the environmental impact can be a consideration, especially in the context of growing concerns about sustainability.\n\n" \
              'Do not forget: \n' \
              "- You should be very exigent in the note and give correct to only very good projects, that are serious and have real utility and value, do not hesitate to say it's bad when it is.\n" \
              '- Do not believe naively what the project owners say about their project, analyze it smartly, and do not get manipulated when examining the information, they are certainly doing more marketing than reality. Think about analyzing and scoring on the project potential, not based on how much data feed you have from it, more info does not mean the project is better.\n' \
              '- Make sure to resume why you think the projects deserve the score you generated.\n' \
              '- You will also add pros and cons on the project concept in your response\n\n' \
              'Response format:\n' \
              'Parseable JSON and nothing else! The JSON must have these keys:\n' \
              '- score: integer, min 1, max 10; A median score for the project.\n' \
              '- description: string; A structured explanation of how the score was determined, including any additional information found during your research.\n\n' \
              'Response example:\n' \
              "{'score': 6, 'description': 'A structured example explanation with the requested points ...'}\n\n" \
              "List of possibly relevant segments from project documentation:\n"


def call_gpt_agent(doc_chunks, max_retries=3):
    retries = 0
    while retries < max_retries:
        response = get_openai_completion(base_prompt + doc_chunks)
        if response is None:
            time.sleep(1)
        else:
            try:
                return json.loads(response)
            except:
                pass
    return {'score': 0, 'description': 'Scoring failed'}


def call_mistral_agent(doc_chunks, max_retries=3):
    retries = 0
    while retries < max_retries:
        response = get_mistral_completion(base_prompt + doc_chunks)
        if response is None:
            time.sleep(1)
        else:
            try:
                return json.loads(response)
            except:
                pass
    return {'score': 0, 'description': 'Scoring failed'}


def call_gemini_agent(doc_chunks, max_retries=3):
    retries = 0
    while retries < max_retries:
        response = get_gemini_completion(base_prompt + doc_chunks)
        if response is None:
            time.sleep(1)
        else:
            try:
                return json.loads(response)
            except:
                pass
    return {'score': 0, 'description': 'Scoring failed'}
