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

def load_json(path):
    import json
    with open(path, 'r') as f:
        return json.load(f) 
    

student_path = "sample/students/student_b.json"
gt_path = "sample/gt.json"
rubric_path = "sample/rubric.json"

gt = load_json(gt_path)
student = load_json(student_path)
rubric = load_json(rubric_path)


def format_prompt_input(gt, student, rubric):
    """Format the input prompt for the model."""
    prompt = []
    answers = student.get("answers", {})
    for q in gt.get("questions", []):
        q_id = q.get("id")
        q_text = q.get("text")
        q_ground_truth = q.get("ground_truth", "")
        answer_text = answers.get(q_id, "No answer provided.")
        rubric_parts = rubric.get("parts", [])
        for part in rubric_parts:
            if part.get("qid") == q_id:
                rubric_criteria = part.get("criteria", "No criteria provided.")
                max_marks = part.get("max_marks", 0)
        prompt.append({
            "q_id":q_id, 
            "q_text": q_text, 
            "s_answer": answer_text,
            "ground_truth": q_ground_truth, 
            "rubric_criteria": rubric_criteria, 
            "max_marks": max_marks})
    return prompt

def format_table_input(gt, student):
    """Format the input prompt for the model."""
    prompt = []
    answers = student.get("answers", {})
    for q in gt.get("questions", []):
        q_id = q.get("id")
        q_text = q.get("text")
        q_ground_truth = q.get("ground_truth", "")
        answer_text = answers.get(q_id, "No answer provided.")
        rubric_parts = rubric.get("parts", [])
        for part in rubric_parts:
            if part.get("qid") == q_id:
                rubric_criteria = part.get("criteria", "No criteria provided.")
                max_marks = part.get("max_marks", 0)
        prompt.append({
            "q_id":q_id, 
            "q_text": q_text, 
            "s_answer": answer_text,
            "ground_truth": q_ground_truth, 
            "rubric_criteria": rubric_criteria, 
            "max_marks": max_marks})
    return prompt


def review_table(data):
    """Create a review table from the data."""
    df = pd.DataFrame(data, columns=["q_id", "s_answer", "max_marks"])
    df.rename(columns={"q_id": "Q", "s_answer": "Student Answers", "max_marks": "Max Marks"}, inplace=True)
    df["Marks Awarded"] = [8, 9]  # Example marks awarded
    df["Feedback"] = [
        "-", 
        "-"
        ]  # Example reasoning
    df["Reasoning"] = [
        "Good understanding but minor calculation error.", 
        "Well done, just a small mistake in the final step."
        ]  # Example reasoning
    df["Score"] = df["Marks Awarded"].astype(str) + " / " + df["Max Marks"].astype(str)
    new_row = {
        "Q": "Total", 
        "Student Answers": "-", 
        "Score": df["Marks Awarded"].sum().astype(str) + " / " + df["Max Marks"].sum().astype(str), 
        "Feedback": "Great effort on this assignment! You demonstrated a solid understanding of the key concepts. To improve further, focus on double-checking your calculations and ensuring all parts of the question are fully addressed. Keep up the good work!",
        "Reasoning": "-"}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df = df[["Q", "Student Answers", "Score", "Feedback", "Reasoning"]]
   
    return df


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

def create_feedback_prompt(grading_output, feedback_length="concise"):
    """Create the feedback prompt based on the grading output."""
    user_prompt = FEEDBACK_USER_PROMPT_TEMPLATE.format(
        grading_output=grading_output,
        feedback_length=feedback_length
    )
    return FEEDBACK_SYSTEM_PROMPT, user_prompt



