import streamlit as st
import sqlite3
import hashlib
import datetime
from streamlit_drawable_canvas import st_canvas
import pandas as pd
from PIL import Image
import io
import base64

# Page configuration
st.set_page_config(
    page_title="Kolam Art Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Indian aesthetic
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #ff6b35, #f7931e);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .kolam-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #fff5f0, #ffe8d6);
    }
    .stButton > button {
        background: linear-gradient(135deg, #ff6b35, #f7931e);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Database initialization
def init_db():
    conn = sqlite3.connect('kolam_art.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, created_at TEXT)''')
    
    # Artworks table
    c.execute('''CREATE TABLE IF NOT EXISTS artworks
                 (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, image_data TEXT, 
                  likes INTEGER DEFAULT 0, created_at TEXT,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Comments table
    c.execute('''CREATE TABLE IF NOT EXISTS comments
                 (id INTEGER PRIMARY KEY, artwork_id INTEGER, user_id INTEGER, 
                  comment TEXT, created_at TEXT,
                  FOREIGN KEY (artwork_id) REFERENCES artworks (id),
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

# Authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    conn = sqlite3.connect('kolam_art.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
                 (username, hash_password(password), datetime.datetime.now().isoformat()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect('kolam_art.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ? AND password = ?",
             (username, hash_password(password)))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# Artwork functions
def save_artwork(user_id, title, image_data):
    conn = sqlite3.connect('kolam_art.db')
    c = conn.cursor()
    c.execute("INSERT INTO artworks (user_id, title, image_data, created_at) VALUES (?, ?, ?, ?)",
             (user_id, title, image_data, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_artworks():
    conn = sqlite3.connect('kolam_art.db')
    c = conn.cursor()
    c.execute("""SELECT a.id, a.title, a.image_data, a.likes, a.created_at, u.username 
                 FROM artworks a JOIN users u ON a.user_id = u.id 
                 ORDER BY a.created_at DESC""")
    result = c.fetchall()
    conn.close()
    return result

def like_artwork(artwork_id):
    conn = sqlite3.connect('kolam_art.db')
    c = conn.cursor()
    c.execute("UPDATE artworks SET likes = likes + 1 WHERE id = ?", (artwork_id,))
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Main header
st.markdown("""
<div class="main-header">
    <h1>🎨 Kolam Art Studio</h1>
    <p>Create, Share, and Explore Traditional Indian Kolam Art</p>
</div>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose a page", 
                           ["🎨 Drawing Tool", "🖼️ Community Gallery", "📚 Kolam Info", "👤 Account"])

# Authentication sidebar
if st.session_state.user_id is None:
    st.sidebar.subheader("Login / Sign Up")
    auth_mode = st.sidebar.radio("Choose", ["Login", "Sign Up"])
    
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button(f"{auth_mode}"):
        if auth_mode == "Sign Up":
            if create_user(username, password):
                st.sidebar.success("Account created! Please login.")
            else:
                st.sidebar.error("Username already exists!")
        else:
            user_id = authenticate_user(username, password)
            if user_id:
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.sidebar.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials!")
else:
    st.sidebar.success(f"Logged in as: {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()

# Page content
if page == "🎨 Drawing Tool":
    st.header("Interactive Kolam Drawing Tool")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("Drawing Controls")
        drawing_mode = st.selectbox("Drawing Mode", ["freedraw", "line", "rect", "circle"])
        stroke_width = st.slider("Brush Size", 1, 25, 3)
        stroke_color = st.color_picker("Color", "#FF6B35")
        
        # Kolam pattern templates
        st.subheader("Kolam Templates")
        if st.button("Load Dot Grid"):
            st.session_state.template = "dots"
        if st.button("Load Geometric Pattern"):
            st.session_state.template = "geometric"
        if st.button("Clear Canvas"):
            st.session_state.template = "clear"
    
    with col1:
        # Drawing canvas
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_color="#FFFFFF",
            background_image=None,
            update_streamlit=True,
            height=500,
            width=700,
            drawing_mode=drawing_mode,
            key="canvas",
        )
        
        # Save artwork
        if canvas_result.image_data is not None and st.session_state.user_id:
            st.subheader("Save Your Artwork")
            artwork_title = st.text_input("Artwork Title", "My Kolam Creation")
            
            if st.button("Save Artwork"):
                # Convert image to base64
                img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                save_artwork(st.session_state.user_id, artwork_title, img_str)
                st.success("Artwork saved successfully!")
        
        elif canvas_result.image_data is not None:
            st.info("Please login to save your artwork!")

elif page == "🖼️ Community Gallery":
    st.header("Community Gallery")
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("Search artworks...")
    with col2:
        sort_by = st.selectbox("Sort by", ["Newest", "Most Liked"])
    
    # Display artworks
    artworks = get_artworks()
    
    if artworks:
        for artwork in artworks:
            artwork_id, title, image_data, likes, created_at, artist = artwork
            
            # Filter by search term
            if search_term and search_term.lower() not in title.lower() and search_term.lower() not in artist.lower():
                continue
            
            with st.container():
                st.markdown('<div class="kolam-card">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # Display image
                    try:
                        img_data = base64.b64decode(image_data)
                        img = Image.open(io.BytesIO(img_data))
                        st.image(img, width=200)
                    except:
                        st.write("Image not available")
                
                with col2:
                    st.subheader(title)
                    st.write(f"By: {artist}")
                    st.write(f"Created: {created_at[:10]}")
                    
                    col_like, col_share = st.columns(2)
                    with col_like:
                        if st.button(f"❤️ {likes}", key=f"like_{artwork_id}"):
                            like_artwork(artwork_id)
                            st.rerun()
                    
                    with col_share:
                        st.button("📤 Share", key=f"share_{artwork_id}")
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.info("No artworks yet. Be the first to create and share!")

elif page == "📚 Kolam Info":
    st.header("Learn About Kolam Art")
    
    tab1, tab2, tab3 = st.tabs(["History & Culture", "Mathematics", "Tutorials"])
    
    with tab1:
        st.subheader("The Rich History of Kolam")
        st.write("""
        Kolam is a traditional art form from Tamil Nadu, India, with a history spanning over 5,000 years. 
        These intricate geometric patterns are drawn with rice flour, chalk, or colored powders, typically 
        at the entrance of homes during dawn.
        
        **Cultural Significance:**
        - **Spiritual Protection**: Kolams are believed to bring prosperity and ward off evil spirits
        - **Daily Ritual**: Women traditionally create fresh Kolams every morning
        - **Community Bonding**: The art form strengthens neighborhood relationships
        - **Seasonal Celebrations**: Special Kolams mark festivals and important occasions
        """)
        
        st.subheader("Symbolism and Meaning")
        st.write("""
        - **Dots (Pulli)**: Represent the universe and cosmic energy
        - **Lines**: Symbolize the path of life and interconnectedness
        - **Geometric Patterns**: Reflect mathematical precision and divine order
        - **Colors**: Each color has specific meanings - red for prosperity, white for purity
        """)
    
    with tab2:
        st.subheader("Mathematics in Kolam")
        st.write("""
        Kolam art demonstrates sophisticated mathematical concepts:
        
        **Geometric Principles:**
        - Symmetry and reflection
        - Tessellation patterns
        - Fractal geometry
        - Graph theory applications
        
        **Mathematical Concepts:**
        - Prime numbers in dot arrangements
        - Fibonacci sequences in spiral patterns
        - Topology in continuous line drawings
        - Group theory in pattern transformations
        """)
        
        st.info("💡 Fun Fact: Many Kolam patterns follow mathematical rules that ensure the design can be drawn in one continuous line without lifting the hand!")
    
    with tab3:
        st.subheader("Step-by-Step Tutorials")
        
        tutorial_type = st.selectbox("Choose Tutorial Level", 
                                   ["Beginner - Basic Dots", "Intermediate - Geometric Patterns", 
                                    "Advanced - Complex Designs"])
        
        if tutorial_type == "Beginner - Basic Dots":
            st.write("""
            **Basic Dot Kolam Tutorial:**
            
            1. **Start with a grid**: Place dots in a regular pattern (3x3, 5x5, etc.)
            2. **Connect the dots**: Draw curved lines connecting adjacent dots
            3. **Create symmetry**: Ensure your pattern is balanced on all sides
            4. **Add details**: Fill in with smaller patterns or decorative elements
            5. **Practice daily**: Start with simple patterns and gradually increase complexity
            """)
            
        elif tutorial_type == "Intermediate - Geometric Patterns":
            st.write("""
            **Geometric Kolam Tutorial:**
            
            1. **Plan your design**: Sketch the basic geometric shape (hexagon, octagon)
            2. **Create the framework**: Draw the main structural lines
            3. **Add interlacing**: Weave patterns that go over and under each other
            4. **Maintain proportions**: Keep all elements balanced and proportional
            5. **Refine details**: Add finishing touches and decorative elements
            """)
            
        else:
            st.write("""
            **Advanced Complex Designs:**
            
            1. **Master the basics**: Ensure proficiency in simple patterns first
            2. **Study traditional designs**: Learn from classical Kolam books and masters
            3. **Combine patterns**: Merge different traditional motifs creatively
            4. **Experiment with colors**: Use traditional color combinations meaningfully
            5. **Document your work**: Keep a record of your creations for future reference
            """)

elif page == "👤 Account":
    if st.session_state.user_id:
        st.header(f"Welcome, {st.session_state.username}!")
        
        # User statistics
        conn = sqlite3.connect('kolam_art.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM artworks WHERE user_id = ?", (st.session_state.user_id,))
        artwork_count = c.fetchone()[0]
        
        c.execute("SELECT SUM(likes) FROM artworks WHERE user_id = ?", (st.session_state.user_id,))
        total_likes = c.fetchone()[0] or 0
        conn.close()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Artworks Created", artwork_count)
        with col2:
            st.metric("Total Likes", total_likes)
        with col3:
            st.metric("Member Since", "2024")
        
        st.subheader("Your Artworks")
        # Display user's artworks
        conn = sqlite3.connect('kolam_art.db')
        c = conn.cursor()
        c.execute("SELECT title, image_data, likes, created_at FROM artworks WHERE user_id = ? ORDER BY created_at DESC", 
                 (st.session_state.user_id,))
        user_artworks = c.fetchall()
        conn.close()
        
        if user_artworks:
            for artwork in user_artworks:
                title, image_data, likes, created_at = artwork
                with st.expander(f"{title} - {likes} likes"):
                    try:
                        img_data = base64.b64decode(image_data)
                        img = Image.open(io.BytesIO(img_data))
                        st.image(img, width=300)
                    except:
                        st.write("Image not available")
                    st.write(f"Created: {created_at}")
        else:
            st.info("You haven't created any artworks yet. Visit the Drawing Tool to get started!")
    
    else:
        st.header("Account")
        st.info("Please login to view your account information.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🎨 Kolam Art Studio - Preserving Traditional Indian Art Through Technology</p>
    <p>Made with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)



## Setup Instructions

# 1. Save the code as `app.py`
# 2. Create `requirements.txt` with the dependencies below
# 3. Install dependencies: `pip install -r requirements.txt`
# 4. Run the app: `streamlit run app.py`

# streamlit==1.28.0
streamlit-drawable-canvas==0.9.3
# Pillow==10.0.1
# pandas==2.1.1

# sqlite3


