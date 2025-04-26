import streamlit as st
import openai
import os
from dotenv import load_dotenv
import pandas as pd
from fpdf import FPDF

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Streamlit Page Config
st.set_page_config(page_title="Interview Prep Bot 🎯", page_icon="🎯", layout="centered", initial_sidebar_state="collapsed")

# Custom CSS (Vibrant colors + dark theme)
st.markdown("""
    <style>
    body {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stApp {
        background-color: #0e1117;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', sans-serif;
        color: #7dd3fc; /* Light Blue */
    }
    p, label, div {
        font-family: 'Poppins', sans-serif;
        font-size: 18px;
        color: #d1d5db;
    }
    .stTextInput>div>div>input, .stTextArea>div>textarea {
        background-color: #1c1e26;
        color: #ffffff;
    }
    .stButton>button {
        background-color: #6366f1;
        color: white;
        border-radius: 10px;
        height: 3em;
        width: 10em;
        font-weight: bold;
        margin: 10px;
    }
    .stButton>button:hover {
        background-color: #4f46e5;
    }
    </style>
""", unsafe_allow_html=True)

# Global variables
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'scores' not in st.session_state:
    st.session_state.scores = []
if 'leaderboard' not in st.session_state:
    st.session_state.leaderboard = pd.DataFrame(columns=["Name", "Score"])

# Title
st.title("🎯 AI Interview Preparation Bot")

# Divider
st.markdown("---")

# User Input Section
role = st.selectbox("🎯 Choose Your Target Role:", ["Software Engineer", "Data Scientist", "Product Manager", "Backend Developer", "Frontend Developer"])
mode = st.radio("🛠️ Choose Interview Mode:", ["Technical", "Behavioral"])
user_name = st.text_input("👤 Enter Your Name for Leaderboard:")

start_interview = st.button("🚀 Start 5-Question Mock Interview")

# Function to generate interview questions
def generate_question(role, mode):
    prompt = f"Act like a professional interviewer. Ask 1 {mode.lower()} interview question for a {role}."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional interviewer."},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']

# Interview Logic
if start_interview:
    st.session_state.questions = [generate_question(role, mode) for _ in range(5)]
    st.session_state.current_question = 0
    st.session_state.answers = []
    st.session_state.scores = []

if st.session_state.questions and st.session_state.current_question < 5:
    st.subheader(f"🧠 Question {st.session_state.current_question + 1}:")
    st.write(st.session_state.questions[st.session_state.current_question])

    user_answer = st.text_area("✍️ Your Answer:", key=f"answer_{st.session_state.current_question}")

    if st.button("✅ Submit Answer", key=f"submit_{st.session_state.current_question}"):
        if user_answer.strip() == "":
            st.warning("⚠️ Please type your answer before submitting!")
        else:
            feedback_prompt = f"Evaluate this answer. Give short feedback and a score out of 10.\n\nQuestion: {st.session_state.questions[st.session_state.current_question]}\n\nAnswer: {user_answer}"
            feedback_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert evaluator."},
                    {"role": "user", "content": feedback_prompt}
                ]
            )
            feedback = feedback_response['choices'][0]['message']['content']

            st.session_state.answers.append((user_answer, feedback))

            # Extract score from feedback (very basic way)
            import re
            score = re.findall(r"(\d+)/10", feedback)
            score = int(score[0]) if score else 7  # fallback score

            st.session_state.scores.append(score)
            st.success(f"🎯 Answer submitted with score: {score}/10")

            st.session_state.current_question += 1

# After Interview
if st.session_state.current_question == 5 and st.session_state.questions:
    st.subheader("🏆 Interview Completed!")

    total_score = sum(st.session_state.scores)
    avg_score = round(total_score / 5, 2)

    st.success(f"🎯 Your Average Score: {avg_score}/10")

    # Update leaderboard
    if user_name:
        st.session_state.leaderboard = pd.concat([
            st.session_state.leaderboard,
            pd.DataFrame({"Name": [user_name], "Score": [avg_score]})
        ], ignore_index=True)

    # Session Summary
    with st.expander("📋 View Full Session Summary"):
        for i, (answer, feedback) in enumerate(st.session_state.answers):
            st.markdown(f"**Q{i+1}:** {st.session_state.questions[i]}")
            st.markdown(f"**Your Answer:** {answer}")
            st.markdown(f"**Feedback:** {feedback}")
            st.markdown("---")

    # PDF Download
    if st.button("📄 Download Interview Summary as PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Interview Session Summary", ln=True, align="C")
        pdf.ln(10)

        for i, (answer, feedback) in enumerate(st.session_state.answers):
            pdf.multi_cell(0, 10, txt=f"Q{i+1}: {st.session_state.questions[i]}")
            pdf.multi_cell(0, 10, txt=f"Answer: {answer}")
            pdf.multi_cell(0, 10, txt=f"Feedback: {feedback}")
            pdf.ln(5)

        pdf_filename = f"{user_name}_interview_summary.pdf"
        pdf.output(pdf_filename)
        with open(pdf_filename, "rb") as file:
            btn = st.download_button(
                label="Download PDF",
                data=file,
                file_name=pdf_filename,
                mime="application/octet-stream"
            )

    st.markdown("---")

    # Show Leaderboard
    st.subheader("🌟 Leaderboard (Top Scores)")
    st.dataframe(st.session_state.leaderboard.sort_values("Score", ascending=False).reset_index(drop=True))

# Footer
st.markdown("---")
st.caption("Made with ❤️ using Streamlit, OpenAI, FPDF | Hackathon Project")
