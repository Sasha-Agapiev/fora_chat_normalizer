import streamlit as st
import requests
import json
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Fora Travel Message Normalizer",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
.stApp {
    background-color: #faf7f2;
}
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.response-container {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: 0.5rem;
    padding: 1rem;
    margin: 1rem 0;
}
.metric-container {
    display: flex;
    justify-content: space-around;
    margin: 1rem 0;
}
.status-success {
    color: #28a745;
}
.status-error {
    color: #dc3545;
}
.stButton > button[kind="primary"]{
    background-color: #f97316;  /* orange-500 */
    border-color: #f97316;
    color: white;
}
.stButton > button[kind="primary"]:hover{
    background-color: #ea580c;  /* orange-600 */
    border-color: #ea580c;
}
.stButton > button[kind="primary"]:focus{
    box-shadow: 0 0 0 0.2rem rgba(249,115,22,.35);
}
</style>
""", unsafe_allow_html=True)

# Logo and header
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    # Add Fora logo - replace with actual logo URL
    st.image("foratravel_logo.jfif", width=200)

# Main header
st.markdown('<h1 class="main-header"> Fora Travel Message Normalizer</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666; font-size: 1.1rem;">AI-powered message classification and enrichment for travel support</p>', unsafe_allow_html=True)

# API endpoint
API_BASE_URL = "https://forachatnormalizer-production.up.railway.app"

# Sidebar with example messages
with st.sidebar:
    st.header("📝 Example Messages")
    example_messages = {
        "🚨 Emergency (Theft)": "my wallet was stolen in Paris last night",
        "⏰ Urgent (Flight)": "flight in 3 h, need assistance", 
        "📋 Contact Info": "Hi Fora, I'm Alex Smith (917-555-1234) in 10003. My client flies to Rome next week and just lost her passport—help!",
        "🏨 Hotel Booking": "I'm Jamie Lee, 310-555-0099, 94105. Staying at The St. Regis San Francisco.",
        "🗺️ Trip Planning": "planning Rome in October with a stay at Chapter Roma and maybe NYC",
        "🏥 Medical Emergency": "Client had medical emergency in London, need hospital recommendations immediately"
    }
    
    selected_example = st.selectbox("Choose an example:", list(example_messages.keys()))
    if st.button("Use Example"):
        st.session_state.selected_message = example_messages[selected_example]

# Main input area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 Enter Customer Message")
    message_text = st.text_area(
        "Message Text:",
        value=st.session_state.get('selected_message', ''),
        height=120,
        placeholder="Enter a customer support message to analyze..."
    )
    
    message_id = st.text_input("Message ID:", value=f"demo_{int(time.time())}")

with col2:
    st.subheader("🎯 API Configuration")
    st.info(f"**Endpoint:** {API_BASE_URL}/normalize")
    st.info("**Method:** POST")
    
    # Health check
    if st.button("🔍 Check API Health"):
        try:
            health_response = requests.get(f"{API_BASE_URL}/health", timeout=10)
            if health_response.status_code == 200:
                st.success("✅ API is healthy!")
                health_data = health_response.json()
                st.json(health_data)
            else:
                st.error(f"❌ API health check failed: {health_response.status_code}")
        except Exception as e:
            st.error(f"❌ API unavailable: {str(e)}")

# Process message button
st.markdown("---")
if st.button("🚀 Analyze Message", type="primary", use_container_width=True):
    if not message_text.strip():
        st.error("⚠️ Please enter a message to analyze")
    else:
        # Prepare request
        payload = {
            "message_id": message_id,
            "text": message_text
        }
        
        # Show loading state
        with st.spinner('🤖 Processing message with AI...'):
            start_time = time.time()
            
            try:
                # Make API request
                response = requests.post(
                    f"{API_BASE_URL}/normalize",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                # Display results
                if response.status_code == 200:
                    result = response.json()
                    
                    # Success metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Status", "✅ Success", delta="200 OK")
                    with col2:
                        st.metric("Response Time", f"{response_time:.2f}s", delta=f"Target: <20s")
                    with col3:
                        category = result.get('category', 'unknown')
                        st.metric("Category", category.upper(), delta=f"Risk Level")
                    
                    # Response breakdown
                    st.subheader("📊 Analysis Results")
                    
                    # Category with color coding
                    category = result.get('category', 'unknown')
                    if category == 'high_risk':
                        st.error(f"🚨 **Category:** {category.upper()}")
                    elif category == 'urgent':
                        st.warning(f"⏰ **Category:** {category.upper()}")
                    else:
                        st.info(f"📋 **Category:** {category.upper()}")
                    
                    # Extracted information
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("👤 Contact Information")
                        contact = result.get('contact')
                        if contact:
                            contact_display = {}
                            for key, value in contact.items():
                                if value:
                                    contact_display[key.replace('_', ' ').title()] = value
                            if contact_display:
                                st.json(contact_display)
                            else:
                                st.info("No contact information extracted")
                        else:
                            st.info("No contact information extracted")
                        
                        st.subheader("🏢 Entities")
                        entities = result.get('entities', [])
                        if entities:
                            for entity in entities:
                                entity_type = entity['type'].title()
                                entity_value = entity['value']
                                if entity['type'] == 'city':
                                    st.success(f"🏙️ **{entity_type}:** {entity_value}")
                                elif entity['type'] == 'hotel':
                                    st.info(f"🏨 **{entity_type}:** {entity_value}")
                                elif entity['type'] == 'restaurant':
                                    st.info(f"🍽️ **{entity_type}:** {entity_value}")
                        else:
                            st.info("No entities extracted")
                    
                    with col2:
                        st.subheader("🔧 Enrichments")
                        enrichments = result.get('enrichment')
                        if enrichments:
                            for key, value in enrichments.items():
                                if key == 'local_emergency_numbers':
                                    st.error(f"🚨 **Emergency Numbers:** {', '.join(value)}")
                                elif key == 'support_recommendations':
                                    st.info("💡 **Support Recommendations:**")
                                    if isinstance(value, dict):
                                        for rec_key, rec_value in value.items():
                                            st.write(f"• **{rec_key.replace('_', ' ').title()}:** {rec_value}")
                                else:
                                    st.write(f"• **{key.replace('_', ' ').title()}:** {value}")
                        else:
                            st.info("No enrichments available")
                    
                    # Full JSON response
                    with st.expander("🔍 View Full JSON Response"):
                        st.json(result)
                    
                    # Request details
                    with st.expander("📤 Request Details"):
                        st.code(json.dumps(payload, indent=2), language="json")
                        
                else:
                    # Error handling
                    st.error(f"❌ API Error: {response.status_code}")
                    try:
                        error_detail = response.json()
                        st.json(error_detail)
                    except:
                        st.code(response.text)
                    
                    # Show response time even for errors
                    st.metric("Response Time", f"{response_time:.2f}s")
                        
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out (>30s)")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Cannot connect to API - please check if the service is running")
            except Exception as e:
                st.error(f"💥 Unexpected error: {str(e)}")

# Footer with API info
st.markdown("---")
st.markdown("### 🔗 API Documentation")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"**Base URL:** {API_BASE_URL}")
with col2:
    st.markdown(f"**Docs:** [Interactive API Docs]({API_BASE_URL}/docs)")
with col3:
    st.markdown(f"**Health:** [Health Check]({API_BASE_URL}/health)")
