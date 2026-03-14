from llm_service import english_to_asl_gloss_intent

tests = [
    # "Who cheated in AC?",
    # "What is AC?",
    # "Good morning",
    # "I like coffee",
    # "Where did you go?",
    # "They cheated",
    # "Who are you",
    # "AC is broken",
    "Can you help me with my homework?",
    "The cat sat on the mat.",
    "Why is the sky blue?",
    "I am going to the store.",
]

for t in tests:
    try:
        out = english_to_asl_gloss_intent(t)
        print(f"INPUT : {t}")
        print(f"OUTPUT: {out}")
        print("-" * 40)
    except Exception as e:
        print(f"INPUT : {t}")
        print(f"ERROR : {e}")
        print("-" * 40)
