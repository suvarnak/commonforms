import streamlit as st
import tempfile
import os
from commonforms.inference import FFDNetDetector, render_pdf
from commonforms.form_creator import PyPdfFormCreator
from commonforms.utils import BoundingBox

st.title("CommonForms Interactive Field Detector")

# File upload
uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

# Confidence score input
confidence = st.slider("Confidence Threshold", min_value=0.1, max_value=1.0, value=0.3, step=0.05)

if uploaded_file is not None:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        input_path = tmp_file.name

    # Detect fields
    if st.button("Detect Fields"):
        with st.spinner("Detecting form fields..."):
            detector = FFDNetDetector("FFDNet-L")
            pages = render_pdf(input_path)
            widgets_by_page = detector.extract_widgets(pages, confidence=confidence)
            
            # Flatten widgets into single list with page info
            detections = []
            for page_num, widgets in widgets_by_page.items():
                for widget in widgets:
                    detections.append(widget)
        
        st.session_state.detections = detections
        st.session_state.pages = pages
        st.session_state.input_path = input_path

    # Show detected fields if available
    if hasattr(st.session_state, 'detections'):
        st.subheader("Detected Fields")
        
        # Group detections by page
        detections_by_page = {}
        for detection in st.session_state.detections:
            page = detection.page
            if page not in detections_by_page:
                detections_by_page[page] = []
            detections_by_page[page].append(detection)
        
        # Store selected fields
        if 'selected_fields' not in st.session_state:
            st.session_state.selected_fields = {i: True for i in range(len(st.session_state.detections))}
        
        # Display each page with checkboxes
        for page_num, page_detections in detections_by_page.items():
            st.write(f"**Page {page_num + 1}**")
            
            # Show page image
            if page_num < len(st.session_state.pages):
                st.image(st.session_state.pages[page_num].image, width=400)
            
            # Show checkboxes for each detection on this page
            for i, detection in enumerate(st.session_state.detections):
                if detection.page == page_num:
                    field_type = detection.widget_type
                    bbox = detection.bounding_box
                    
                    checkbox_key = f"field_{i}"
                    st.session_state.selected_fields[i] = st.checkbox(
                        f"{field_type} - [{bbox.x0:.3f}, {bbox.y0:.3f}, {bbox.x1:.3f}, {bbox.y1:.3f}]",
                        value=st.session_state.selected_fields.get(i, True),
                        key=checkbox_key
                    )
        
        # Generate PDF with selected fields
        if st.button("Generate PDF with Selected Fields"):
            with st.spinner("Creating fillable PDF..."):
                # Filter selected detections
                selected_detections = [
                    detection for i, detection in enumerate(st.session_state.detections)
                    if st.session_state.selected_fields.get(i, False)
                ]
                
                # Create output PDF
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as output_file:
                    output_path = output_file.name
                
                form_creator = PyPdfFormCreator(st.session_state.input_path)
                form_creator.clear_existing_fields()
                
                for i, detection in enumerate(selected_detections):
                    field_name = f"{detection.widget_type.lower()}_{i}"
                    
                    if detection.widget_type == "TextBox":
                        form_creator.add_text_box(field_name, detection.page, detection.bounding_box)
                    elif detection.widget_type == "ChoiceButton":
                        form_creator.add_checkbox(field_name, detection.page, detection.bounding_box)
                    elif detection.widget_type == "Signature":
                        form_creator.add_signature(field_name, detection.page, detection.bounding_box)
                
                form_creator.save(output_path)
                form_creator.close()
                
                # Provide download
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="Download Fillable PDF",
                        data=f.read(),
                        file_name="fillable_form.pdf",
                        mime="application/pdf"
                    )
                
                # Clean up
                os.unlink(output_path)
        
        # Clean up input file when done
        if st.button("Clear"):
            if hasattr(st.session_state, 'input_path'):
                os.unlink(st.session_state.input_path)
            for key in ['detections', 'input_path', 'selected_fields', 'pages']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()