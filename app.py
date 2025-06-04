import streamlit as st
from syllabus import MATHEMATICS, PHYSICS, CHEMISTRY
import json
from groq import Groq

st.title("MCQ Generator (IITJEE Level)")

# 0. API Key
api_key = st.text_input("Enter your Groq API Key", type="password", disabled=st.session_state.get("show_quiz", False))

# 1. Subject selection
disable_inputs = st.session_state.get("show_quiz", False)
subject = st.selectbox("Select Subject", ("Mathematics", "Physics", "Chemistry"), disabled=disable_inputs)

# 2. Topic selection
topic_dict = {"Mathematics": MATHEMATICS, "Physics": PHYSICS, "Chemistry": CHEMISTRY}
topics = list(topic_dict[subject].keys())
topic = st.selectbox("Select Topic", topics, disabled=disable_inputs)

# 3. Number of questions
num_questions = st.number_input("How many questions?", min_value=1, max_value=20, value=5, disabled=disable_inputs)

# 4. Difficulty level
difficulty = st.selectbox("Select Difficulty", ("Easy", "Medium", "Hard"), disabled=disable_inputs)

# Button to generate questions
if st.button("Generate MCQs", disabled=disable_inputs):
    if not api_key:
        st.error("Please enter your API key.")
    else:
        with st.spinner("Generating questions..."):
            # Build the expert instruction and prompt
            task = "IITJEE MCQ creator"
            full_prompt = f"""
                        You are an expert IITJEE MCQ creator. Generate {num_questions} MCQ questions for the topic '{topic}' from {subject} for class 11/12. The questions should be of '{difficulty}' level and strictly IITJEE standard. 

                        Output a JSON list, each item with these keys: question, option1, option2, option3, option4, hints, correct_answer. 

                        Example:
                        [
                        {{
                            "question": "...",
                            "option1": "...",
                            "option2": "...",
                            "option3": "...",
                            "option4": "...",
                            "solution": "...",
                            "hints": "...",
                            "correct_answer": "option2"
                        }}, ...
                        ]
                        """
            model = "llama3-8b-8192"
            client = Groq(api_key=api_key)
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": full_prompt}],
                    temperature=1,
                    max_completion_tokens=512,
                    top_p=1,
                    stream=True,
                    stop=None,
                )
                # Collect the streamed response
                content = ""
                for chunk in completion:
                    if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
                # Sometimes the model returns code block, strip it
                if content.strip().startswith("```"):
                    content = content.strip().split("\n",1)[1].rsplit("\n",1)[0]
                mcqs = json.loads(content)
                st.session_state["mcqs"] = mcqs
                st.session_state["show_quiz"] = True
                st.session_state["finished"] = False
            except Exception as e:
                st.error(f"Error parsing MCQ JSON: {e}")
                st.code(content if 'content' in locals() else str(e))

# Quiz UI
if st.session_state.get("show_quiz"):
    st.header("MCQ Quiz")
    answers = []
    for idx, q in enumerate(st.session_state["mcqs"]):
        st.subheader(f"Q{idx+1}: {q['question']}")
        ans = st.radio(
            f"Select your answer for Q{idx+1}",
            ("option1", "option2", "option3", "option4"),
            format_func=lambda x: q[x],
            key=f"ans_{idx}",
            disabled=st.session_state.get("finished", False)
        )
        answers.append(ans)
    if not st.session_state.get("finished", False):
        if st.button("Finish"):
            st.session_state["finished"] = True
            score = 0
            for idx, q in enumerate(st.session_state["mcqs"]):
                correct = q["correct_answer"]
                user_ans = st.session_state.get(f"ans_{idx}")
                if user_ans == correct:
                    score += 1
            st.session_state["score"] = score
    else:
        st.header("Results")
        score = st.session_state.get("score", 0)
        st.subheader(f"Your Score: {score} / {len(st.session_state['mcqs'])}") 
