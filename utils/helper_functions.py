# Import files
from prompts import (
    GRADE_JSON_INSTRUCTIONS,
    GRADING_SYSTEM_PROMPT, 
    GRADING_USER_PROMPT_TEMPLATE,
    FEEDBACK_SYSTEM_PROMPT, 
    FEEDBACK_USER_PROMPT_TEMPLATE
    )

# Import libraries
from pathlib import Path
import pandas as pd
import streamlit as st
import json

def load_json(path):
    import json
    with open(path, 'r') as f:
        return json.load(f) 
    

# Default loaders - sample data
def load_defaults():
    gt = load_json("sample/gt.json")
    student = load_json("sample/students/student_a.json")
    rubric = load_json("sample/rubric.json")

    return gt, student, rubric


# Prompt builders - per-question rows with student answers, rubric, ground truth, etc
def built_prompt_rows(gt, student, rubric):
    rows = []
    answers = student.get("answers", {})
    for q in gt.get("questions", []):
        q_id = q.get("id")
        q_text = q.get("text")
        q_ground_truth = q.get("ground_truth", "")
        answer_text = answers.get(q_id, "No answer provided.")

        rubric_parts = rubric.get("parts", [])
        for part in rubric_parts:
            if part.get("qid") == q_id:
                criteria = part.get("criteria", "No criteria provided.")
                max_marks = part.get("max_marks", 0)

        rows.append({
            "q_id":q_id, 
            "q_text": q_text, 
            "s_answer": answer_text,
            "ground_truth": q_ground_truth, 
            "rubric_criteria": criteria, 
            "max_marks": max_marks})
    
    return rows


# Table builders - create table - contains dummy data
def review_table(data):
    """Create a review table from the data."""
    df = pd.DataFrame(data, columns=["q_id", "s_answer", "max_marks"])
    df.rename(columns={"q_id": "Q", "s_answer": "Student Answers", "max_marks": "Max Marks"}, inplace=True)

    # Dummy data
    df["Marks Awarded"] = [10, 10]  
    df["Feedback"] = ["-", "-"]  
    df["Reasoning"] = ["Good understanding.", "Well done, good understanding of the concept."]
    df["Score"] = df["Marks Awarded"].astype(str) + " / " + df["Max Marks"].astype(str)

    # Add overall row
    new_row = {
        "Q": "Total", 
        "Student Answers": "-", 
        "Score": df["Marks Awarded"].sum().astype(str) + " / " + df["Max Marks"].sum().astype(str), 
        "Feedback": "Great effort on this assignment! You demonstrated a solid understanding of the key concepts. Keep up the good work!",
        "Reasoning": "-"
        }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df = df[["Q", "Student Answers", "Score", "Feedback", "Reasoning"]]
   
    return df

# Prompt template
def create_grading_prompt(input):
    """Create the grading prompt for a specific question part."""
    user_prompt = GRADING_USER_PROMPT_TEMPLATE.format(
        question_text=input.get("q_text", ""),
        student_answer=input.get("s_answer", ""),
        ground_truth=input.get("ground_truth", ""),
        rubric_criteria=input.get("rubric_criteria", ""),
        max_marks=input.get("max_marks", 0),
        format_instructions=GRADE_JSON_INSTRUCTIONS
    )
    return GRADING_SYSTEM_PROMPT, user_prompt

def create_feedback_prompt(grading_output, feedback_length):
    """Create the feedback prompt based on the grading output."""
    user_prompt = FEEDBACK_USER_PROMPT_TEMPLATE.format(
        grading_output=grading_output,
        feedback_length=feedback_length
    )
    return FEEDBACK_SYSTEM_PROMPT, user_prompt

# Process model response
def process_model_response(response):
    try:
        if isinstance(response, str):
            parsed = json.loads(response)
            st.markdown(f"Marks Awarded: {parsed.get('marks_awarded', 10)} / {parsed.get('max_marks', 10)}")
            st.markdown(f"Reasoning: {parsed.get('reasoning')}")
        elif isinstance(response, dict):
            parsed = response
            st.markdown(f"Marks Awarded: {parsed.get('marks_awarded', 10)} / {parsed.get('max_marks', 10)}")
            st.markdown(f"Reasoning: {parsed.get('reasoning')}")
        else:
            parsed = response
            st.markdown(parsed)
        return parsed
        
    except json.JSONDecodeError as e:
        print(f"Error in loading response: {e}")
        st.markdown(str(response))
        return response

# Session state management
def save_config_func():
    st.session_state.save_config = True
    st.session_state.apply_config = False
    st.session_state.df = None

def apply_config_func():
    st.session_state.apply_config = True
    st.session_state.save_config = True
    gt, student, rubric = load_defaults()
    prompt_inputs = built_prompt_rows(gt, student, rubric)
    st.session_state.df = review_table(prompt_inputs)
    
    