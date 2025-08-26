import openai
import pandas as pd

# Load your CSV data
df = pd.read_csv("data/sample_companies.csv")

# Initialize OpenAI client (v1.0+)
client = openai.OpenAI(
    api_key=
)

# Loop through companies and generate outbound emails
for index, row in df.iterrows():
    company = row['Company Name']
    industry = row['Industry']
    job_title = row['Job Title']
    size = row['Company Size']
    location = row['Location']
    
    prompt = f"""
    You are a SaaS outbound expert. Generate a cold outbound email.

    Company: {company}
    Industry: {industry}
    Job Title: {job_title}
    Company Size: {size}
    Location: {location}

    Write:
    - Subject line (5-7 words, eye-catching)
    - First personalized sentence
    - 1-2 sentence body that drives curiosity
    - Call-to-action to book a call
    """

    response = client.chat.completions.create(
      model="gpt-4o",
      messages=[{"role": "user", "content": prompt}],
      temperature=0.7
    )

    print(f"--- Email for {company} ---")
    print(response.choices[0].message.content)
    print("\n\n")

