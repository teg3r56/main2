import tkinter as tk
from tkinter import ttk, messagebox
import random
import ast
import threading
import openai
import os

# Ensure the OPENAI_API_KEY environment variable is set in your operating system or environment
client = openai.OpenAI(api_key=os.getenv("OPEN_API_KEY"))


def parse_questions(content):
    valid_questions = []
    lines = content.split('\n')
    for line in lines:
        try:
            # Try to parse each line as a tuple
            question = ast.literal_eval(line.strip(','))
            if isinstance(question, tuple) and len(question) == 4:
                valid_questions.append(question)
        except SyntaxError as e:
            # If a line can't be parsed due to a syntax error, print an error message
            print(f"Syntax error parsing line: {line}. Error: {e}")
        except Exception as e:
            # If any other exception occurs, print an error message
            print(f"Error parsing line: {line}. Error: {e}")
    return valid_questions


class QuizApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Quiz App")
        self.master.geometry("800x600")
        self.master.configure(bg="#282a36")

        self.style = ttk.Style(self.master)
        self.style.configure("TLabel", background="#1c1c1c", foreground="#d9d9d9", font=("Futura", 20))
        self.style.configure("TButton", font=("Futura", 15), padding=12)
        self.style.configure("TRadiobutton", background="#1c1c1c", foreground="#d9d9d9", font=("Arial", 20))
        self.style.configure("TEntry", font=("Arial", 20), padding=10)

        self.intro_label = ttk.Label(self.master, text="Enter the topic you want to create a quiz about:", wraplength=800)  # Adjusted wraplength for larger label
        self.intro_label.pack(pady=15)

        self.topic_input = tk.Entry(self.master, width=45, font=("Arial", 15), bg="#333333", fg="#d9d9d9", insertbackground="white")
        self.topic_input.pack(pady=15)

        self.submit_button = ttk.Button(self.master, text="Generate Quiz", command=self.generate_quiz)
        self.submit_button.pack(pady=15)

        self.questions = []
        self.current_question_index = 0
        self.choices = tk.StringVar()
        self.loading_label = None
        self.spinner_index = 0
        self.spinner_frames = ['|', '/', '—', '\\']

    def generate_quiz(self):
        topic = self.topic_input.get().strip()
        if topic:
            self.show_loading(True)
            threading.Thread(target=self.generate_questions_from_topic, args=(topic,)).start()
        else:
            messagebox.showinfo("Info", "Please enter a topic to create a quiz.")

    def generate_questions_from_topic(self, topic):
        print("Generating questions from topic...")
        try:
            chat_completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",
                     "content": "Generate a list of multiple-choice questions with answers and explanations. The output should be in the form of a Python list, with each question represented as a tuple. Each tuple should contain the question text, a list of options, the index of the correct option, and an explanation. There should only be one pair of brackets surrounding the entire list, and no additional brackets around individual tuples."},
                    {"role": "user", "content": f"Create as many needed multiple-choice questions about {topic}. "
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

            # Extract the message content from the response
            content = chat_completion.choices[0].message.content.strip()
            print("Content extracted:", content)  # Debug print

            # Concatenate content if it's split into multiple lists
            if not content.startswith("[") or not content.endswith("]"):
                content = "[" + content.replace("]\n\n[", ", ") + "]"

            # Parse the content into a list of questions
            try:
                self.questions = ast.literal_eval(content)
            except SyntaxError:
                # Fallback to parsing individual questions if there is a syntax error
                self.questions = parse_questions(content)

            # If questions were successfully parsed, shuffle and display them
            if self.questions:
                random.shuffle(self.questions)
                self.master.after(0, self.display_question)
            else:
                self.master.after(0, messagebox.showerror, "Error",
                                  "Could not parse the API response into quiz questions.")
        except Exception as e:
            print("An error occurred:", e)
            self.master.after(0, messagebox.showerror, "Error", str(e))
        finally:
            self.show_loading(False)

    def show_loading(self, show):
        if show:
            if self.loading_label is None:
                self.loading_label = ttk.Label(self.master, text=self.spinner_frames[self.spinner_index],
                                               background="#282a36", foreground="#f8f8f2", font=("Arial", 48))
                self.loading_label.pack(pady=80)
                self.update_spinner()
        else:
            if self.loading_label:
                self.loading_label.destroy()
                self.loading_label = None
                self.spinner_index = 0

    def update_spinner(self):
        if self.loading_label is not None:  # Check if the loading label still exists
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_frames)
            self.loading_label.config(text=self.spinner_frames[self.spinner_index])
            self.master.after(82, self.update_spinner)
        else:
            return

    def display_question(self):
        self.clean_window()
        question_tuple = self.questions[self.current_question_index]

        if len(question_tuple) != 4:
            print(f"Error: Expected 4 elements, got {len(question_tuple)}: {question_tuple}")
            messagebox.showerror("Error", "Invalid question format.")
            return
        question, options, correct_answer_index, explanation = question_tuple

        self.question_label = ttk.Label(self.master, text=question, wraplength=600, font=('Helvetica', 14))
        self.question_label.pack(pady=20)

        for i, option in enumerate(options):
            rb = ttk.Radiobutton(self.master, text=option, value=i, variable=self.choices)
            rb.pack(anchor='w', padx=20, pady=5)

        self.submit_button = ttk.Button(self.master, text="Submit", command=self.check_answer)
        self.submit_button.pack(pady=20)

        self.try_new_topic_button = ttk.Button(self.master, text="Try New Topic", command=self.restart_quiz)
        self.try_new_topic_button.pack(pady=10)

    def check_answer(self):
        _, _, correct_answer_index, explanation = self.questions[self.current_question_index]
        selected_answer_index = int(self.choices.get())

        if selected_answer_index == correct_answer_index:
            self.display_correct()
        else:
            self.display_explanation(explanation)

    def display_correct(self):
        self.clean_window()
        correct_label = ttk.Label(self.master, text="Correct!", wraplength=600, font=('Helvetica', 14),
                                  foreground="#50fa7b")
        correct_label.pack(pady=20)
        self.master.after(1000, self.next_question)

    def display_explanation(self, explanation):
        self.clean_window()
        explanation_label = ttk.Label(self.master, text=f"Incorrect!\n\n{explanation}", wraplength=600, font=('Helvetica', 14), foreground="#ff5555")
        explanation_label.pack(pady=20)
        words = explanation.split()
        display_time = len(words) * 340  # 340 ms per word
        self.master.after(display_time, self.next_question)

    def next_question(self):
        self.current_question_index += 1
        if self.current_question_index == len(self.questions):
            self.end_quiz()
        else:
            self.display_question()

    def end_quiz(self):
        self.clean_window()
        end_label = ttk.Label(self.master, text="Quiz Finished! Would you like to retry?", wraplength=600,
                              font=('Helvetica', 14))
        end_label.pack(pady=20)
        retry_button = ttk.Button(self.master, text="Retry", command=self.restart_quiz)
        retry_button.pack(pady=10)
        # Adjust the placement of new_topic_button to be below retry_button
        new_topic_button = ttk.Button(self.master, text="Try New Topic", command=self.restart_quiz)
        new_topic_button.pack(pady=10)
        exit_button = ttk.Button(self.master, text="Exit", command=self.master.quit)
        exit_button.pack(pady=10)

    def restart_quiz(self):
        self.current_question_index = 0
        self.questions = []
        self.clean_window()
        # Recreate the widgets
        self.intro_label = ttk.Label(self.master, text="Enter the topic you want to create a quiz about:",
                                     wraplength=400)
        self.intro_label.pack(pady=10)
        self.topic_input = tk.Entry(self.master, width=50, bg="#44475a", fg="#f8f8f2", insertbackground="white")
        self.topic_input.pack(pady=10)
        self.submit_button = ttk.Button(self.master, text="Generate Quiz", command=self.generate_quiz)
        self.submit_button.pack(pady=10)

    def clean_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()


# Run the quiz app
root = tk.Tk()
app = QuizApp(root)
root.mainloop()
