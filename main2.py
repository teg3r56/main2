import streamlit as st
import openai
import ast
import random
import time
from openai import OpenAI

# Initialize the OpenAI client with your API key
client = OpenAI(api_key=st.secrets["OPEN_API_KEY"])

def parse_questions(content):
    try:
        valid_questions = ast.literal_eval(content)
        if isinstance(valid_questions, list) and all(isinstance(question, tuple) and len(question) == 4 for question in valid_questions):
            return valid_questions
        else:
            st.error("The API response is not in the expected format of a list of tuples.")
            return None
    except SyntaxError as e:
        st.error(f"Syntax error while parsing content: {e}")
        return None
    except Exception as e:
        st.error(f"Error while parsing content: {e}")
        return None

def generate_questions_from_topic(topic):
    with st.spinner('Formating your quiz...'):
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
                        "content": f"Create as many needed multiple-choice questions about {topic}. "
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

            if not content.startswith("[") or not content.endswith("]"):
                content = "[" + content.replace("]\n\n[", ", ") + "]"

            questions = parse_questions(content)

            if questions:
                random.shuffle(questions)
                st.session_state.questions = questions
                st.session_state.current_question_index = 0
                st.session_state.correct_answers = 0
                return True
            else:
                st.error("Could not parse the API response into quiz questions.")
                return False
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            return False

if 'questions' not in st.session_state:
    st.session_state.questions = []
    st.session_state.correct_answers = 0
    st.session_state.current_question_index = 0
    st.session_state.show_next = False

def main_screen():
    if 'show_next' not in st.session_state:
        st.session_state.show_next = False
    st.title("Teague Coughlin Quiz Generator")
    topic = st.text_input("Enter the topic you want to create a quiz about:")
    generate_quiz = st.button("Generate Quiz")
    console = st.empty()  # Placeholder for console messages

    if generate_quiz and topic:
        with st.empty():  # Placeholder for loading bar
            for percent_complete in range(101):
                time_delay = 0.07  # Base delay
                if percent_complete > 50:
                    time_delay = 0.1 + (percent_complete - 50) * 0.02
                if percent_complete > 85:
                    exponential_factor = (percent_complete - 85) / 15
                    time_delay += (2 ** exponential_factor) / 100  # Adjust the denominator for rate control
                
                progress = percent_complete / 100.0
                st.progress(progress)
                console.text(f"Loading... {percent_complete}%")
                time.sleep(time_delay)
        
        console.text("Finalizing...")
        quiz_generated = generate_questions_from_topic(topic)
        if quiz_generated:
            st.progress(1.0)
            console.text("Quiz successfully generated. Starting quiz...")
            st.experimental_rerun()
        else:
            console.text("Failed to generate quiz. Please try again.")

    if 'questions' in st.session_state and st.session_state.questions:
        if not st.session_state.show_next:
            # Display the current question and options
            question_tuple = st.session_state.questions[st.session_state.current_question_index]
            question, options, correct_answer_index, explanation = question_tuple
            st.write(question)
            option = st.radio("Choices", options, key=f"option{st.session_state.current_question_index}")
            submit_answer = st.button("Submit Answer")
    
            if submit_answer:
                if options.index(option) == correct_answer_index:
                    st.session_state.correct_answers += 1
                    st.success("Correct!")
                    time.sleep(0.5)  # Show success message for half a second
                else:
                    st.error(f"Incorrect! {explanation}")
                st.session_state.show_next = True  # Prepare to show the 'Next Question' button
    
        if st.session_state.show_next:
            # Display the 'Next Question' button
            if st.button("Next Question"):
                if st.session_state.current_question_index < len(st.session_state.questions) - 1:
                    st.session_state.current_question_index += 1
                    st.session_state.show_next = False  # Hide the 'Next Question' button
                else:
                    st.balloons()
                    st.write(f"Quiz Finished! You got {st.session_state.correct_answers} out of {len(st.session_state.questions)} correct.")
                    if st.button("Restart Quiz"):
                        st.session_state.questions = []
                        st.session_state.correct_answers = 0
                        st.session_state.current_question_index = 0
                        st.session_state.show_next = False
                        random.shuffle(st.session_state.questions)
                st.experimental_rerun()


if __name__ == "__main__":
    main_screen()
