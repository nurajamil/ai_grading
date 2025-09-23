# Import libraries
import pandas as pd
from typing import List, Dict, Any
from io import BytesIO
import streamlit as st


class ExcelExporter:
    "Export grading results and feedback in Excel format."

    def __init__(self):
        pass

    def create_excel_report(self, results: List[Dict[str, Any]]) -> BytesIO:
        try:
            output = BytesIO()

            with pd.ExcelWriter(output, engine="xlsxwriter")as writer:
                self.create_summary_sheet(results, writer)
            
            output.seek(0)
            
            return output.getvalue()
        
        except Exception as e:
            st.error(f"Error creating Excel report: {str(e)}")
            return None
        
    
    def create_summary_sheet(self, results: List[Dict[str, Any]], writer):
        summary_data = []
        results = results.loc[results["Q"] == "Total"]
        summary_data.append({
            "Score": results["Score"],
            "Feedback": results["Feedback"]
        })
        
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name="Summary", index=False)
