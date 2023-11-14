import streamlit as st
import openai
import ast
import random
import time
import math
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPEN_API_KEY"])

def calculate_delay(percent_complete, number_of_items):
    
    base_time = 0.02  
    incremental_time = 0.025  

    time_delay = base_time + ((number_of_items - 1) * incremental_time)

    if percent_complete > 50:
        time_delay *= (1 + (percent_complete - 50) / 50)
    if percent_complete > 85:
        time_delay *= (1 + (percent_complete - 85) / 15)
    if percent_complete > 95:
        time_delay *= (1 + (percent_complete - 95) / 5)
    if percent_complete > 99:
        time_delay *= (1 + (percent_complete - 99))

    return time_delay

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
        
def generate_flashcards_from_topic(topic, number_of_flashcards):
    with st.spinner('Creating your flashcards...'):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                temperature=0.1,
                messages=[
                    {
                        "role": "system",
                        "content": f"Generate a list of key concepts and definitions about {topic}. Please provide exactly {number_of_flashcards} flashcards. Format the output as a Python list, with each flashcard as a tuple containing the concept and its definition."
                    },
                    {
                        "role": "user", 
                        "content": f"Create flashcards for key concepts about {topic} with exactly {number_of_flashcards} flashcards. Format the output as: [('concept', 'definition'), ...]"
                    }
                ]
            )

            content = response.choices[0].message.content.strip()
            flashcards = parse_flashcards(content)

            if flashcards:
                st.session_state.flashcards = flashcards
                st.session_state.current_flashcard_index = 0
                return True
            else:
                st.error("Could not parse the API response into flashcards.")
                return False
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            return False

def parse_flashcards(content):
    try:
        valid_flashcards = ast.literal_eval(content)
        if isinstance(valid_flashcards, list) and all(isinstance(flashcard, tuple) and len(flashcard) == 2 for flashcard in valid_flashcards):
            return valid_flashcards
        else:
            st.error("The API response is not in the expected format of a list of tuples.")
            return None
    except SyntaxError as e:
        st.error(f"Syntax error while parsing content: {e}")
        return None
    except Exception as e:
        st.error(f"Error while parsing content: {e}")
        return None

def update_progress_bar():
    progress = 0
    max_delay = 0.25  # maximum delay at 90% progress
    while progress < 90:
        delay_factor = (progress / 90) ** 2  # exponential growth factor
        sleep_time = max_delay * delay_factor
        time.sleep(sleep_time)
        progress += 1
        st.session_state.progress_bar.progress(progress)

def generate_questions_from_topic(topic, number_of_items):

    if 'progress_bar' not in st.session_state:
            st.session_state.progress_bar = st.progress(0)

    update_progress_bar()

    try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                temperature=0.1,
                messages=[
                    {
                        "role": "system",
                        "content": f"Generate a list of multiple-choice questions with answers and explanations on the topic of {topic}. Please provide exactly {number_of_items} questions. Format the output as a Python list, with each question as a tuple containing the question text, a list of options, the index of the correct option, and an explanation. Surround the entire list with one pair of brackets, without extra brackets around individual tuples."
                    },
                    {
                        "role": "user", 
                        "content": f"Create multiple-choice questions about {topic} with exactly {number_of_items} questions. The output should be formatted as:"
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

            with st.spinner('Formatting your quiz...'):
                if questions:
                    random.shuffle(questions)
                    st.session_state.questions = questions
                    st.session_state.current_question_index = 0
                    st.session_state.correct_answers = 0
                    st.session_state.display_quiz = True
                    quiz_ready = True 
                    if quiz_ready:
                        st.session_state.progress_bar.progress(100)
                    return True
                else:
                    st.error("Could not parse the API response into quiz questions.")
                    return False
    except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            return False
    finally:
        st.session_state.progress_bar.empty()


if 'questions' not in st.session_state:
    st.session_state.questions = []
    st.session_state.correct_answers = 0
    st.session_state.current_question_index = 0
    st.session_state.show_next = False

if 'quiz_history' not in st.session_state:
    st.session_state.quiz_history = []

def main_screen():
    if 'choice' not in st.session_state:
        st.session_state.choice = None
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    if 'review_ready' not in st.session_state:
        st.session_state.review_ready = False
    if 'generate_pressed' not in st.session_state:
        st.session_state.generate_pressed = False
    if 'last_answer_was_correct' not in st.session_state:
        st.session_state.last_answer_was_correct = None
    if 'last_explanation' not in st.session_state:
        st.session_state.last_explanation = ''
    if 'progress_bar_placeholder' not in st.session_state:
        st.session_state.progress_bar_placeholder = st.empty()
    if 'quiz_history' not in st.session_state:
        st.session_state.quiz_history = []
    if 'show_next' not in st.session_state:
        st.session_state.show_next = False
    if 'answer_submitted' not in st.session_state:
        st.session_state.answer_submitted = False
    if 'quiz_generated' not in st.session_state:
        st.session_state.quiz_generated = False
    if 'quiz_or_flashcard' not in st.session_state:
        st.session_state.quiz_or_flashcard = None

    st.title("Teague Coughlin Study Tool")
    
    topic = st.text_input("Enter the topic or notes you want to study:")

    st.markdown("""
    <style>
    div.stButton > button:first-child {
        width: 100%;
    }
    </style>""", unsafe_allow_html=True)

    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False

    if 'review_ready' not in st.session_state:
        st.session_state.review_ready = False

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate a Quiz"):
            st.session_state.choice = "quiz"
            st.session_state.generate_pressed = False
    with col2:
        if st.button("Generate Flashcards"):
            st.session_state.choice = "flashcard"
            st.session_state.generate_pressed = False

    # Show the number of questions and generate button only if quiz not started and no choice has been made yet
    if st.session_state.choice and not st.session_state.quiz_started and not st.session_state.generate_pressed:
        number_of_questions = st.number_input("Number of Questions", min_value=1, max_value=40, value=5, key='number_of_questions')
        if st.button("Generate"):
            st.session_state.generate_pressed = True
            if st.session_state.choice == "quiz":
                generate_questions_from_topic(topic, number_of_questions)
            elif st.session_state.choice == "flashcard":
                generate_flashcards_from_topic(topic, number_of_questions)

    if st.session_state.get('display_quiz', False):
        display_current_question()

    if st.session_state.get('show_results', False):
        display_results()
    
    if 'restart_quiz' in st.session_state and st.session_state.restart_quiz:
        st.session_state.quiz_started = False
        st.session_state.choice = None

def generate_quiz_or_flashcards(topic, number_of_items):
    if st.session_state.choice == "quiz":
        quiz_generated = generate_questions_from_topic(topic, number_of_items)
    elif st.session_state.choice == "flashcard":
        flashcards_generated = generate_flashcards_from_topic(topic, number_of_items)

    st.experimental_rerun()

def display_flashcards():
    if 'flashcards' in st.session_state and st.session_state.flashcards:
        current_flashcard = st.session_state.flashcards[st.session_state.current_flashcard_index]
        concept, definition = current_flashcard

        if st.button(concept, key=f"flashcard{st.session_state.current_flashcard_index}"):
            st.info(definition)

        if st.button("Next", key="next_flashcard"):
            if st.session_state.current_flashcard_index < len(st.session_state.flashcards) - 1:
                st.session_state.current_flashcard_index += 1
            else:
                st.session_state.current_flashcard_index = 0
            st.experimental_rerun()

def check_answer(option, options, correct_answer_index, explanation):
    if options.index(option) == correct_answer_index:
        st.session_state.correct_answers += 1
        st.session_state.last_answer_was_correct = True
    else:
        st.session_state.last_answer_was_correct = False
    
    st.session_state.last_explanation = explanation
    st.session_state.answer_submitted = True

def display_current_question():
    if st.session_state.get('display_quiz', False) and st.session_state.questions:
        question_tuple = st.session_state.questions[st.session_state.current_question_index]
        question, options, correct_answer_index, explanation = question_tuple
        
        # display question
        st.write(question)

        selected_option = st.radio("Choose the correct answer:", options, key=f"option{st.session_state.current_question_index}")

        if not st.session_state.get('answer_submitted', False):
            if st.button("Submit Answer"):
                check_answer(selected_option, options, correct_answer_index, explanation)

                # if its rhe last question, prepare review button
                if st.session_state.current_question_index == len(st.session_state.questions) - 1:
                    st.session_state.review_ready = True
                    st.session_state.generate_pressed = False  
                st.experimental_rerun()
        else:
            if st.session_state.last_answer_was_correct:
                st.success("Correct!")
            else:
                st.error("Incorrect!")
            st.info(explanation)

            if st.session_state.get('review_ready', False):
                if st.button("Review"):
                    handle_quiz_end()
            elif st.button("Next Question", key="next_question"):
                next_question()

def display_results():
    if st.session_state.show_results:
        correct_answers = st.session_state.correct_answers
        total_questions = len(st.session_state.questions)
        letter_grade = get_letter_grade(correct_answers, total_questions)
        grade_color_style = f"color: {grade_color[letter_grade]};"
        score = f"{correct_answers} out of {total_questions}"

        if not st.session_state.get('results_displayed', False):
            st.balloons()
            st.session_state.results_displayed = True

        st.markdown(f"Quiz Finished! You got {score} correct. Your grade: <span style='{grade_color_style}'>{letter_grade}</span>", unsafe_allow_html=True)

        if st.button("Restart Quiz"):
            restart_quiz()

def restart_quiz():
    st.session_state.show_results = False
    st.session_state.quiz_started = False

    # reset the quiz state
    st.session_state.questions = random.sample(st.session_state.questions, len(st.session_state.questions))
    st.session_state.current_question_index = 0
    st.session_state.correct_answers = 0
    st.session_state.show_next = False
    st.session_state.answer_submitted = False
    st.session_state.display_quiz = True
    
    st.session_state.generate_pressed = False

    st.session_state.last_answer_was_correct = None
    st.session_state.last_explanation = ''
    
    st.experimental_rerun()

def next_question():
    if st.session_state.current_question_index < len(st.session_state.questions) - 1:
        st.session_state.current_question_index += 1
        st.session_state.show_next = False
        st.session_state.answer_submitted = False
        st.experimental_rerun()
    else:
        handle_quiz_end()

def check_answer(selected_option, options, correct_answer_index, explanation):
    if options.index(selected_option) == correct_answer_index:
        st.session_state.correct_answers += 1
        st.session_state.last_answer_was_correct = True
    else:
        st.session_state.last_answer_was_correct = False
    st.session_state.last_explanation = explanation
    
    st.session_state.answer_submitted = True

def capitalize_topic(topic):
    words = topic.split()
    capitalized_words = [word if word[0].isupper() else word.capitalize() for word in words]
    return ' '.join(capitalized_words)
    
def get_letter_grade(correct, total):
    if total == 0: return 'N/A'  # division by zero 
    percentage = (correct / total) * 100
    if percentage >= 90: return 'A'
    elif percentage >= 80: return 'B'
    elif percentage >= 70: return 'C'
    elif percentage >= 60: return 'D'
    else: return 'F'
        
# color dictionary
grade_color = {
    'A': '#4CAF50',  # Green
    'B': '#90EE90',  # Light Green
    'C': '#FFC107',  # Amber
    'D': '#FF9800',  # Orange
    'F': '#F44336',  # Red
}

def handle_quiz_end():
    st.session_state.quiz_started = False
    st.session_state.display_quiz = False  
    st.session_state.show_results = True

    if 'submit_placeholder' in st.session_state:
        st.session_state.submit_placeholder.empty()
    if 'next_placeholder' in st.session_state:
        st.session_state.next_placeholder.empty()
    if 'explanation_placeholder' in st.session_state:
        st.session_state.explanation_placeholder.empty()

    st.experimental_rerun()

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
