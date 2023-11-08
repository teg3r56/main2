import streamlit as st
import openai
import os
import ast
import random

# Ensure the OPENAI_API_KEY environment variable is set in your operating system or environment
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to parse questions from the content
def parse_questions(content):
    valid_questions = []
    lines = content.split('\n')
    for line in lines:
        try:
            question = ast.literal_eval(line.strip(','))
            if isinstance(question, tuple) and len(question) == 4:
                valid_questions.append(question)
        except SyntaxError as e:
            st.error(f"Syntax error parsing line: {line}. Error: {e}")
        except Exception as e:
            st.error(f"Error parsing line: {line}. Error: {e}")
    return valid_questions

# Function to generate questions from a given topic using OpenAI API
def generate_questions_from_topic(topic):
    try:
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "..."
                },
                {
                    "role": "user",
                    "content": f"Create questions about {topic}..."
                }
            ]
        )

        content = chat_completion.choices[0].message["content"].strip()

        if not content.startswith("[") or not content.endswith("]"):
            content = "[" + content.replace("]\n\n[", ", ") + "]"

        questions = parse_questions(content)

        if questions:
            random.shuffle(questions)
            return questions
        else:
            st.error("Could not parse the API response into quiz questions.")
            return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

# Streamlit Sidebar for input
st.sidebar.title("Quiz Generator")
topic = st.sidebar.text_input("Enter the topic you want to create a quiz about:")
generate_quiz = st.sidebar.button("Generate Quiz")

# Main app logic
if 'questions' not in st.session_state:
    st.session_state.questions = []
    st.session_state.current_question_index = 0

if generate_quiz and topic:
    st.session_state.questions = generate_questions_from_topic(topic)
    st.session_state.current_question_index = 0

if st.session_state.questions:
    question_tuple = st.session_state.questions[st.session_state.current_question_index]
    question, options, correct_answer_index, explanation = question_tuple
    st.write(question)
    option = st.radio("Choices", options)

    if st.button("Submit Answer"):
        if options.index(option) == correct_answer_index:
            st.success("Correct!")
        else:
            st.error(f"Incorrect! {explanation}")
        if st.session_state.current_question_index < len(st.session_state.questions) - 1:
            st.session_state.current_question_index += 1
        else:
            st.balloons()
            st.session_state.questions = []
            st.session_state.current_question_index = 0
            st.write("Quiz Finished! Start again?")
