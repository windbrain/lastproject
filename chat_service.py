def get_ai_response(client, messages, model="gpt-4o"):
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content
