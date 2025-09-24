# Import libraries
import streamlit as st
import pandas as pd
import logging
import json
import datetime

# Import files
from utils.helper_functions import (
    built_prompt_rows,  
    apply_config_func,
    create_feedback_prompt,
    create_grading_prompt,
    process_model_response,
    load_json,
    combine_students,
    pick_random_student
    )

from utils.excel_export import ExcelExporter

try:
    from utils.helper_functions import save_config_func
except ImportError as e:
    import streamlit as st
    import pandas as pd
    def save_config_func():
        st.session_state.save_config = True
        st.session_state.apply_config = False
        st.session_state.df = None

try:
    from utils.helper_functions import load_defaults
except ImportError as e:
    gt = load_json("sample/gt.json")
#    student = load_json("sample/students/student_a.json")
    students = combine_students("sample/students/student_a.json", "sample/students/student_b.json")
    rubric = load_json("sample/rubric.json")
    
try:
    from utils.helper_functions import combine_students
except ImportError as e:
    students = []
    for file in ["sample/students/student_a.json", "sample/students/student_b.json"]:
        with open(file, "r") as f:
            data = json.load(f)
            students.append(data)

from model_manager.custom_model import CustomModel
from model_manager.model_fallback import ModelFallback

# Set page configuration
st.set_page_config(
    page_title="AIGS", 
    layout="wide", 
    initial_sidebar_state="expanded"
    )

# Initialize session state variables
defaults = {
    "gt": None,
    "rubric": None,
    "students": None,
    "apply_config": False,
    "save_config": False,
    "df": None,
    "final_df": None,
    "feedback_length": "Standard",
    "custom_model_flag": False,
    "custom_model_name": None,
    "s_id": None
}

for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# load sample data
if st.session_state.gt is None or st.session_state.students is None or st.session_state.rubric is None:
    st.session_state.gt, st.session_state.students, st.session_state.rubric = load_defaults()

excel = ExcelExporter()

# Sidebar
with st.sidebar:
    st.image(
        "https://i0.wp.com/www.niallmcnulty.com/wp-content/uploads/2023/05/ai_auto_assessment.png?ssl=1", 
        width=250
        )
    st.markdown("# AI Grading & Feedback System")
    st.markdown("Use this app to **configure, review, and publish** grading and feedback for student scripts using AI.")
    st.markdown("Note that this is a mock prototype.")
    st.markdown("---")
    st.markdown("## Instructions")
    st.markdown("""
                1. **Configure**: Upload materials, set preferences, and preview the AI output.
                2. **Review**: Apply your configuration, edit, and validate the results.
                3. **Publish**: Finalise and publish the reviewed result.
                """)
    st.markdown("---")
    st.markdown("## Contact")
    st.markdown("Nura")
    st.markdown('<a href="mailto:nura.jamil@gmail.com">📧 Email Me</a>', unsafe_allow_html=True)


tab1, tab2, tab3 = st.tabs([
    r"$\textsf{\Large Step 1: Configure}$", 
    r"$\textsf{\Large Step 2: Review}$", 
    r"$\textsf{\Large Step 3: Publish}$"
    ])

# Tab 1: Configure
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
    
    
    st.subheader("Configure AI System")
    st.markdown("")
    st.info("Complete the steps below. Remember to **save your configuration** before proceeding to Review and Publish.")
    st.markdown("")
    
    # Main container for configuration
    with st.container(border=True):
        # Step 1: Upload student scripts
        st.markdown("<div class='field-title'>1. Upload Student Scripts</div>", unsafe_allow_html=True)
        uploaded_scripts = st.file_uploader(
            "Select materials to upload...", 
            type=["txt", "pdf", "docx"], 
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="key_uploaded_scripts"
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # Step 2: Upload rubric, criterion 
        st.markdown("<div class='field-title'>2. Upload Rubric / Marking Guide</div>", unsafe_allow_html=True)
        uploaded_rubric = st.file_uploader(
        "Select materials to upload...", 
        type=["txt", "pdf", "docx"], 
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="key_uploaded_rubric"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # Step 3: Upload ground truth
        st.markdown("<div class='field-title'>3. Upload Ground Truth (Sample Marked Scripts)</div>", unsafe_allow_html=True)
        uploaded_gt = st.file_uploader(
        "Select materials to upload...", 
        type=["txt", "pdf", "docx"], 
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="key_uploaded_gt"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # Step 4: Edit advanced settings
        st.markdown("<div class='field-title'>4. Edit Advance Settings (Optional)</div>", unsafe_allow_html=True)
        with st.expander("4. Advance Settings", expanded=False):
            # Step 4.1: Select model
            st.markdown("<div class='field-title'>1. Select Model</div>", unsafe_allow_html=True)
            model_choice = st.selectbox(
                "select model", 
                ["Deepseek-R1", "Gemini-2.0-Flash", "Other (OpenAI)"],
                label_visibility="collapsed",
                key="selected_model"
                )
            if model_choice == "Other (OpenAI)":
                st.text_input("Model Name", key="custom_model_name")
                st.text_input("API Key", type="password", key="custom_model_api")
                st.text_input("Endpoint URL", key="custom_model_url")

            st.markdown("</div>", unsafe_allow_html=True)

            if (st.session_state.custom_model_name and st.session_state.custom_model_api) is not None:
                st.session_state.custom_model_flag = True

            # Step 4.2: Set feedback length - concise, medium, detailed
            st.markdown("<div class='field-title'>2. Set Feedback length</div>", unsafe_allow_html=True)
            feedback_length = st.radio(
                "Choose feedback length", 
                ["Brief", "Standard", "Comprehensive"],
                index=["Brief", "Standard", "Comprehensive"].index(st.session_state.feedback_length),
                horizontal=True,
                label_visibility="collapsed",
                key="feedback_length"
                )
            st.markdown("</div>", unsafe_allow_html=True)

            # Step 4.3: Set confidence threshold
            st.markdown("<div class='field-title'>3. Set Confidence Threshold</div>", unsafe_allow_html=True)
            confidence_threshold = st.slider(
                "Confidence Threshold (%)", 
                min_value=0, 
                max_value=100, 
                value=90,
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
                label_visibility="hidden",
                key="key_auto_publish"
                )
            if auto_publish == True:
                auto_text = "Auto-publish is **enabled**. Results that meet the confidence threshold will be automatically reviewed and published by the AI system."
            else:
                auto_text = "Auto-publish is **disabled**. You will need to manually review all results."
            st.info(auto_text)               
            st.markdown("</div>", unsafe_allow_html=True)

        # Step 5: Preview AI output
        st.markdown("---")
        st.markdown("<div class='field-title'>5. Click To Preview AI Output", unsafe_allow_html=True)
        preview = st.button("Preview", key="key_button_review")
        prompt_rows = built_prompt_rows(st.session_state.gt, st.session_state.students, st.session_state.rubric)
        print(f"Prompt rows generated: {prompt_rows}")
                
        left, right = st.columns(2)

        # Display student scripts and AI output side by side
        with left:
            # Container for student scripts
            with st.container(border=True, height=400):
                st.markdown("**Script Preview**")
                st.markdown("---")

                if preview:
                    st.session_state.s_id = pick_random_student(st.session_state.students)
                    for row in prompt_rows:
                        s_id = row.get("s_id")
                        if s_id == st.session_state.s_id:
                            st.markdown(f"Q{row.get('q_id')}. {row.get('q_text')}")
                            st.markdown("**Answer:**")
                            st.markdown(f"**{row.get('s_answer', 'No answers provided.')}**")
                            st.markdown("---")


        with right:
            # Container for AI output
            with st.container(border=True, height=400):
                st.markdown("**AI Output Preview**")
                st.markdown("---")
                if preview:

                    with st.spinner("Running preview..."):
                        grading_set = []

                        # 1. Grading
                        for i, prompt in enumerate(prompt_rows):
                            s_id = prompt.get("s_id")
                            q_id = prompt.get("q_id")
                            if s_id == st.session_state.s_id:
                                system_prompt, user_prompt = create_grading_prompt(prompt)
                                st.markdown(f"Q{q_id}")

                                try:
                                    if st.session_state.custom_model_flag:
                                        CM = CustomModel(
                                            st.session_state.custom_model_api, 
                                            st.session_state.custom_model_name
                                            )
                                        response = CM.model_pipeline(system_prompt, user_prompt)
                                    else:
                                        MF = ModelFallback()
                                        response = MF.call_with_fallback(system_prompt, user_prompt)

                                    parsed = process_model_response(response)
                                    grading_set.append(parsed)
                                    st.markdown("---")
                                
                                except Exception as e:
                                    fallback = {
                                        "marks_awarded": 10,
                                        "max_marks": 10, 
                                        "reasoning": "Correct application, clear working, and correct answer. Full marks as per rubric."
                                    }
                                    parsed = process_model_response(fallback)
                                    grading_set.append(fallback)
                                    st.markdown("---")
                            
                            
                        
                        # 2. Feedback
                        st.markdown("**Overall Feedback:**")
                        system_prompt, user_prompt = create_feedback_prompt(
                            grading_set,
                            st.session_state.feedback_length
                        )

                        try:
                            if st.session_state.custom_model_flag:
                                CM = CustomModel(
                                        st.session_state.custom_model_api, 
                                        st.session_state.custom_model_name
                                    )
                                response = CM.model_pipeline(system_prompt, user_prompt)
                            else:
                                MF = ModelFallback()
                                response = MF.call_with_fallback(system_prompt, user_prompt)
                            
                            st.markdown(response)
                        
                        except Exception as e:
                            st.markdown("**Overall Feedback (Sample):**")
                            st.markdown("""
                                Great effort on this assignment! You demonstrated a solid understanding of the key concepts.
                                """)
                        
                                    
                                    
        st.markdown("---")

        # Step 6: Save configuration
        st.markdown("<div class='field-title'>6. Click To Save Configuration", unsafe_allow_html=True)
        st.session_state.save_config = st.button("Save Configuration",on_click=save_config_func, disabled=st.session_state.save_config)
        st.markdown("")
        if st.session_state.save_config:
            st.success("Configuration saved successfully! You may now proceed to Step 2: Review.")
        
    st.markdown("</div>", unsafe_allow_html=True)
    st.write("---")
    st.write("Updated on:", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))

# Tab 2 - Review
with tab2:
    st.subheader("Review AI Output")
    st.markdown("")

    if not st.session_state.save_config:
        st.info("Please **save your configuration** before proceeding to review the results.")
        st.markdown("")
    else:
        st.button("Generate Results", on_click=apply_config_func, disabled=st.session_state.apply_config, key="key_button_apply")
        st.markdown("")
        st.info("Click to generate and review the results.")
        st.markdown("")
    if st.session_state.apply_config:
        st.info("Double click on the cells to edit. Press Enter to save changes.")
        st.markdown("")

        #st.session_state.df = review_table(prompt_rows)
        edited_df = st.data_editor(st.session_state.df, key="key_editor_df", hide_index=True)
        st.warning("Please review the AI output. Make sure the output is accurate before proceeding to publish.")
        st.session_state.df = edited_df

    st.write("---")
    st.write("Updated on:", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))

# Publish tab
with tab3:
    st.subheader("Publish Results")
    st.markdown("")
    if not st.session_state.apply_config:
        st.info("Please complete the previous steps to view and publish the results.")
        st.markdown("")
    
    else:
        st.info("Confirm the results below before publishing.")
        st.markdown("")
#        excel_data = excel.create_excel_report(st.session_state.df)
#        if excel_data:
#            st.download_button(
#                "Download Excel Report",
#                data = excel_data,
#                file_name = f"grading_report.xlsx",
#                mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#            )
        st.dataframe(st.session_state.df, hide_index=True)
        if st.button("Publish"):
            st.success("The results have been published successfully!")
        

    st.write("---")
    st.write("Updated on:", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))


