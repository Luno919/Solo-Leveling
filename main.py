APIKEY="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"
import requests
import json
import re

# Input prompt


# Updated parsing function
def parse_challenge_text(raw_text):
    title_match = re.search(r'<Title>\s*\**(.*?)\**\s*</Title>', raw_text, re.DOTALL)
    desc_match = re.search(r'<Description>\s*(.*?)\s*</Description>', raw_text, re.DOTALL)
    time_match = re.search(r'<Time_Limit>\s*(.*?)\s*</Time_Limit>', raw_text, re.DOTALL)
    tip_match = re.search(r'<Tip>\s*(.*?)\s*</Tip>', raw_text, re.DOTALL)

    title = title_match.group(1).strip() if title_match else None
    description = desc_match.group(1).strip() if desc_match else None
    time_limit = time_match.group(1).strip() if time_match else None
    tip = tip_match.group(1).strip() if tip_match else None

    # Remove bold ** formatting
    clean = lambda s: re.sub(r'\*\*', '', s) if s else None

    return {
        'title': clean(title),
        'description': clean(description),
        'time_limit': clean(time_limit),
        'tip': clean(tip)
    }
def dynamic_quest(quests="",skills="good communication, good listening , daring"):
    query = f'''
I want to Learn skills {skills} give me a challenge  in the format  
and  there is no person  interact but i can use the Ai tools give Challenge only for today and a single task only  only one challenge
and those challenge should improve me scientifically 
<challenge>
<Title> </Title>
<Description>   </Description> 
<Time_Limit>  </Time_Limit>
<Tip>  </Tip>
</challenge>

this are my previous challenges  {quests}

so don't give the same style again
'''
    # Request to OpenRouter
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {APIKEY}",  # ← Replace with your real API key
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "deepseek/deepseek-r1:free",
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ]
        })
    )
    # Handle the response
    if response.status_code == 200:
        result = response.json()
        message = result['choices'][0]['message']['content']

        # Remove <challenge> wrapper tags
        message = message.replace('<challenge>', '').replace('</challenge>', '').strip()

        print("Raw Challenge Text:\n", message)
        print("\nParsed Challenge Fields:")
        return(parse_challenge_text(message))

    else:
        print("Error:", response.status_code, response.text)


# print(dynamic_quest())