import streamlit as st
import requests
import io
import time

st.set_page_config(page_title="Plagiarism Checker with Kong", page_icon="📄", layout="wide")

st.title("📄 Plagiarism Checker with Kong API Gateway")
st.markdown("Upload original and submitted text files to check for plagiarism.")
st.markdown("---")

# Sidebar with info
with st.sidebar:
    st.header("ℹ API Gateway Info")
    st.info("**Rate Limits (via Kong):**\n- 5 requests per second\n- 10 requests per minute\n- 100 requests per hour")
    st.info("**File Limits:**\n- Maximum: 10MB\n- Format: .txt (UTF-8)")
    st.markdown("---")
    st.markdown("**Kong Gateway Status:**")

    # Check Kong health
    try:
        health_check = requests.get("http://localhost:8001/status", timeout=2)
        if health_check.status_code == 200:
            st.success("Kong is running")
        else:
            st.error("Kong is not responding")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to Kong")

col1, col2 = st.columns(2)

with col1:
    original_file = st.file_uploader(" Upload Original File", type=["txt"], key="original")

with col2:
    submission_file = st.file_uploader(" Upload Submission File", type=["txt"], key="submission")

if st.button(" Check Plagiarism", type="primary", use_container_width=True):
    if not original_file or not submission_file:
        st.error(" Please upload both files before checking.")
        st.stop()

    with st.spinner(" Analyzing documents through Kong Gateway..."):
        try:
            # Read file contents
            original_content = original_file.getvalue()
            submission_content = submission_file.getvalue()

            # Display file sizes
            original_size = len(original_content) / 1024  # KB
            submission_size = len(submission_content) / 1024  # KB

            st.caption(f"Original: {original_size:.2f} KB | Submission: {submission_size:.2f} KB")

            # Check file sizes before sending
            MAX_SIZE = 10 * 1024 * 1024  # 10MB
            if len(original_content) > MAX_SIZE or len(submission_content) > MAX_SIZE:
                st.error(" One or both files exceed the 10MB size limit")
                st.stop()

            # Prepare files for request
            files = {
                "original": (original_file.name, io.BytesIO(original_content), "text/plain"),
                "submission": (submission_file.name, io.BytesIO(submission_content), "text/plain")
            }

            # Send request through Kong Gateway
            start_time = time.time()
            response = requests.post(
                "http://localhost:8000/api/plagiarism/check",
                files=files,
                timeout=30
            )
            elapsed_time = time.time() - start_time

            # Display Kong rate limit headers
            with st.sidebar:
                st.markdown("---")
                st.markdown("**Rate Limit Status:**")
                if 'X-RateLimit-Remaining-Minute' in response.headers:
                    remaining = response.headers.get('X-RateLimit-Remaining-Minute', 'N/A')
                    limit = response.headers.get('X-RateLimit-Limit-Minute', 'N/A')
                    st.metric("Remaining Requests", f"{remaining}/{limit}")

                if 'X-RateLimit-Remaining-Second' in response.headers:
                    remaining_sec = response.headers.get('X-RateLimit-Remaining-Second', 'N/A')
                    limit_sec = response.headers.get('X-RateLimit-Limit-Second', 'N/A')
                    st.metric("Per Second", f"{remaining_sec}/{limit_sec}")

            # Handle rate limiting (429)
            if response.status_code == 429:
                st.error(" **Rate Limit Exceeded (Kong Gateway)**")
                st.warning("You have exceeded the allowed request rate.")

                # Show retry information
                retry_after = response.headers.get('Retry-After', 'unknown')
                reset_time = response.headers.get('X-RateLimit-Reset', 'unknown')

                st.info(f" Retry after: {retry_after} seconds")
                st.info(f" Rate limit resets at: {reset_time}")

                # Show response body if available
                try:
                    error_data = response.json()
                    st.json(error_data)
                except:
                    st.code(response.text)
                st.stop()

            # Handle file too large (413)
            if response.status_code == 413:
                st.error(" **Request Too Large (Kong Gateway)**")
                st.warning("The request size exceeds Kong's 10MB limit.")
                st.info(" Try uploading smaller files or splitting the content.")
                st.stop()

            # Handle bad request (400)
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    st.error(f" **Bad Request:** {error_data.get('error', 'Unknown error')}")
                except:
                    st.error(f" **Bad Request:** {response.text}")
                st.stop()

            # Handle server error (500)
            if response.status_code >= 500:
                st.error("🔧 **Server Error**")
                st.code(response.text)
                st.stop()

            # Success (200)
            if response.status_code == 200:
                data = response.json()

                st.success(f" Analysis completed in {elapsed_time:.2f} seconds via Kong Gateway")
                st.markdown("---")

                # Display metrics
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Similarity Score",
                        f"{data['similarity_score'] * 100:.2f}%",
                        help="Cosine similarity between documents"
                    )

                with col2:
                    st.metric(
                        "Plagiarism Probability",
                        f"{data['probability'] * 100:.2f}%",
                        help="ML model confidence"
                    )

                with col3:
                    if data["plagiarized"]:
                        st.error("Plagiarism Detected")
                    else:
                        st.success("No Plagiarism")

                st.markdown("---")

                # Display highlighted text
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("###  Original Document")
                    st.markdown(data["highlighted_original"], unsafe_allow_html=True)

                with col2:
                    st.markdown("###  Submission Document")
                    st.markdown(data["highlighted_submission"], unsafe_allow_html=True)
            else:
                st.error(f" Unexpected HTTP Status: {response.status_code}")
                st.code(response.text)

        except requests.exceptions.ConnectionError:
            st.error(" **Connection Error**")
            st.warning("Cannot connect to Kong Gateway at http://localhost:8000")
            st.info(" Make sure Kong and Flask are both running")

        except requests.exceptions.Timeout:
            st.error("️ **Timeout Error:** Request took too long")

        except Exception as e:
            st.error(f" **Error:** {str(e)}")
            with st.expander("Show details"):
                import traceback
                st.code(traceback.format_exc())

# Footer
st.markdown("---")
st.markdown("**Protected by Kong API Gateway** | Rate Limiting & Request Size Limiting Enabled")