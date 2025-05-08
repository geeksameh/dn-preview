import cadquery as cq
import streamlit as st
import os
import sys
from pathlib import Path
import time
from streamlit_stl import stl_from_file

if 'text1' not in st.session_state:
    st.session_state.text1 = "STOP"
if 'text2' not in st.session_state:
    st.session_state.text2 = "WORK"

SPECIAL_CHARS = ['♥','♦','♣','♠','♪','♫','►','◄']

def get_fonts_path():
    """Get the absolute path to the resource, works for both development and PyInstaller bundle."""
    try:
        # PyInstaller stores files in a temporary folder _MEIPASS
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Development mode
        base_path = Path(__file__).parent.parent

    return base_path / 'fonts'

def letter(let, angle, fontPath=""):
    """Extrude a letter, center it and rotate of the input angle"""
    wp = (cq.Workplane('XZ')
        .text(let, fontsize, extr, fontPath=fontPath, valign='bottom')
        )
    b_box = wp.combine().objects[0].BoundingBox()
    x_shift = -(b_box.xlen/2 + b_box.xmin )
    wp = (wp.translate([x_shift,extr/2,0])
        .rotate((0,0,0),(0,0,1),angle)
        )
    return wp


def dual_text(text1, text2, fontPath='', 
              save='stl', 
              b_h=2, b_pad=2, b_fil_per=0.8, space_per=0.3, 
              extrab_h=1, extrab_rad=2, extrab_mask='',
              export_name='file'):
    """Generate the dual letter illusion from the two text and save it"""
    space = fontsize*space_per # spece between letter
    res = cq.Assembly() # start assembly
    last_ymax = 0
    for ind, ab in enumerate(zip(text1, text2)):
        try:
            a = letter(ab[0], 45, fontPath=fontPath)
            b = letter(ab[1], 135, fontPath=fontPath,)
            a_inter_b = a & b
            b_box = a_inter_b.objects[0].BoundingBox()
            translate_vect = [0, -b_box.ymin, 0]
            if ind:
                translate_vect[1] += last_ymax + space
            a_inter_b = a_inter_b.translate(translate_vect)
            last_ymax = a_inter_b.objects[0].BoundingBox().ymax
            res.add( a_inter_b) # add the intersection to the assebmly
            if extrab_mask and len(extrab_mask) > ind and extrab_mask[ind] != '_':
                res.add(cq.Workplane('XY')
                        .circle(extrab_rad//2)
                        .extrude(extrab_h)
                        .translate(translate_vect)
                        )
        except:
            last_ymax += space*1.5

    b_box = res.toCompound().BoundingBox() # calculate the bounding box
    # add the base to the assembly
    res.add(cq.Workplane()
            .box(b_box.xlen+b_pad*2, b_box.ylen+b_pad*2, b_h, centered=(1,0,0))
            .translate([0, -b_pad, -b_h])
            .edges('|Z')
            .fillet(b_box.xlen/2*b_fil_per)
            )
    # convert the assemly to a shape and center it
    res = res.toCompound()
    res = res.translate([0, -b_box.ylen/2,0])
    # export the files
    cq.exporters.export(res, f'file_display.stl')
    cq.exporters.export(res, f"{export_name}.{save}")


if __name__ == "__main__":
    st.set_page_config(page_title="TextTango", page_icon="random", layout="wide", initial_sidebar_state="collapsed")
    for file in os.listdir():
        if 'file' in file:
            try:
                os.remove(file)
            except:
                print(f'Cannot remove file {file}')

                params = st.experimental_get_query_params()
if 'text1' in params and 'text2' in params:
    t1 = params['text1'][0].upper()
    t2 = params['text2'][0].upper()
    # force equal length check or pad/truncate
    if len(t1)!=len(t2): st.error("Length mismatch"); st.stop()
    # render immediately
    dual_text(t1, t2,
              fontPath=str(font_path),
              save='stl',  # or whatever
              export_name=f"{t1}_{t2}")
    stl_from_file('file_display.stl')
    st.stop()  # skip the manual UI below

    st.title('TextTango: Dual Letter Illusion')


    col1, col2, col3 = st.columns(3)
    # Input type
    with col1:
        text1 = st.text_input('First text', value=st.session_state.text1, key='text1_input')
        st.session_state.text1 = text1  # Update session state
        special_chars1 = st.columns(8)
        for i, char in enumerate(SPECIAL_CHARS):
            with special_chars1[i]:
                if st.button(char, key=f"btn1_{char}"):
                    st.session_state.text1 += char
                    st.rerun()
    with col2:
        text2 = st.text_input('Second text', value=st.session_state.text2, key='text2_input')
        st.session_state.text2 = text2  # Update session state
        special_chars2 = st.columns(8)
        for i, char in enumerate(SPECIAL_CHARS):
            with special_chars2[i]:
                if st.button(char, key=f"btn2_{char}"):
                    st.session_state.text2 += char
                    st.rerun()
    with col3:
        fontsize = st.number_input('Font size', min_value=1, max_value=None, value=20)
        extr = fontsize*2 # extrude letter

    if len(text1) != len(text2):
        st.warning("The two texts don't have the same length, letters in excess will be cut", icon="⚠️")
    if not text1.isupper() or not text2.isupper():
        st.warning("Non-capital letters with different height lead to bad results", icon="⚠️")

    col1, col2, col3 = st.columns(3)
    # Input type 
    font_dir = get_fonts_path()
    fonts = [f for f in os.listdir(font_dir) if '.' != f[0]]
    with col1:
        font_name = st.selectbox('Select font', ['lato'] + sorted(fonts))
    with col2:
        font_type_list = [f for f in os.listdir(font_dir / font_name) if '.ttf' in f and '-' in f]
        # font with explicit type (-bold, -regular, ...)
        if font_type_list:
            font_start_name = font_type_list[0].split('-')[0]
            font_type_list_name = [f.split('-')[1].strip('.ttf') for f in font_type_list]
            font_type = st.selectbox('Font type', sorted(font_type_list_name))
            font_type_pathname = font_start_name + '-' + font_type + '.ttf'
            font_path = font_dir / font_name / font_type_pathname
        else: # font without explicit type
            font_type_list = [f for f in os.listdir(font_dir / font_name) if '.ttf' in f]
            font_type = st.selectbox('Font type', sorted(font_type_list))
            font_path = font_dir / font_name / font_type
    with col3:
        space = st.slider('Letters space (%)', 0, 200, step=1, value=30) / 100
    # base parameters
    col1, col2, col3 = st.columns(3)
    with col1:
        b_h = st.slider('Base height', 0.0, float(fontsize)/2, step=0.1, value=1.0)
    with col2:
        b_pad = st.slider('Base Padding', 0.0, float(fontsize)/2, step=0.1, value=2.0)
    with col3:
        b_fil_per = st.slider('Base fillet (%)', 0, 100, step=1, value=80) / 100

    # add base mask
    extra_mask = ''
    extrab_h = 0
    extrab_rad = 0
    if st.toggle('Add extra base for letters', value=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            default_mask = ''.join(['_' if i > 0 else 'X' for i in range(len(text1))])
            extra_mask = st.text_input('Text mask', value=default_mask,
                                       help="The underscore '_' means no extra base is added, the 'X' means an extra base is added at the corresponding letter position")
            if len(extra_mask) != len(text1):
                st.warning("The mask must have the same length as the text", icon="⚠️")
        with col2:
            extrab_h = st.slider('Height', 0.0, float(fontsize), step=0.1, value=1.0)
        with col3:
            extrab_rad = st.slider('Radius', 0.0, float(fontsize), step=0.1, value=2.0)


    col1, _, _ = st.columns(3)
    with col1:
        out = st.selectbox('Output file type', ['stl', 'step'])
            

    if st.button('Render'):
        start = time.time()
        with st.spinner('Wait for it...'):
            dual_text(text1, text2, fontPath=str(font_path), save=out, 
                      b_h=b_h, b_pad=b_pad, b_fil_per=b_fil_per, space_per=space,
                        extrab_h=extrab_h, extrab_rad=extrab_rad, extrab_mask=extra_mask)
        end = time.time()
        if f'file.{out}' not in os.listdir():
            st.error('The program was not able to generate the mesh.', icon="🚨")
        else:
            st.success(f'Rendered in {int(end-start)} seconds', icon="✅")
            with open(f'file.{out}', "rb") as file:
                btn = st.download_button(
                        label=f"Download {out}",
                        data=file,
                        file_name=f'TextTango_{text1}_{text2}.{out}',
                        mime=f"model/{out}"
                    )

            # stl preview
            stl_from_file('file_display.stl')

