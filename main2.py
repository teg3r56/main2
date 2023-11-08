import streamlit as st
import openai
import os
import ast
import random
from openai import OpenAI

# Initialize the OpenAI client with your API key
client = OpenAI(api_key=("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"))

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
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Generate a list of multiple-choice questions with answers and explanations. The output should be in the form of a Python list, with each question represented as a tuple. Each tuple should contain the question text, a list of options, the index of the correct option, and an explanation. There should only be one pair of brackets surrounding the entire list, and no additional brackets around individual tuples."
                    },
                {
                    "role": "user", 
                    "content": "Create as many needed multiple-choice questions about {topic}. "
                                                "In this exact format, only one pair of brackets surrounding all questions: "
                                                "[('question', ['options', 'options', 'options'], correct_option_index, 'explanation')] "
                                                "Example: ["
                                                "('How many valence electrons do elements in the Alkali metal family have?', "
                                                "['1', '2', '3'], 0, 'Alkali metals belong to Group 1A and have 1 valence electron.'),"
                                                "('What is the common oxidation state of Alkali metals?', ['+1', '+2', '0'], 0, "
                                                "'Alkali metals have an oxidation state of +1 as they tend to lose one electron.')]"
                     }
            ]
        )

        content = response.choices[0].message.content.strip()

        # Concatenate content if it's split into multiple lists
        if not content.startswith("[") or not content.endswith("]"):
            content = "[" + content.replace("]\n\n[", ", ") + "]"

        # Parse the content into a list of questions
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
    
if 'questions' not in st.session_state:
    st.session_state.questions = []

def generate_and_store_questions(topic):
    questions = generate_questions_from_topic(topic)
    if questions:
        st.session_state.questions = questions
        st.session_state.current_question_index = 0

# Streamlit Sidebar for input
st.sidebar.title("Quiz Generator")
topic = st.sidebar.text_input("Enter the topic you want to create a quiz about:")
generate_quiz = st.sidebar.button("Generate Quiz", on_click=generate_and_store_questions, args=(topic,))

# Main app logic
if 'questions' in st.session_state and st.session_state.questions:
    question_tuple = st.session_state.questions[st.session_state.current_question_index]
    question, options, correct_answer_index, explanation = question_tuple
    st.write(question)
    option = st.radio("Choices", options)

    if st.button("Submit Answer"):
        if options.index(option) == correct_answer_index:
            st.success("Correct!")
            if st.session_state.current_question_index < len(st.session_state.questions) - 1:
                st.session_state.current_question_index += 1
            else:
                st.balloons()
                st.session_state.questions = []
                st.session_state.current_question_index = 0
                st.write("Quiz Finished! Start again?")
        else:
            st.error(f"Incorrect! {explanation}")
