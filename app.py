# Import libraries
import streamlit as st
import pandas as pd
import logging
import time

# Import files
from utils.helper_functions import student, gt, rubric, format_prompt_input, review_table
from prompts import (
    GRADE_JSON_INSTRUCTIONS, 
    GRADING_SYSTEM_PROMPT, 
    GRADING_USER_PROMPT_TEMPLATE,
    FEEDBACK_SYSTEM_PROMPT,
    FEEDBACK_USER_PROMPT_TEMPLATE
    )
from model_manager.deepseek_model import DeepseekModel
from model_manager.gemini_model import GeminiModel

# Set page configuration
st.set_page_config(
    page_title="AIGS", 
    layout="wide", 
    initial_sidebar_state="expanded"
    )

# Initialize session state variables
if "gt" not in st.session_state:
    st.session_state.gt = 0
if "rubric" not in st.session_state:
    st.session_state.rubric = None
if "scripts" not in st.session_state:
    st.session_state.scripts = ""

tab1, tab2, tab3 = st.tabs([
    r"$\textsf{\Large Step 1: Configure}$", 
    r"$\textsf{\Large Step 2: Review}$", 
    r"$\textsf{\Large Step 3: Publish}$"
    ])

with st.sidebar:
    st.image("https://i0.wp.com/www.niallmcnulty.com/wp-content/uploads/2023/05/ai_auto_assessment.png?ssl=1", width=250)
    st.markdown("# AI Grading & Feedback System")
    st.markdown("Use this app to configure, review, and publish grading and feedback of student scripts using AI.")
    st.markdown("---")
    st.markdown("## Instructions")
    st.markdown("""
                1. **Configure**: Upload materials, set your preferences, and preview the AI output.
                2. **Review**: Apply configuration and review the results.
                3. **Publish**: Once satisfied, publish the result.
                """)
    st.markdown("---")
    st.markdown("## Contact")
    st.markdown('<a href="mailto:nura.jamil@gmail.com">📧 Email Me</a>', unsafe_allow_html=True)

# Configure tab
with tab1:
    # custom style for expanders and layout
    st.markdown("""
                <style>
                .expander-box {
                    background-color: #f9f9f9;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #ddd;
                    margin-bottom: 10px;
                }
                .title {
                    font-size: 18px;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 5px;
                }
                </style>
                """, unsafe_allow_html=True)
    
    # title
    st.subheader("Configure AI System")
    st.markdown("")
    st.info("Complete the steps below. Remember to save your configuration before proceeding to Review and Publish.")

    st.markdown("""
                <style>
                .expander-content {
                    background-color: #f9f9f9;
                    padding: 15px;
                    border-radius: 5px;
                    border: 1px solid #ddd;
                }
                .field-title {
                    font-size: 16px;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 5px;
                }
                </style>
                """, unsafe_allow_html=True)

    st.markdown("""
                <style>
                .expander-box {
                    background-color: #f9f9f9;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #ddd;
                    margin-bottom: 10px;
                    box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
                }
                .card:hover {
                    box-shadow: 0px 8px 16px rgba(0, 0, 0, 0.2);
                    transform: translateY(-2px);
                    transition: all 0.3s ease;
                }
                </style>
                """, unsafe_allow_html=True)
    
    # Main container for configuration
    with st.container(border=True):
        # Step 1: Upload student scripts
        st.markdown("<div class='field-title'>1. Upload Student Scripts</div>", unsafe_allow_html=True)
        uploaded_scripts = st.file_uploader(
            "Select materials to upload...", 
            type=["txt", "pdf", "docx"], 
            accept_multiple_files=True,
            label_visibility="collapsed",
            key=st.session_state.scripts
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # Step 2: Upload ground truth documents (q&a pairs)
        st.markdown("<div class='field-title'>2. Upload Ground Truth</div>", unsafe_allow_html=True)
        uploaded_gt = st.file_uploader(
        "Select materials to upload...", 
        type=["txt", "pdf", "docx"], 
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=st.session_state.gt
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # Step 3: Upload rubric
        st.markdown("<div class='field-title'>3. Upload Rubric</div>", unsafe_allow_html=True)
        uploaded_rubric = st.file_uploader(
        "Select materials to upload...", 
        type=["txt", "pdf", "docx"], 
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=st.session_state.rubric
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # Step 4: Edit advanced settings
        st.markdown("<div class='field-title'>4. Edit Advance Settings (Optional)</div>", unsafe_allow_html=True)
        with st.expander("4. Advance Settings", expanded=False):
            # Step 4.1: Select model
            st.markdown("<div class='field-title'>1. Select Model</div>", unsafe_allow_html=True)
            llm = st.selectbox(
                "", 
                ["Deepseek-R1", "Gemini-2.0-Flash"],
                label_visibility="collapsed",
                )
            st.markdown("</div>", unsafe_allow_html=True)

            # Step 4.2: Set feedback length - concise, medium, detailed
            st.markdown("<div class='field-title'>2. Set Feedback length</div>", unsafe_allow_html=True)
            feedback_length = st.radio(
                "", 
                ["Concise", "Medium", "Detailed"],
                index=0,
                horizontal=True,
                label_visibility="collapsed"
                )
            st.markdown("</div>", unsafe_allow_html=True)

            # Step 4.3: Set confidence threshold
            st.markdown("<div class='field-title'>3. Set Confidence Threshold</div>", unsafe_allow_html=True)
            confidence_threshold = st.slider(
                "Confidence Threshold (%)", 
                min_value=0, 
                max_value=100, 
                value=80,
                step=1,
                label_visibility="collapsed"
                )
            st.info(f"Current confidence threshold is set to **{confidence_threshold}%**.")
            st.markdown("</div>", unsafe_allow_html=True)

            # Step 4.4: Enable auto-publish
            st.markdown("<div class='field-title'>4. Enable Auto-Publish</div>", unsafe_allow_html=True)
            auto_publish=st.toggle(
                "Enable auto-publish when confidence threshold is met", 
                value=False,
                label_visibility="hidden"
                )
            if auto_publish == True:
                auto_text = "Auto-publish is **enabled**. The AI system will automatically publish results when the confidence threshold is met."
            else:
                auto_text = "Auto-publish is **disabled**. You will need to manually publish results."
            st.info(auto_text)               
            st.markdown("</div>", unsafe_allow_html=True)

        # Step 5: Preview AI output
        st.markdown("---")
        st.markdown("<div class='field-title'>5. Click To Preview AI Output", unsafe_allow_html=True)
        preview = st.button("Preview")
        prompt_inputs = format_prompt_input(gt, student, rubric)
                
        left, right = st.columns(2)

        # Display student scripts and AI output side by side
        with left:
            # Container for student scripts
            with st.container(border=True, height=400):
                st.markdown("**Script Preview**")
                st.markdown("---")

                if preview:
                    answers = student.get("answers", {})
                    for input in prompt_inputs:
                        q_id = input.get("q_id")
                        q_text = input.get("q_text")
                        st.markdown(f"Q{q_id}. {q_text}")
                        answer_text = input.get("q_text", "No answer provided.")
                        st.markdown("**Answer:**")
                        st.markdown(f"**{answer_text}**")
                        st.markdown("---")


        with right:
            # Container for AI output
            with st.container(border=True, height=400):
                st.markdown("**AI Output Preview**")
                st.markdown("---")
                if preview:
                    prompts = format_prompt_input(gt, student, rubric)
                    for i, prompt in enumerate(prompts):
                        DS = DeepseekModel(prompt=prompt)
                        GM = GeminiModel(prompt=prompt)
                        try:
                            response = GM.model_pipeline(prompt=prompt)
                        except Exception as e:
                            try:
                                response = DS.model_pipeline(prompt=prompt)
                            except Exception as e:
                                response = {"marks_awarded": "6", "max_marks": "10", "reasoning": "Error in generating response. Try again later"}
                                logging.error(f"Both models failed: {e}")
                        st.markdown(f"Q{i+1}")
                        st.markdown(f"Marks Awarded: {response.get('marks_awarded', 6)} / {response.get('max_marks', 10)}")
                        st.markdown(f"Reasoning: {response.get('reasoning', '')}")
                        st.markdown("---")
                        
                    st.markdown("**Overall Feedback:**")
                    st.markdown("""
                                Great effort on this assignment! You demonstrated a solid understanding of the key concepts.
                                To improve further, focus on double-checking your calculations and ensuring all parts of the question
                                are fully addressed. Keep up the good work!
                                """)
        st.markdown("---")

        # Step 6: Save configuration
        st.markdown("<div class='field-title'>6. Click To Save Configuration", unsafe_allow_html=True)
        save = st.button("Save Configuration")
        st.markdown("")
        if save:
            st.success("Configuration saved successfully!")

    
    st.markdown("</div>", unsafe_allow_html=True)
    st.write("---")
    st.write("Updated on:", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))

# Review tab
with tab2:
    st.subheader("Review AI Output")
    st.markdown("")
    st.info("Double click on the cells to edit. Press Enter to save changes.")
    st.markdown("")
    if 'df' not in st.session_state:
        st.session_state.df = review_table(prompt_inputs)
    edited_df = st.data_editor(st.session_state.df, key="my_data_editor", hide_index=True)
    st.warning("Please review the AI output. Make sure the output is accurate before proceeding to publish.")
    st.write("---")
    st.write("Updated on:", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))

# Publish tab
with tab3:
    st.subheader("Publish Results")
    st.markdown("")
    st.info("Confirm the results below before publishing.")
    st.markdown("")
    st.dataframe(review_table(prompt_inputs), hide_index=True)
    if st.button("Publish"):
        st.success("The results have been published successfully!")
    st.write("---")


