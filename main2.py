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

def generate_questions_from_topic(topic, number_of_questions):
    with st.spinner('Formatting your quiz...'):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"Generate a {number_of_questions} list of multiple-choice questions with answers and explanations. The output should be in the form of a Python list, with each question represented as a tuple. Each tuple should contain the question text, a list of options, the index of the correct option, and an explanation. There should only be one pair of brackets surrounding the entire list, and no additional brackets around individual tuples."
                    },
                    {
                        "role": "user", 
                        "content": f"Create {number_of_questions} multiple-choice questions about {topic}. "
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

if 'quiz_history' not in st.session_state:
    st.session_state.quiz_history = []
    
def main_screen():
    if 'quiz_history' not in st.session_state:
        st.session_state.quiz_history = []
        
    if 'show_next' not in st.session_state:
        st.session_state.show_next = False
        
    if 'answer_submitted' not in st.session_state:
        st.session_state.answer_submitted = False

    st.title("Teague Coughlin Quiz Generator")
    
    topic = st.text_input("Enter the topic you want to create a quiz about:")
    
    st.markdown(
            """
            <style>
                /* Target the slider's container div and adjust its position */
                .stSlider > div {
                    margin-top: -30px;  /* Adjust this value as needed */
                }
            </style>
            """,
            unsafe_allow_html=True,
    )
    
    # columns
    col1, col2 = st.columns([1, 4])

    with col1:
        generate_quiz = st.button("Generate Quiz")
        
    with col2:
        number_of_questions = st.slider("", 1, 20, 5, key='num_questions')

    console = st.empty()

    if generate_quiz and topic:
        st.session_state.topic = topic
        st.session_state.number_of_questions = number_of_questions
        with st.empty():
            for percent_complete in range(101):
                # loading bar logic
                time_delay = calculate_delay(percent_complete)
                progress = percent_complete / 100.0
                st.progress(progress)
                console.text(f"Loading... {percent_complete}%")
                time.sleep(time_delay)
        
        console.text("Finalizing...")
        quiz_generated = generate_questions_from_topic(topic, st.session_state.number_of_questions)  # Pass the number of questions
        if quiz_generated:
            st.progress(1.0)
            console.text("Quiz successfully generated. Starting quiz...")
            st.experimental_rerun()
        else:
            console.text("Failed to generate quiz. Please try again.")

    if 'questions' in st.session_state and st.session_state.questions:
        if st.session_state.current_question_index < len(st.session_state.questions):
            display_current_question()
        else:
            handle_quiz_end()
    else:
        st.write("Welcome! Enter a topic to generate a quiz.")
            
def display_current_question():
    question_tuple = st.session_state.questions[st.session_state.current_question_index]
    question, options, correct_answer_index, explanation = question_tuple
    st.write(question)
    option = st.radio("Choices", options, key=f"option{st.session_state.current_question_index}")

    # Use placeholders for buttons to manage their state
    submit_placeholder = st.empty()
    next_placeholder = st.empty()

    if not st.session_state.answer_submitted:
        if submit_placeholder.button("Submit Answer"):
            check_answer(option, options, correct_answer_index, explanation)
            submit_placeholder.empty()  # Clear the submit button after it's clicked

    # Check if we need to show the 'Next Question' button
    if st.session_state.show_next:
        if next_placeholder.button("Next Question"):
            next_question()

def next_question():
    st.session_state.current_question_index += 1
    st.session_state.show_next = False
    st.session_state.answer_submitted = False
    st.experimental_rerun()

def check_answer(option, options, correct_answer_index, explanation):
    if options.index(option) == correct_answer_index:
        st.session_state.correct_answers += 1
        st.success("Correct!")
    else:
        st.error(f"Incorrect! {explanation}")
    
    st.session_state.show_next = True
    st.session_state.answer_submitted = True

def capitalize_topic(topic):
    words = topic.split()
    capitalized_words = [word if word[0].isupper() else word.capitalize() for word in words]
    return ' '.join(capitalized_words)
    
def get_letter_grade(correct, total):
    if total == 0: return 'N/A'  # division by zero lol
    percentage = (correct / total) * 100
    if percentage >= 90: return 'A'
    elif percentage >= 80: return 'B'
    elif percentage >= 70: return 'C'
    elif percentage >= 60: return 'D'
    else: return 'F'
        
# Global grade color dictionary
grade_color = {
    'A': '#4CAF50',  # Green
    'B': '#90EE90',  # Light Green
    'C': '#FFC107',  # Amber
    'D': '#FF9800',  # Orange
    'F': '#F44336',  # Red
}

def handle_quiz_end():
    end_placeholder = st.empty()
    if not st.session_state.show_next:
        st.balloons()
        correct_answers = st.session_state.correct_answers
        total_questions = len(st.session_state.questions)
        score = f"{correct_answers} out of {total_questions}"

        st.markdown(f"Quiz Finished! You got {score} correct.", unsafe_allow_html=True)

        # save quiz results without grades
        capitalized_topic = capitalize_topic(st.session_state.topic)
        existing_quiz = next((quiz for quiz in st.session_state.quiz_history if quiz['topic'] == capitalized_topic), None)
        if not existing_quiz:
            st.session_state.quiz_history.append({
                'topic': capitalized_topic,
                'questions': st.session_state.questions
            })

        st.session_state.show_next = True

    if end_placeholder.button("Restart Quiz"):
        random.shuffle(st.session_state.questions)
        st.session_state.current_question_index = 0
        st.session_state.correct_answers = 0
        st.session_state.show_next = False
        st.session_state.answer_submitted = False
        st.experimental_rerun()

        
def calculate_delay(percent_complete):
    time_delay = 0.09  
    if percent_complete > 50:
        time_delay = 0.15 + (percent_complete - 50) * 0.02
    if percent_complete > 85:
        exponential_factor = (percent_complete - 85) / 15
        time_delay += (2 ** exponential_factor) / 100
    if percent_complete > 95:
        exponential_factor = (percent_complete - 95) / 5
        time_delay += 0.5 * (2 ** exponential_factor)
    if percent_complete > 99:
        exponential_factor = (percent_complete - 99) / 1
        time_delay += 2 * (2 ** exponential_factor)
    return time_delay

with st.sidebar:
    st.header("Quiz History")
    for index, quiz in enumerate(st.session_state.quiz_history):
        topic_display = quiz['topic']
        if st.button(f"Replay {topic_display} Quiz", key=f"replay_{index}"):
            st.session_state.questions = quiz['questions']
            st.session_state.correct_answers = 0
            st.session_state.current_question_index = 0
            st.session_state.show_next = False
            st.session_state.answer_submitted = False
            st.experimental_rerun()
        
        scores = quiz.get('scores', [])  
        if len(scores) > 1:
            st.write(f"{topic_display} Grades:")
            for score, grade in scores:
                st.write(f"{grade} ({score})")

if __name__ == "__main__":
    main_screen()
