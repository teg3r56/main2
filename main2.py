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

def generate_flashcards_from_topic(topic, number_of_flashcards):
    my_bar = st.progress(0)
    for percent_complete in range(100):
        time.sleep(calculate_delay(percent_complete, number_of_flashcards))
        my_bar.progress(percent_complete + 1)

    with st.spinner('Creating your flashcards...'):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                temperature=0.5,
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

def generate_questions_from_topic(topic, number_of_questions):
    my_bar = st.progress(0)
    for percent_complete in range(100):
        time.sleep(calculate_delay(percent_complete, number_of_questions))
        my_bar.progress(percent_complete + 1)

    with st.spinner('Formatting your quiz...'):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                temperature=0.1,
                messages=[
                    {
                        "role": "system",
                        "content": f"Generate a list of multiple-choice questions with answers and explanations on the topic of {topic}. Please provide exactly {number_of_questions} questions. Format the output as a Python list, with each question as a tuple containing the question text, a list of options, the index of the correct option, and an explanation. Surround the entire list with one pair of brackets, without extra brackets around individual tuples."
                    },
                    {
                        "role": "user", 
                        "content": f"Create multiple-choice questions about {topic} with exactly {number_of_questions} questions. The output should be formatted as:"
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
                content = "[" + content + "]"

            questions = parse_questions(content)
            if questions:
                random.shuffle(questions)
                st.session_state.questions = questions
                st.session_state.current_question_index = 0
                st.session_state.correct_answers = 0
                st.session_state.display_quiz = True
                return True
            else:
                st.error("Could not parse the API response into quiz questions.")
                return False
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            return False

# Initialize state variables
if 'questions' not in st.session_state:
    st.session_state.questions = []
    st.session_state.correct_answers = 0
    st.session_state.current_question_index = 0
    st.session_state.show_next = False

if 'quiz_history' not in st.session_state:
    st.session_state.quiz_history = []
    
def initialize_state_variables():
    if 'generation_started' not in st.session_state:
        st.session_state['generation_started'] = False
    if 'number_of_questions' not in st.session_state:
        st.session_state['number_of_questions'] = 5
    if 'let_quizon_decide' not in st.session_state:
        st.session_state['let_quizon_decide'] = False
    if 'display_quiz' not in st.session_state:
        st.session_state['display_quiz'] = False
    if 'display_flashcards' not in st.session_state:
        st.session_state['display_flashcards'] = False
    if 'quiz_or_flashcard' not in st.session_state:
        st.session_state['quiz_or_flashcard'] = None
    if 'answer_submitted' not in st.session_state:
        st.session_state['answer_submitted'] = False
        
# Main screen function
def main_screen():
    initialize_state_variables()

    st.markdown("""
    <style>
    div.stButton > button:first-child {
        width: 100%;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <style>
    .checkbox-style {
        position: relative;
        left: 20px; /* Adjust as necessary */
        top: 50px;
    }
    </style>""", unsafe_allow_html=True)
    
    st.title("Teague Coughlin Study Tool")
    topic = st.text_input("Enter the topic or notes you want to study:")
    col1, col2, col3 = st.columns([2, 3, 3])

    with col1:
        generate_quiz = st.button("Generate Quiz")
        
    with col2:
        number_of_questions = st.slider("", 1, 40, 5, key='num_questions')

    with col3:
        st.checkbox("Let QuizOn Decide", key='let_quizon_decide', css_class='checkbox-style')
        st.caption("Adjust the number of questions for the quiz")
        
    if st.session_state.get('quiz_or_flashcard'):
        col3, col4 = st.columns([1, 3])
        with col3:
            st.session_state.let_quizon_decide = st.checkbox("Let QuizOn Decide", key='quiz_decide_checkbox')
        with col4:
            st.session_state.number_of_questions = st.number_input("Number of Questions", min_value=1, max_value=40, value=5, key='num_questions_input', disabled=st.session_state.let_quizon_decide)

        if st.button("Generate", key='generate_button'):
            topic = capitalize_topic(topic)
            number_of_items = "As many as needed" if st.session_state.let_quizon_decide else st.session_state.number_of_questions
            handle_generation(topic, st.session_state.quiz_or_flashcard == "quiz", number_of_items)

    if st.session_state.get('display_quiz', False):
        display_current_question()

    elif st.session_state.get('display_flashcards', False):
        display_flashcards()
        
    if st.session_state.generation_started:
        if st.session_state.quiz_or_flashcard == "quiz":
            display_current_question()
        elif st.session_state.quiz_or_flashcard == "flashcard":
            display_flashcards()
        st.session_state.generation_started = False

    if st.session_state.quiz_or_flashcard and topic and st.button("Generate"):
        handle_generation(topic, st.session_state.quiz_or_flashcard == "quiz")
        st.session_state.ready_to_generate = False
        st.session_state.quiz_or_flashcard = None
        st.experimental_rerun()

# Handle generation function
def handle_generation(topic, generate_quiz, number_of_items):
    if generate_quiz:
        quiz_generated = generate_questions_from_topic(topic, number_of_items)
        if not quiz_generated:
            st.error("Failed to generate quiz.")
            return False
    else:
        flashcards_generated = generate_flashcards_from_topic(topic, number_of_items)
        if not flashcards_generated:
            st.error("Failed to generate flashcards.")
            return False

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
            
def display_current_question():
    question_tuple = st.session_state.questions[st.session_state.current_question_index]
    question, options, correct_answer_index, explanation = question_tuple
    st.write(question)
    
    disabled = st.session_state.answer_submitted
    
    if not disabled:
        option = st.radio("Choose the correct answer:", options, key=f"option{st.session_state.current_question_index}")
        submit_placeholder = st.empty()

        if submit_placeholder.button("Submit Answer"):
            check_answer(option, options, correct_answer_index, explanation)
            submit_placeholder.empty()

    if st.session_state.show_next:
        button_label = "Review" if st.session_state.current_question_index == len(st.session_state.questions) - 1 else "Next Question"
        if next_placeholder.button(button_label):
            next_question()

def next_question():
    if st.session_state.current_question_index < len(st.session_state.questions) - 1:
        st.session_state.current_question_index += 1
        st.session_state.show_next = False
        st.session_state.answer_submitted = False
        st.experimental_rerun()
    else:
        handle_quiz_end()

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
        
# global grade color
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
        letter_grade = get_letter_grade(correct_answers, total_questions)
        grade_color_style = f"color: {grade_color[letter_grade]};"
        score = f"{correct_answers} out of {total_questions}"

        # Display current score and grade
        st.markdown(f"Quiz Finished! You got {score} correct. An <span style='{grade_color_style}'>{letter_grade}</span>", unsafe_allow_html=True)

        # Check if there is a previous score
        topic = st.session_state.topic
        existing_quiz = next((quiz for quiz in st.session_state.quiz_history if quiz['topic'] == topic), None)
        if existing_quiz and 'last_score' in existing_quiz:
            last_score, last_grade = existing_quiz['last_score']
            last_grade_color_style = f"color: {grade_color[last_grade]};"
            st.markdown(f"Your previous score was {last_score}. <span style='{last_grade_color_style}'>{last_grade}</span>", unsafe_allow_html=True)

        # Update the last score for the current topic
        if existing_quiz:
            existing_quiz['last_score'] = (score, letter_grade)
        else:
            st.session_state.quiz_history.append({
                'topic': topic,
                'questions': st.session_state.questions,
                'last_score': (score, letter_grade)
            })

        st.session_state.show_next = True

    if end_placeholder.button("Restart Quiz"):
        # Shuffle questions here before restarting
        st.session_state.questions = random.sample(st.session_state.questions, len(st.session_state.questions))
        st.session_state.current_question_index = 0
        st.session_state.correct_answers = 0
        st.session_state.show_next = False
        st.session_state.answer_submitted = False
        st.experimental_rerun()

        
def calculate_delay(percent_complete, number_of_items):
    base_time = 0.02  # base time for 1 item
    incremental_time = 0.025  # additional time per item

    if isinstance(number_of_items, str) and number_of_items == "As many as needed":
        number_of_items = 10  

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
