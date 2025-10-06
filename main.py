from ollama import chat


def prompt_to_schema(prompt):
    response = chat(
        model="llama3",
        messages=[
            {"role": "system", "content": "You are a data modeling expert."},
            {"role": "user", "content": f"Create a SQL schema for the following: {prompt}"}
        ]
    )
    return response['message']['content']

if __name__ == "__main__":
    print("💡 Enter your data modeling prompt below:")
    user_prompt = input("> ")

    try:
        schema = prompt_to_schema(user_prompt)
        print("\n✅ Generated Schema:\n")
        print(schema)
    except Exception as e:
        print(f"❌ Error: {e}")
