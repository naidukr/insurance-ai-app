"""
Insurance AI Application - Streamlit Frontend Dashboard
User interface for claims processing, policy analysis, and customer support
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json

# ==================== Configuration ====================
API_URL = "http://localhost:8000"

# ==================== Page Configuration ====================

st.set_page_config(
    page_title="Insurance AI Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Styling ====================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .stat-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .success { color: #28a745; }
    .warning { color: #ffc107; }
    .danger { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# ==================== Session State ====================

if 'api_url' not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'uploaded_records' not in st.session_state:
    st.session_state.uploaded_records = []

if 'selected_record' not in st.session_state:
    st.session_state.selected_record = None

# ==================== Header ====================

st.markdown('<div class="main-header">🏢 Insurance AI Platform</div>', unsafe_allow_html=True)
st.markdown("*AI-Powered Claims Processing & Policy Analysis System*")
st.divider()

# ==================== Sidebar Navigation ====================

with st.sidebar:
    st.title("📱 Navigation")
    page = st.radio(
        "Select a page:",
        [
            "Dashboard",
            "Process Claim",
            "Analyze Policy",
            "Extract Document",
            "Upload Record",
            "Chat Support",
            "Analytics"
        ]
    )
    
    st.divider()
    st.subheader("Configuration")
    api_url = st.text_input("API URL:", value=st.session_state.api_url)
    st.session_state.api_url = api_url
    
    # API Status
    try:
        response = requests.get(f"{api_url}/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Error")
    except:
        st.warning("⚠️ API Unreachable")

# ==================== Helper Functions ====================

def safe_api_call(method: str, endpoint: str, **kwargs):
    """Make safe API calls with error handling"""
    try:
        url = f"{st.session_state.api_url}{endpoint}"
        response = requests.request(method, url, timeout=10, **kwargs)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, str(e)

# ==================== Dashboard Page ====================

if page == "Dashboard":
    st.subheader("📊 Dashboard Overview")
    
    # Fetch analytics
    analytics, error = safe_api_call("GET", "/api/analytics/dashboard")
    
    if analytics:
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Claims",
                f"{analytics.get('total_claims', 0):,}",
                "+45 today"
            )
        
        with col2:
            st.metric(
                "Processing Time",
                f"{analytics.get('average_processing_time', 0):.1f}h",
                "-0.5h"
            )
        
        with col3:
            st.metric(
                "AI Accuracy",
                f"{analytics.get('ai_accuracy_rate', 0)*100:.0f}%",
                "+2%"
            )
        
        with col4:
            st.metric(
                "Satisfaction",
                f"{analytics.get('customer_satisfaction', 0)*100:.0f}%",
                "+1%"
            )
        
        st.divider()
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Claims Trend
            trend_data, _ = safe_api_call("GET", "/api/analytics/claims-trend")
            if trend_data:
                fig = go.Figure(data=[
                    go.Bar(name='Approved', x=['Claims'], y=[trend_data.get('approved', 0)]),
                    go.Bar(name='Pending', x=['Claims'], y=[trend_data.get('pending', 0)]),
                    go.Bar(name='Rejected', x=['Claims'], y=[trend_data.get('rejected', 0)]),
                ])
                fig.update_layout(title="Claims Status Distribution", barmode='stack')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Processing Efficiency
            fig = go.Figure(data=[go.Pie(
                labels=['Approved', 'Pending', 'Rejected'],
                values=[950, 175, 125],
                marker=dict(colors=['#28a745', '#ffc107', '#dc3545'])
            )])
            fig.update_layout(title="Claims Breakdown")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"Failed to load analytics: {error}")

# ==================== Process Claim Page ====================

elif page == "Process Claim":
    st.subheader("📋 Process Insurance Claim")
    
    with st.form("claim_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            claim_id = st.text_input("Claim ID", "CLM-2024-")
            customer_name = st.text_input("Customer Name")
            claim_type = st.selectbox(
                "Claim Type",
                ["Auto", "Health", "Property", "Life", "Travel"]
            )
        
        with col2:
            amount = st.number_input("Amount Claimed ($)", min_value=0.0, step=100.0)
            incident_date = st.date_input("Incident Date")
            description = st.text_area("Claim Description", height=100)
        
        if st.form_submit_button("🚀 Process Claim", use_container_width=True):
            with st.spinner("Processing claim with AI..."):
                payload = {
                    "claim_id": claim_id,
                    "customer_name": customer_name,
                    "claim_type": claim_type.lower(),
                    "description": description,
                    "amount_claimed": amount,
                    "incident_date": str(incident_date)
                }
                
                result, error = safe_api_call("POST", "/api/claims/process", json=payload)
                
                if result:
                    st.success("✅ Claim Processed Successfully")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Status", result.get('status', 'N/A'))
                    with col2:
                        st.metric("Confidence", f"{result.get('confidence_score', 0)*100:.0f}%")
                    with col3:
                        st.metric("Processing Time", f"{result.get('processing_time', 0):.1f}s")
                    
                    st.info(f"Recommendation: {result.get('recommendation', 'N/A')}")
                else:
                    st.error(f"Error: {error}")

# ==================== Analyze Policy Page ====================

elif page == "Analyze Policy":
    st.subheader("📑 Policy Analysis")
    
    with st.form("policy_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            policy_id = st.text_input("Policy ID", "POL-2024-")
            customer_id = st.text_input("Customer ID")
        
        with col2:
            analysis_type = st.selectbox(
                "Analysis Type",
                ["Coverage", "Risk", "Compliance", "Optimization"]
            )
            st.write("")  # Spacing
        
        if st.form_submit_button("🔍 Analyze Policy", use_container_width=True):
            with st.spinner("Analyzing policy with AI..."):
                payload = {
                    "policy_id": policy_id,
                    "customer_id": customer_id,
                    "analysis_type": analysis_type.lower()
                }
                
                result, error = safe_api_call("POST", "/api/policies/analyze", json=payload)
                
                if result:
                    st.success("✅ Analysis Complete")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Risk Score", f"{result.get('risk_score', 0):.2f}")
                    with col2:
                        st.metric("Recommendations", result.get('recommendations', 0))
                    with col3:
                        st.metric("Analysis Type", result.get('analysis_type', 'N/A').title())
                    
                    st.subheader("Findings")
                    for finding in result.get('findings', []):
                        st.info(finding)
                else:
                    st.error(f"Error: {error}")

# ==================== Extract Document Page ====================

elif page == "Extract Document":
    st.subheader("🗂️ Document Processing")
    
    uploaded_file = st.file_uploader(
        "Upload document (PDF, PNG, JPG)",
        type=["pdf", "png", "jpg", "jpeg"]
    )
    
    doc_type = st.selectbox(
        "Document Type",
        ["Claim Form", "Policy", "Receipt", "Medical Report", "Invoice"]
    )
    
    if st.button("📤 Extract & Process", use_container_width=True):
        if uploaded_file:
            with st.spinner("Processing document with AI..."):
                files = {
                    'file': (uploaded_file.name, uploaded_file.getbuffer()),
                }
                params = {'document_type': doc_type}
                
                result, error = safe_api_call(
                    "POST",
                    "/api/documents/process",
                    files=files,
                    params=params
                )
                
                if result:
                    st.success("✅ Document Processed Successfully")
                    
                    st.metric("Confidence Score", f"{result.get('confidence_score', 0)*100:.0f}%")
                    
                    st.subheader("Extracted Fields")
                    fields = result.get('extracted_fields', {})
                    for field, value in fields.items():
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.write(f"**{field.replace('_', ' ').title()}**")
                        with col2:
                            st.write(value)
                else:
                    st.error(f"Error: {error}")
        else:
            st.warning("Please upload a document first")

# ==================== Upload Record Page ====================

elif page == "Upload Record":
    st.subheader("📤 Upload Record")
    
    # Tabs for different upload methods
    tab1, tab2 = st.tabs(["📁 Upload File", "📝 Manual JSON"])
    
    # ===== File Upload Tab =====
    with tab1:
        st.info("Upload files (PDF, CSV, TXT, SQL, JSON, DOC, etc.) - They'll be automatically parsed and stored as records")
        
        uploaded_file = st.file_uploader(
            "Choose a file to upload",
            type=["pdf", "csv", "txt", "sql", "json", "doc", "docx", "xlsx", "xls"],
            help="Supported formats: PDF, CSV, TXT, SQL, JSON, DOC, DOCX, XLSX, XLS"
        )
        
        if uploaded_file is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**File**: {uploaded_file.name}")
                st.write(f"**Size**: {uploaded_file.size:,} bytes")
            
            with col2:
                file_ext = uploaded_file.name.split('.')[-1].lower()
                type_emoji = {
                    'pdf': '📄', 'csv': '📊', 'txt': '📋',
                    'sql': '🗄️', 'json': '{}', 'doc': '📑', 'docx': '📑'
                }.get(file_ext, '📎')
                st.write(f"**Type**: {type_emoji} {file_ext.upper()}")
            
            if st.button("⬆️ Upload File", key="file_upload_btn", use_container_width=True):
                with st.spinner(f"Uploading and parsing {uploaded_file.name}..."):
                    try:
                        files = {'file': (uploaded_file.name, uploaded_file.getbuffer())}
                        response = requests.post(
                            f"{API_URL}/api/records/upload-file",
                            files=files
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ {result['message']}")
                            st.info(f"Record ID: {result['record_id']}")
                            
                            # Show summary
                            with st.expander("📊 File Parsing Summary"):
                                if 'line_count' in result['summary']['parsed_info']:
                                    st.write(f"Lines: {result['summary']['parsed_info']['line_count']}")
                                if 'row_count' in result['summary']['parsed_info']:
                                    st.write(f"Rows: {result['summary']['parsed_info']['row_count']}")
                                if 'page_count' in result['summary']['parsed_info']:
                                    st.write(f"Pages: {result['summary']['parsed_info']['page_count']}")
                                if 'statement_count' in result['summary']['parsed_info']:
                                    st.write(f"SQL Statements: {result['summary']['parsed_info']['statement_count']}")
                                st.write(f"File Size: {result['summary']['size_bytes']:,} bytes")
                            
                            st.session_state.selected_record = result['record_id']
                            st.rerun()
                        else:
                            st.error(f"Error: {response.text}")
                    except Exception as e:
                        st.error(f"Upload error: {str(e)}")
    
    # ===== Manual JSON Tab =====
    with tab2:
        st.info("Manually create a record by entering JSON data")
        
        with st.form("record_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                record_id = st.text_input("Record ID", "REC-2024-")
                record_type = st.selectbox(
                    "Record Type",
                    ["Claim", "Policy", "Customer", "Document", "Invoice", "Report"]
                )
            
            with col2:
                record_name = st.text_input("Record Name")
                st.write("")  # Spacing
            
            # Record data input
            st.subheader("Record Data (JSON)")
            record_data_json = st.text_area(
                "Enter record data as JSON",
                value='{"claimAmount": 5000, "status": "submitted", "date": "2024-01-15"}',
                height=150,
                help="Enter record information in JSON format"
            )
            
            if st.form_submit_button("🚀 Upload Record", use_container_width=True):
                if not record_id or not record_name:
                    st.error("Record ID and Name are required")
                else:
                    with st.spinner("Uploading record..."):
                        try:
                            import json
                            record_data = json.loads(record_data_json)
                            
                            payload = {
                                "record_id": record_id,
                                "record_type": record_type.lower(),
                                "record_name": record_name,
                                "record_data": record_data
                            }
                            
                            result, error = safe_api_call("POST", "/api/records/upload", json=payload)
                            
                            if result:
                                st.success(f"✅ {result['message']}")
                                st.info(f"Record ID: {result['record_id']}")
                                st.session_state.selected_record = record_id
                                st.rerun()
                            else:
                                st.error(f"Error: {error}")
                        except json.JSONDecodeError:
                            st.error("Invalid JSON format. Please check your record data.")
    
    # Display uploaded records
    st.divider()
    st.subheader("📋 Uploaded Records")
    
    records, error = safe_api_call("GET", "/api/records")
    
    if records and records.get('records'):
        # Filter and sort records
        all_records = records.get('records', [])
        
        # Show statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(all_records))
        with col2:
            file_records = len([r for r in all_records if 'file_type' in r])
            st.metric("Files", file_records)
        with col3:
            json_records = len([r for r in all_records if 'file_type' not in r])
            st.metric("Manual Records", json_records)
        
        st.write("")
        
        # Display each record
        for record in all_records:
            record_icon = {
                'document': '📄',
                'dataset': '📊',
                'database': '🗄️',
                'data': '{}',
                'claim': '📋',
                'policy': '📜',
                'customer': '👤',
                'invoice': '🧾',
                'report': '📑'
            }.get(record['type'], '📎')
            
            file_type_str = f" - {record.get('file_type', 'json').upper()}" if 'file_type' in record else ""
            
            with st.expander(f"{record_icon} {record['name']}{file_type_str}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**ID**: `{record['id']}`")
                    st.write(f"**Type**: {record['type'].capitalize()}")
                    if 'file_size_bytes' in record:
                        st.write(f"**Size**: {record['file_size_bytes']:,} bytes")
                    st.write(f"**Uploaded**: {record['uploaded_at']}")
                
                with col2:
                    if st.button("📌 Select", key=f"select-{record['id']}", use_container_width=True):
                        st.session_state.selected_record = record['id']
                        st.success("Record selected for chat!")
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete-{record['id']}", use_container_width=True):
                        del_result, del_error = safe_api_call("DELETE", f"/api/records/{record['id']}")
                        if del_result:
                            st.success("Record deleted!")
                            st.rerun()
                        else:
                            st.error(f"Delete error: {del_error}")
                
                # Display document content
                st.divider()
                
                # Create tabs for different viewing modes
                content_tabs = st.tabs(["📄 Content", "📊 Metadata", "🔍 Search in Doc"])
                
                with content_tabs[0]:
                    st.subheader("Document Content")
                    
                    # Show document content based on type
                    if 'data' in record:
                        data = record['data']
                        
                        if record.get('file_type') == 'csv':
                            if 'rows' in data:
                                st.write(f"**Columns**: {', '.join(data.get('columns', []))}")
                                st.write(f"**Total Rows**: {data.get('row_count', 0)}")
                                st.write("**First few rows:**")
                                df = pd.DataFrame(data['rows'][:10])
                                st.dataframe(df, use_container_width=True)
                        
                        elif record.get('file_type') == 'text':
                            if 'content' in data:
                                st.text_area(
                                    "Text Content",
                                    value=data['content'],
                                    height=300,
                                    disabled=True,
                                    key=f"content-{record['id']}"
                                )
                                st.write(f"**Total Lines**: {data.get('line_count', 0)}")
                        
                        elif record.get('file_type') == 'json':
                            st.json(data.get('data', data))
                        
                        elif record.get('file_type') == 'pdf':
                            st.write(f"**Pages**: {data.get('page_count', 'N/A')}")
                            if 'content' in data:
                                st.text_area(
                                    "PDF Extracted Content",
                                    value=data['content'],
                                    height=300,
                                    disabled=True,
                                    key=f"pdf-content-{record['id']}"
                                )
                        
                        elif record.get('file_type') == 'sql':
                            if 'content' in data:
                                st.code(data['content'], language='sql')
                                st.write(f"**SQL Statements**: {data.get('statement_count', 0)}")
                        
                        else:
                            st.json(data)
                
                with content_tabs[1]:
                    st.subheader("Metadata")
                    metadata_cols = st.columns(2)
                    with metadata_cols[0]:
                        st.write(f"**File Type**: {record.get('file_type', 'manual')}")
                        st.write(f"**Record Type**: {record['type']}")
                    with metadata_cols[1]:
                        st.write(f"**Size**: {record.get('file_size_bytes', 'N/A')} bytes")
                        st.write(f"**Uploaded**: {record['uploaded_at']}")
                
                with content_tabs[2]:
                    st.subheader("Search in Document (RAG)")
                    search_query = st.text_input(
                        "Search query",
                        placeholder="Ask about the document content...",
                        key=f"search-{record['id']}"
                    )
                    
                    if search_query and st.button("🔍 Search", key=f"search-btn-{record['id']}"):
                        with st.spinner("Searching document..."):
                            response, error = safe_api_call(
                                "POST",
                                "/api/rag/search",
                                json={"query": search_query, "record_id": record['id'], "top_k": 3}
                            )
                            
                            if response:
                                st.success(f"Found {response.get('count', 0)} results")
                                for i, result in enumerate(response.get('results', []), 1):
                                    st.write(f"**Result {i}:**")
                                    st.text(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
                            else:
                                st.error(f"Search error: {error}")
    else:
        st.info("No records uploaded yet. Upload a record to get started!")

# ==================== Chat Support Page ====================

elif page == "Chat Support":
    st.subheader("💬 AI Chat Support with RAG")
    
    st.info("Ask questions about your insurance policy, claims, or uploaded documents - powered by RAG (Retrieval Augmented Generation)")
    
    # Display selected record info
    record_selected = False
    if st.session_state.selected_record:
        record_info, _ = safe_api_call("GET", f"/api/records/{st.session_state.selected_record}")
        if record_info and record_info.get('record'):
            record = record_info['record']
            with st.success(f"📌 Using record: **{record['name']}** ({record['type']})"):
                st.caption(f"ID: {record['id']} | Type: {record.get('file_type', 'manual')}")
            record_selected = True
    else:
        st.warning("⚠️ No record selected. Go to 'Upload Record' to upload and select a record for AI-powered answers.")
    
    # Chat settings expander
    with st.expander("⚙️ Chat Settings"):
        use_rag = st.checkbox("Use RAG (Retrieval Augmented Generation)", value=True, help="Search uploaded documents for answers")
        show_sources = st.checkbox("Show Source Documents", value=True, help="Display which documents were used")
    
    # Display conversation history
    for msg in st.session_state.conversation_history:
        if msg['role'] == 'user':
            with st.chat_message("user"):
                st.write(msg['content'])
        else:
            with st.chat_message("assistant"):
                st.write(msg['content'])
                if msg.get('record_used') and show_sources:
                    st.caption(f"Based on: {msg['record_used']}")
                if msg.get('rag_info') and show_sources:
                    with st.expander("📚 RAG Sources"):
                        for i, source in enumerate(msg.get('rag_sources', []), 1):
                            with st.container():
                                st.write(f"**Source {i}**: {source['metadata'].get('source', 'unknown')}")
                                st.text(source['content'][:300] + "...")
    
    # Chat input
    if user_message := st.chat_input("Ask me about your records or insurance..."):
        st.session_state.conversation_history.append({
            'role': 'user',
            'content': user_message
        })
        
        with st.chat_message("user"):
            st.write(user_message)
        
        with st.spinner("Thinking... (using RAG)" if record_selected and use_rag else "Thinking..."):
            # Choose endpoint based on record selection and RAG setting
            if record_selected and use_rag:
                # Use RAG query endpoint
                payload = {
                    "query": user_message,
                    "record_id": st.session_state.selected_record,
                    "top_k": 3
                }
                result, error = safe_api_call("POST", "/api/rag/query", json=payload)
                
                if result and result.get('status') == 'success':
                    response = result.get('answer', 'Unable to generate response')
                    sources = result.get('sources', [])
                    
                    st.session_state.conversation_history.append({
                        'role': 'assistant',
                        'content': response,
                        'record_used': st.session_state.selected_record,
                        'rag_info': True,
                        'rag_sources': sources
                    })
                    
                    with st.chat_message("assistant"):
                        st.write(response)
                        
                        if show_sources and sources:
                            st.divider()
                            st.subheader("📚 Retrieved Sources")
                            for i, source in enumerate(sources, 1):
                                with st.expander(f"Source {i}"):
                                    st.text(source['content'][:500])
                                    if source['metadata']:
                                        st.caption(f"From: {source['metadata'].get('source', 'unknown')}")
                else:
                    st.error(f"RAG Error: {error}")
            else:
                # Use regular chat endpoint
                payload = {
                    "message": user_message,
                    "record_id": st.session_state.selected_record if record_selected else None,
                    "context": "insurance_support"
                }
                
                endpoint = "/api/chat-with-record" if record_selected else "/api/chat"
                result, error = safe_api_call("POST", endpoint, json=payload)
                
                if result:
                    response = result.get('ai_response', 'Unable to generate response')
                    st.session_state.conversation_history.append({
                        'role': 'assistant',
                        'content': response,
                        'record_used': result.get('record_used')
                    })
                    
                    with st.chat_message("assistant"):
                        st.write(response)
                        
                        if result.get('record_used') and show_sources:
                            with st.expander("📋 Record Context Used"):
                                st.json(result.get('record_summary', {}).get('data'))
                        
                        if result.get('suggested_actions'):
                            st.divider()
                            st.subheader("Suggested Actions")
                            for action in result['suggested_actions']:
                                st.write(f"• {action}")
                else:
                    st.error(f"Error: {error}")

# ==================== Analytics Page ====================

elif page == "Analytics":
    st.subheader("📈 Advanced Analytics")
    
    tab1, tab2, tab3 = st.tabs(["Claims Metrics", "Performance", "Trends"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Claim Value", "$8,500", "-5%")
        with col2:
            st.metric("Resolution Time", "24 hours", "-3h")
        
        st.subheader("Claims by Type")
        df = pd.DataFrame({
            'Type': ['Auto', 'Health', 'Property', 'Life'],
            'Count': [450, 350, 250, 200],
            'Avg Value': [5200, 12000, 15000, 75000]
        })
        st.dataframe(df, use_container_width=True)
    
    with tab2:
        st.line_chart(pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=30),
            'Processing Time': [2.1 + i*0.02 for i in range(30)],
            'Accuracy': [0.85 + i*0.001 for i in range(30)]
        }).set_index('Date'))
    
    with tab3:
        st.bar_chart(pd.DataFrame({
            'Week': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'Claims': [280, 310, 295, 320],
            'Approvals': [215, 238, 226, 245]
        }).set_index('Week'))

# ==================== Footer ====================

st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col2:
    st.caption("Insurance AI Platform v1.0")
with col3:
    st.caption("© 2024 Enterprise Insurance Solutions")
