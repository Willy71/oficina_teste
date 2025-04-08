import streamlit as st
import pandas as pd
import webbrowser
from datetime import datetime

# Colocar nome na pagina, icone e ampliar a tela
st.set_page_config(
    page_title="Contact",
    page_icon=":house",
    layout="wide"
)

# We reduced the empty space at the beginning of the streamlit
reduce_space ="""
            <style type="text/css">
            /* Remueve el espacio en el encabezado por defecto de las apps de Streamlit */
            div[data-testid="stAppViewBlockContainer"]{
                padding-top:30px;
            }
            </style>
            """
# We load reduce_space
st.markdown(reduce_space, unsafe_allow_html=True)

page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] > .main {{
background-image: url("https://github.com/Willy71/oficina/blob/main/pictures/wallpaper%20black%20vintage.jpg?raw=true");
background-size: 180%;
background-position: top left;
background-repeat: repeat;
background-attachment: local;
}}

[data-testid="stHeader"] {{
background: rgba(0,0,0,0);
}}

[data-testid="stToolbar"] {{
right: 2rem;
}}

[data-testid="stSidebar"] {{
background: rgba(0,0,0,0);
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)


def centrar_imagen(imagen, ancho):
    # Aplicar estilo CSS para centrar la imagen con Markdown
    st.markdown(
        f'<div style="display: flex; justify-content: center;">'
        f'<img src="{imagen}" width="{ancho}">'
        f'</div>',
        unsafe_allow_html=True
    )

def centrar_texto(texto, tamanho, color):
    st.markdown(f"<h{tamanho} style='text-align: center; color: {color}'>{texto}</h{tamanho}>",
                unsafe_allow_html=True)

def photo_link(alt_text, img_url, link_url, img_width):
    markdown_code = f'<a href="{link_url}" target="_blank"><img src="{img_url}" alt="{alt_text}" width="{img_width}"></a>'
    st.markdown(markdown_code, unsafe_allow_html=True)

centrar_texto("Guillermo Cerato", 2, "white")
        
with st.container():    
    col30, col31, col32, col33, col34, col35 = st.columns(6)
    with col32:
        photo_link("Whatsapp", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/WhatsApp.svg/120px-WhatsApp.svg.png", "https://wa.me/5542988736508", "50px")
    with col33:
        centrar_texto("Whatsapp", 4, "white")

        
with st.container():    
    col10, col11, col12, col13, col14, col15 = st.columns(6)
    with col12:
        photo_link("Instagram", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Instagram_logo_2022.svg/150px-Instagram_logo_2022.svg.png", "https://www.instagram.com/willycerato", "50px")
    with col13:
        centrar_texto("Instagram", 4, "white")





