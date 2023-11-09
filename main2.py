import matplotlib.pyplot as plt
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
    generate_quiz = st.button("Generate Quiz")
    console = st.empty()

    if generate_quiz and topic:
        st.session_state.topic = topic  
        with st.empty():
            for percent_complete in range(101):
                # loading bar logic
                time_delay = calculate_delay(percent_complete)
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
        if st.session_state.current_question_index < len(st.session_state.questions):
            display_current_question()
        else:
            handle_quiz_end()
            
def display_grade_history_with_graph(current_quiz):
    grade_history_container = st.expander("Grade History and Graph", expanded=True)
    with grade_history_container:
        if current_quiz:
            scores = current_quiz.get('scores', [])
            if scores:
                score_values = [int(score.split()[0]) for score, _ in scores]
                grades = [grade for _, grade in scores]

                fig, ax = plt.subplots()
                ax.plot(score_values, 'o-')
                ax.set_title('Score Over Time')
                ax.set_xlabel('Attempt')
                ax.set_ylabel('Score')
                ax.set_xticks(range(len(scores)))
                ax.set_xticklabels(range(1, len(scores) + 1))
                st.pyplot(fig)

                for score, grade in scores:
                    grade_color = {
                        'A': '#4CAF50',  # Green
                        'B': '#90EE90',  # Light Green
                        'C': '#FFC107',  # Amber
                        'D': '#FF9800',  # Orange
                        'F': '#F44336',  # Red
                    }.get(grade, '#9E9E9E')  # Grey for undefined grades

                    st.markdown(
                        f"<span style='color: {grade_color};'>{grade}</span> ({score})",
                        unsafe_allow_html=True
                    )
                
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
        
def handle_quiz_end():
    end_placeholder = st.empty()
    if not st.session_state.show_next:
        st.balloons()
        correct_answers = st.session_state.correct_answers
        total_questions = len(st.session_state.questions)
        score = f"{correct_answers} out of {total_questions}"
        letter_grade = get_letter_grade(correct_answers, total_questions)
        
        capitalized_topic = capitalize_topic(st.session_state.topic)
        existing_entry = next((entry for entry in st.session_state.quiz_history if entry['topic'] == capitalized_topic), None)

        if existing_entry:
            display_grade_history_with_graph(existing_entry)  

            if 'scores' not in existing_entry:
                existing_entry['scores'] = []
            existing_entry['scores'].append((score, letter_grade))
        else:
            new_entry = {
                'topic': capitalized_topic,
                'scores': [(score, letter_grade)],
                'questions': st.session_state.questions
            }
            st.session_state.quiz_history.append(new_entry)
            display_grade_history_with_graph(new_entry)  

        st.write(f"Quiz Finished! You got {score} correct. Your grade: {letter_grade}.")
        st.session_state.show_next = True

    if end_placeholder.button("Restart Quiz"):
        restart_quiz()
        end_placeholder.empty()

# restart quiz
def restart_quiz():
    new_questions = st.session_state.questions.copy()
    random.shuffle(new_questions)
    st.session_state.questions = new_questions
    st.session_state.correct_answers = 0
    st.session_state.current_question_index = 0
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
            display_grade_history_with_graph(quiz)
            st.experimental_rerun()
        
        scores = quiz.get('scores', [])  
        if len(scores) > 1:
            st.write(f"{topic_display} Grades:")
            for score, grade in scores:
                st.write(f"{grade} ({score})")

if __name__ == "__main__":
    main_screen()
