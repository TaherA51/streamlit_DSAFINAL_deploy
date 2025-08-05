import streamlit as st
import random
import subprocess
import os
from collections import deque
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests
import gdown

st.set_page_config(
    page_title="WikiRoute",
    layout="wide",
    page_icon="🔍"
)

def download_graph_from_gdrive():
    """
    Downloads graph.csv from Google Drive if it doesn't exist locally.
    """
    graph_file_path = "data/graph.csv"
    
    os.makedirs("data", exist_ok=True)
    
    if os.path.exists(graph_file_path):
        return True
    
 
    GOOGLE_DRIVE_FILE_ID = "1wGU9SajC0CSMiH1DpOMJHTaFtWunKaGC"  
    
    try:
        with st.spinner("🔄 Downloading graph data from Google Drive (first-time setup)..."):
            url = f"https://drive.google.com/uc?id={GOOGLE_DRIVE_FILE_ID}"
            gdown.download(url, graph_file_path, quiet=False)
            
            if os.path.exists(graph_file_path) and os.path.getsize(graph_file_path) > 0:
                st.success("✅ Graph data downloaded successfully!")
                return True
            else:
                st.error("❌ Download failed - file is empty or doesn't exist")
                return False
                
    except Exception as e:
        st.error(f"❌ Error downloading graph data: {str(e)}")
        
        try:
            st.info("🔄 Trying alternative download method...")
            download_url = f"https://drive.google.com/uc?export=download&id={GOOGLE_DRIVE_FILE_ID}"
            
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(graph_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if os.path.exists(graph_file_path) and os.path.getsize(graph_file_path) > 0:
                st.success("✅ Graph data downloaded successfully using fallback method!")
                return True
            else:
                st.error("❌ Fallback download also failed")
                return False
                
        except Exception as fallback_error:
            st.error(f"❌ Fallback download failed: {str(fallback_error)}")
            return False

@st.cache_data
def load_title_id_map():
    """
    Loads the mapping from page IDs to titles and vice versa from a TSV file.
    Note: This requires the 'data/top100k_id_title.tsv' file to be present.
    """
    id_to_title = {}
    title_to_id = {}
    
    data_file_path = "data/top100k_id_title.tsv"
    if not os.path.exists(data_file_path):
        st.error(f"Error: The data file '{data_file_path}' was not found.")
        return {}, {}

    try:
        with open(data_file_path, encoding="utf-8") as f:
            for line in f:
                if "\t" not in line:
                    continue
                page_id, title = line.strip().split("\t", 1)
                id_to_title[page_id] = title
                title_to_id[title] = page_id
    except Exception as e:
        st.error(f"Error reading data file: {e}")
        return {}, {}
    return id_to_title, title_to_id

# Download graph data if needed (this runs once when the app starts)
if not download_graph_from_gdrive():
    st.error("❌ Cannot proceed without graph data. Please check your Google Drive file ID and permissions.")
    st.stop()

id_to_title, title_to_id = load_title_id_map()
titles = sorted(title_to_id.keys())

st.sidebar.title("🔍 Wikipedia Pathfinder")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate to", ["Home", "About", "Predetermined Paths", "Performance Metrics"])

# Page Selection
if page == "Home":
    st.title("🔍 WikiRoute")
    st.write("Find the shortest hyperlink path between two Wikipedia articles.")

    if not titles:
        st.error("Cannot proceed. Please ensure the data file is present and correctly formatted.")
    else:
        if "src_title" not in st.session_state:
            st.session_state.src_title = titles[0]
        if "dst_title" not in st.session_state:
            st.session_state.dst_title = titles[1]
        if "path_history" not in st.session_state:
            st.session_state.path_history = deque(maxlen=10)

        # Input Form
        with st.form("path_form", clear_on_submit=False):
            st.header("Select Articles and Algorithm")

            src_title = st.session_state.get("src_title")
            dst_title = st.session_state.get("dst_title")
            
            src_index = titles.index(src_title) if src_title in titles else 0
            dst_index = titles.index(dst_title) if dst_title in titles else 1

            col1, col2 = st.columns(2)
            with col1:
                src = st.selectbox(
                    "Start article",
                    titles,
                    index=src_index,
                    key="src_select"
                )
            with col2:
                dst = st.selectbox(
                    "End article",
                    titles,
                    index=dst_index,
                    key="dst_select"
                )

            algorithm = st.selectbox(
                "Select Algorithm",
                ["Dijkstra", "Dial"],
                index=0,
            )

            col1, col2, col3 = st.columns([1,1,2])
            with col1:
                randomize = st.form_submit_button("🎲 Randomize")
            with col2:
                submit = st.form_submit_button("🔍 Find Path")

        if randomize:
            random_titles = random.sample(titles, 2)
            st.session_state.src_title = random_titles[0]
            st.session_state.dst_title = random_titles[1]
            st.rerun()

        if submit:
            st.session_state.src_title = src
            st.session_state.dst_title = dst
            
            src_id = title_to_id.get(src)
            dst_id = title_to_id.get(dst)

            if not src_id or not dst_id:
                st.error("One or both of the articles were not found in the dataset. Please enter a valid article title.")
            else:
                with st.spinner(f"🔍 Finding path from \"{src}\" to \"{dst}\" using {algorithm}..."):
                    try:
                        result = subprocess.run(
                            ["./cplusplus/pathfinder", "data/graph.csv", algorithm.lower().replace("'", "").strip(), src_id, dst_id],
                            capture_output=True, text=True, check=True
                        )
                        output = result.stdout.strip()
                    except FileNotFoundError:
                        st.error("Pathfinder executable or data file not found. Please ensure all files are in their correct locations.")
                        output = ""
                    except subprocess.CalledProcessError as e:
                        st.error(f"An error occurred while running the pathfinder program: {e.stderr}")
                        output = ""

                if "No path found" in output:
                    st.error("No path found between the selected articles.")
                elif output:
                    st.success("✅ Path found!")
                    path_lines = output.splitlines()

                    path_line = None
                    for line in path_lines:
                        if "->" in line and not line.startswith("  →") and not line.startswith("Source node"):
                            path_line = line.strip()
                            break
                    
                    if path_line is None:
                        if len(path_lines) >= 3:
                            path_line = path_lines[-3].strip()
                        elif len(path_lines) >= 2:
                            path_line = path_lines[-2].strip()
                        else:
                            st.error("Could not find path in program output")
                            with st.expander("Full Output"):
                                st.text(output)
                            st.stop()
                    
                    title_path = []
                    for node_id in path_line.split(' -> '):
                        title = id_to_title.get(node_id, f"{node_id} (Unknown)")
                        title_path.append(title)
                    
                    st.session_state.path_history.appendleft({
                        "source": src,
                        "target": dst,
                        "path": title_path,
                        "length": len(title_path) - 1,
                        "algorithm": algorithm
                    })
                    
                    with st.container():
                        st.markdown(
                            f"<div style='background-color: #0E1117; padding: 5px; "
                            f"border-radius: 10px; margin-bottom: 0px; text-align: center;'>"
                            f"<h2 style='margin: 0; font-size: 1.1rem;'>Start: {title_path[0]}</h2>"
                            f"</div>", 
                            unsafe_allow_html=True
                        )
                        
                        for i in range(1, len(title_path)-1):
                            st.markdown("<div style='text-align: center; font-size: 18px; padding: 2px;'>↓</div>", unsafe_allow_html=True)
                            st.markdown(
                                f"<div style='background-color: #0E1117; padding: 5px; "
                                f"border-radius: 8px; margin-bottom: 0px; text-align: center;'>"
                                f"<h3 style='margin: 0; font-size: 1rem;'>Step {i}: {title_path[i]}</h3>"
                                f"</div>", 
                                unsafe_allow_html=True
                            )
                        
                        if len(title_path) > 1:
                            st.markdown("<div style='text-align: center; font-size: 18px; padding: 2px;'>↓</div>", unsafe_allow_html=True)
                            st.markdown(
                                f"<div style='background-color: #0E1117; padding: 5px; "
                                f"border-radius: 10px;'>"
                                f"<h2 style='margin: 0; font-size: 1.1rem; text-align: center;'>End: {title_path[-1]}</h2>"
                                f"</div>", 
                                unsafe_allow_html=True
                            )
                    
                    st.subheader("Path Summary")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Start Article", src)
                    col2.metric("End Article", dst)
                    col3.metric("Path Length", f"{len(title_path) - 1} links")
                    
                    st.markdown("**Compact Path View:** " + " → ".join(
                        [f"**{t}**" if i == 0 or i == len(title_path)-1 else t 
                         for i, t in enumerate(title_path)]
                    ))

                    with st.expander("Full Output"):
                        st.text(output)

        if st.session_state.path_history:
            st.markdown("---")
            st.subheader("Recent Paths")
            for i, path_info in enumerate(st.session_state.path_history):
                with st.expander(f"{i+1}. {path_info['source']} → {path_info['target']} ({path_info['length']} links) [{path_info['algorithm']}]"):
                    st.markdown(f"**Start:** {path_info['path'][0]}")
                    for j in range(1, len(path_info['path'])-1):
                        st.markdown(f"↓<br>**Step {j}:** {path_info['path'][j]}", unsafe_allow_html=True)
                    if len(path_info['path']) > 1:
                        st.markdown(f"↓<br>**End:** {path_info['path'][-1]}", unsafe_allow_html=True)
                    st.markdown(f"**Algorithm:** {path_info['algorithm']}")
                    st.markdown(f"**Path:** " + " → ".join(path_info['path']))

elif page == "About":
    st.title("About WikiRoute")
    
    st.markdown("""
    ## What is WikiRoute?
    WikiRoute is a tool that finds the shortest hyperlink path between two Wikipedia articles. 
    It uses graph algorithms to navigate through the massive network of Wikipedia pages.
    
    ## How does it work?
    1. **Select two articles**: Choose a starting and ending Wikipedia article
    2. **Choose an algorithm**: Select between Dijkstra's algorithm or Dial's algorithm
    3. **Find the path**: The tool will calculate the shortest path between the articles
    
    The path is displayed as a series of steps, showing how you can navigate from the start article to the end article 
    by clicking on Wikipedia links. 
    """)
    
    st.markdown("---")
    st.header("Data Information")
    st.markdown("""
    The tool uses a subset of Wikipedia containing the top 100,000 most linked articles.
    We selected this subset from the larger set of 6 million articles.

    We parsed the Wikipedia SQL dump to extract page IDs and their corresponding titles from the main article namespace.  
    Then we extracted article-to-article link pairs from the pagelinks SQL dump.

    For each node, we calculated a simplified PageRank score using the formula:

      **score = (2 × in_degree × out_degree) / (in_degree + out_degree)**

    This harmonic mean balanced popularity and connectivity.  
    We then ranked all nodes by their score and selected the top 100,000 as the most central articles.

    The dataset includes:
    - Article IDs and titles
    - Hyperlink connections between articles
    """)
    
    st.header("Download Data")
    try:
        with open("data/top100k_id_title.tsv", "rb") as f:
            st.download_button(
                label="⬇ Download top100k_id_title.tsv",
                data=f.read(),
                file_name="top100k_id_title.tsv",
                mime="text/tab-separated-values"
            )
    except FileNotFoundError:
        st.warning("top100k_id_title.tsv not found, download button is disabled.")
    
    st.markdown("---")
    st.header("Technical Details")
    st.markdown("""
    - **Backend**: C++ for efficient pathfinding
    - **Frontend**: Streamlit for the web interface
    - **Algorithms**: 
        - Dijkstra's algorithm (standard implementation)
        - Dial's algorithm (optimized for graphs with small integer weights)
    """)
    
elif page == "Predetermined Paths":
    st.title("Predetermined Paths")
    st.markdown("""
    Explore some interesting pre-calculated paths between Wikipedia articles:
    """)
        
    st.markdown("---")
    st.subheader("Example Path")
    st.markdown("""
    Here's an example of what predetermined paths will look like:
    """)
    
    example_path = [
        "University of Florida",
        "Genetic recombination",
        "Cryptography",
        "Sub-saharan Africa",
        "Carpal tunnel syndrome"
    ]
    
    with st.container():
        st.markdown(
            f"<div style='background-color: #0E1117; padding: 5px; "
            f"border-radius: 10px; margin-bottom: 0px; text-align: center;'>"
            f"<h2 style='margin: 0; font-size: 1.1rem;'>Start: {example_path[0]}</h2>"
            f"</div>", 
            unsafe_allow_html=True
        )
        
        for i in range(1, len(example_path)-1):
            st.markdown("<div style='text-align: center; font-size: 18px; padding: 2px;'>↓</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='background-color: #0E1117; padding: 5px; "
                f"border-radius: 8px; margin-bottom: 0px; text-align: center;'>"
                f"<h3 style='margin: 0; font-size: 1rem;'>Step {i}: {example_path[i]}</h3>"
                f"</div>", 
                unsafe_allow_html=True
            )
        
        if len(example_path) > 1:
            st.markdown("<div style='text-align: center; font-size: 18px; padding: 2px;'>↓</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='background-color: #0E1117; padding: 5px; "
                f"border-radius: 10px;'>"
                f"<h2 style='margin: 0; font-size: 1.1rem; text-align: center;'>End: {example_path[-1]}</h2>"
                f"</div>", 
                unsafe_allow_html=True
            )
    
    st.markdown("---")
    st.write("Check back soon for more interesting paths!")

elif page == "Performance Metrics":
    st.title("Performance Metrics")
    st.markdown("Analyze algorithm performance and execution statistics")
    
    metrics_file = "performance_metrics.csv"
    if not os.path.exists(metrics_file):
        st.warning("No performance metrics collected yet. Run some searches on the Home page first!")
        st.stop()
    
    try:
        metrics_df = pd.read_csv(metrics_file, header=None, names=[
            "Timestamp", "Algorithm", "Source", "Target", 
            "Load Time (ms)", "Algorithm Time (ms)", "Nodes Visited",
            "Path Length", "Graph Nodes", "Graph Edges"
        ])
        
        metrics_df["Timestamp"] = metrics_df["Timestamp"].astype(str)
        
        metrics_df["Source Article"] = metrics_df["Source"].apply(
            lambda x: id_to_title.get(str(x), f"ID {x} (Unknown)"))
        metrics_df["Target Article"] = metrics_df["Target"].apply(
            lambda x: id_to_title.get(str(x), f"ID {x} (Unknown)"))
        
        valid_metrics_df = metrics_df[metrics_df["Path Length"] >= 0]
        
        with st.expander("View Raw Metrics Data"):
            st.dataframe(metrics_df)
        
        metrics_df["Datetime"] = pd.to_datetime(metrics_df["Timestamp"], errors='coerce')
        valid_metrics_df["Datetime"] = pd.to_datetime(valid_metrics_df["Timestamp"], errors='coerce')
        
        st.subheader("Summary Statistics")
        st.dataframe(metrics_df.describe())
        
        st.subheader("Performance Visualizations")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Algorithm Execution Time Comparison**")
            fig1 = px.box(valid_metrics_df, x="Algorithm", y="Algorithm Time (ms)", 
                         color="Algorithm", points="all",
                         title="Execution Time Distribution by Algorithm")
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            if not valid_metrics_df["Datetime"].isnull().all():
                st.markdown("**Data Loading Time**")
                fig2 = px.line(valid_metrics_df, x="Datetime", y="Load Time (ms)",
                              title="Graph Loading Time Over Time",
                              color="Algorithm")
                st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("**Algorithm Efficiency (Successful Paths Only)**")
        if not valid_metrics_df.empty:
            fig3 = px.scatter(valid_metrics_df, x="Nodes Visited", y="Algorithm Time (ms)",
                             color="Algorithm", size="Path Length",
                             hover_data=["Source Article", "Target Article"],
                             title="Nodes Visited vs Execution Time")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning("No successful paths to display")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Path Length Distribution**")
            fig4 = px.histogram(valid_metrics_df, x="Path Length", color="Algorithm",
                               marginal="rug", nbins=20,
                               title="Distribution of Path Lengths")
            st.plotly_chart(fig4, use_container_width=True)
        
        with col2:
            st.markdown("**Path Length vs Execution Time**")
            if not valid_metrics_df.empty:
                fig5 = px.scatter(valid_metrics_df, x="Path Length", y="Algorithm Time (ms)",
                                 color="Algorithm", 
                                 hover_data=["Source Article", "Target Article"],
                                 title="Path Length vs Execution Time")
                st.plotly_chart(fig5, use_container_width=True)
            else:
                st.warning("No successful paths to display")
        
        st.subheader("Top 10 Longest Executions")
        longest_executions = metrics_df.nlargest(10, "Algorithm Time (ms)")
        st.dataframe(longest_executions[["Timestamp", "Algorithm", "Source Article", "Target Article", 
                                       "Algorithm Time (ms)", "Nodes Visited", "Path Length"]])
        
        st.subheader("Algorithm Performance Comparison")
        algo_comparison = metrics_df.groupby("Algorithm").agg({
            "Algorithm Time (ms)": ["mean", "median", "min", "max"],
            "Nodes Visited": ["mean", "median"],
            "Path Length": ["mean", "median"]
        }).reset_index()
        st.dataframe(algo_comparison)
        
        if not metrics_df["Datetime"].isnull().all():
            st.subheader("Performance Over Time")
            fig6 = px.line(metrics_df, x="Datetime", y="Algorithm Time (ms)",
                          color="Algorithm", markers=True,
                          title="Algorithm Execution Time Over Time")
            st.plotly_chart(fig6, use_container_width=True)
        
        st.markdown("---")
        st.warning("Clearing metrics will permanently delete all collected performance data.")
        if st.button("Clear All Metrics Data", type="primary"):
            try:
                os.remove(metrics_file)
                st.success("Metrics data cleared successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error clearing metrics: {e}")
                
    except Exception as e:
        st.error(f"Error loading performance metrics: {e}")

        st.error("Please ensure the CSV file format matches the expected structure.")
