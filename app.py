import streamlit as st
import sqlite3
import pandas as pd
import random
import base64
import tempfile
import shutil
import os

# Function to connect to the database and retrieve N random rows
def get_random_questions(num_questions, uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False) as fp:
        fp.write(uploaded_file.getvalue())
        conn = sqlite3.connect(fp.name)
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM my_table ORDER BY RANDOM() LIMIT {num_questions}')
        questions = cursor.fetchall()
        conn.close()
        
    # remove the temporary file
    os.unlink(fp.name)
    
    return questions

# Function to create the summary table
def create_summary_table(questions, answers, scores):
    data = []
    for i, question in enumerate(questions):
        user_answer = answers.get(question[0], '')  # Retrieve the user's answer using the question text as the key
        if question[1] is not None and isinstance(question[1], bytes):
            try:
                st.image(question[1], caption=f"Question {i+1} Image", width=700)
            except Exception as e:
                st.warning(f"Error loading image for question {i+1}: {e}")

        data.append(list(question[:1]) + ["N/A"] + list(question[2:]) + [user_answer, scores[i]])

    df = pd.DataFrame(data, columns=['Question', 'Image', 'Possible_answers', 'Correct_answer', 'Explanation', 'Your answer', 'Score'])
    return df

# Streamlit app
def main():
    st.title('Quiz App')

    # Upload the database file to use
    uploaded_file = st.file_uploader("Choose a sqlite3 file", type='db')
    if uploaded_file is None:
        st.info("Please upload a sqlite3 file to start the quiz.")
        return

    total_score = 0

    if 'questions' not in st.session_state:
        st.session_state.started = False
        st.session_state.current_question_index = 0
        st.session_state.answers = {}
        st.session_state.scores = []

    if not st.session_state.started:
        num_questions = st.number_input('Number of questions:', min_value=1, max_value=140, value=10, step=1)
        st.session_state.questions = get_random_questions(num_questions, uploaded_file)

        if st.button('Start'):
            st.session_state.started = True

    if st.session_state.current_question_index >= len(st.session_state.questions):
        st.subheader('Quiz Summary')
        total_score = sum(st.session_state.scores)
        st.write(f'Total Score: {total_score}')

        summary_table = create_summary_table(st.session_state.questions, st.session_state.answers, st.session_state.scores)
        st.dataframe(summary_table)

        return

    current_question = st.session_state.questions[st.session_state.current_question_index]
    st.subheader('Question')
    st.write(current_question[0])  

    if current_question[1] is not None:
        st.image(current_question[1])

    st.subheader('Possible Answers')
    possible_answers = current_question[2].split('\n')
    user_answer = st.radio('', possible_answers + ['None'], key='user_answer')  

    st.session_state.answers[current_question[0]] = user_answer.strip() if user_answer != 'None' else ''

    col1, col2 = st.columns(2)
    if col1.button('Previous', key='prev_button') and st.session_state.current_question_index > 0:
        st.session_state.current_question_index -= 1

    if col2.button('Next', key='next_button'):
        st.session_state.current_question_index += 1

        correct_answer = current_question[3]
        explanation = current_question[4]

        user_picked_answer = st.session_state.answers.get(current_question[0], '')
        if user_picked_answer == '':
            score = 0.0  
        elif user_picked_answer == correct_answer:
            score = 1.0
        else:
            score = -0.25

        st.session_state.scores.append(score)

        st.experimental_rerun()

if __name__ == '__main__':
    main()
