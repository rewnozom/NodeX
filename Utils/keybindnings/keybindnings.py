# .version/shared/utils/keybindnings.py

import logging


logger = logging.getLogger(__name__)

# ------------------- Keybind_Functions to the left_menu ------------------- #

def Keybind_Ctrl_1(main_window):
    """Öppnar "first page" sektionen i vänstermenyn."""
    try:
        main_window.load_page("1_chat")
        logger.info("Loaded first page via Ctrl+1")
    except Exception as e:
        logger.error(f"Error loading first page: {e}")

def Keybind_Ctrl_2(main_window):
    """Öppnar "second page" sektionen i vänstermenyn."""
    main_window.load_page("2_script_launcher_page")

def Keybind_Ctrl_3(main_window):
    """Öppnar "third page" sektionen i vänstermenyn."""
    main_window.load_page("3_chat")

def Keybind_Ctrl_4(main_window):
    """Öppnar "fourth page" sektionen i vänstermenyn."""
    main_window.load_page("4_new_Page_Template")

def Keybind_Ctrl_5(main_window):
    """Öppnar "fifth page" sektionen i vänstermenyn."""
    main_window.load_page("5_chat")

def Keybind_Ctrl_6(main_window):
    """Öppnar "sixth page" sektionen i vänstermenyn."""
    main_window.load_page("5_new_Page_Template")

def Keybind_Ctrl_7(main_window):
    """Öppnar "seventh page" sektionen i vänstermenyn."""
    main_window.load_page("")

def Keybind_Ctrl_8(main_window):
    """Öppnar "eighth page" sektionen i vänstermenyn."""
    main_window.load_page("")

def Keybind_Ctrl_9(main_window):
    """Öppnar "ninth page" sektionen i vänstermenyn."""
    main_window.load_page("")


# ------------------- Keybind_Functions to the ai Chat ------------------- #

def Keybind_Alt_1(chat_page):
    """Växlar Prefix-1 'På/Av'"""
    chat_page.toggle_prefix(1)

def Keybind_Alt_2(chat_page):
    """Växlar Prefix-2 'På/Av'"""
    chat_page.toggle_prefix(2)

def Keybind_Alt_3(chat_page):
    """Växlar Prefix-3 'På/Av'"""
    chat_page.toggle_prefix(3)

def Keybind_Alt_4(chat_page):
    """Växlar Prefix-4 'På/Av'"""
    chat_page.toggle_prefix(4)

def Keybind_Alt_5(chat_page):
    """Växlar Prefix-5 'På/Av'"""
    chat_page.toggle_prefix(5)

def Keybind_Alt_6(chat_page):
    """Växlar Prefix-6 'På/Av'"""
    chat_page.toggle_prefix(6)

def Keybind_Alt_a(chat_page):
    """Växlar AutoG 'På/Av'"""
    chat_page.toggle_autog()

def Keybind_Shift_Enter(chat_page):
    """Infogar en ny rad i chattinmatningsfältet utan att skicka meddelandet."""
    chat_page.insert_newline()

def Keybind_Ctrl_N(main_window):
    """Öppnar en "Ny" chatt."""
    main_window.load_page("chat")

def Keybind_Alt_S(main_window):
    """Öppnar systempromptrullgardinsmenyn och fokuserar på den."""
    main_window.open_system_prompt_menu()

def Keybind_Alt_C(chat_page):
    """Rensar den aktuella chatten."""
    chat_page.clear_chat()
