# - stdlib imports -
import colorsys
from datetime import timedelta
import io
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import tkinter as tk
from tkinter import colorchooser, messagebox
import traceback
import webbrowser

if getattr(sys, 'frozen', False):
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    os.add_dll_directory(bundle_dir)

# - 3rd party imports -
import cairosvg
import lucide
from PIL import Image
import pygame
from pygame import draw, gfxdraw, transform
import pystray
import win32api
import win32con
import win32gui

# cairosvg, lucide, PIL, pygame, pystray, win32api, win32con, win32gui

# - local app imports -
import school_schedule

pygame.init()
pygame.font.init()

APP_VERSION = "1.0.0"

# <--== HELPER FUNCTIONS ==-->
def lerp(start, end, t):
    return start + (end - start) * t

def lerp_hue(h1, h2, t):
    diff = h2 - h1
    if diff > 0.5:
        h1 += 1.0
    elif diff < -0.5:
        h2 += 1.0
    
    return lerp(h1, h2, t) % 1.0

def lerp_color(color1_rgb, color2_rgb, t):
    r1, g1, b1 = [x / 255.0 for x in color1_rgb]
    r2, g2, b2 = [x / 255.0 for x in color2_rgb]
    
    rgb_lerp_r = lerp(r1, r2, t)
    rgb_lerp_g = lerp(g1, g2, t)
    rgb_lerp_b = lerp(b1, b2, t)
    
    h1, s1, v1 = colorsys.rgb_to_hsv(r1, g1, b1)
    h2, s2, v2 = colorsys.rgb_to_hsv(r2, g2, b2)
    
    if s1 == 0 or v1 == 0: h1 = h2
    if s2 == 0 or v2 == 0: h2 = h1
        
    h_blend = lerp_hue(h1, h2, t)
    s_blend = lerp(s1, s2, t)
    v_blend = lerp(v1, v2, t)
    
    hsv_lerp_r, hsv_lerp_g, hsv_lerp_b = colorsys.hsv_to_rgb(h_blend, s_blend, v_blend)
    
    final_r = (1.3 * rgb_lerp_r + 0.7 * hsv_lerp_r) / 2.0
    final_g = (1.3 * rgb_lerp_g + 0.7 * hsv_lerp_g) / 2.0
    final_b = (1.3 * rgb_lerp_b + 0.7 * hsv_lerp_b) / 2.0
    
    return (round(final_r * 255), round(final_g * 255), round(final_b * 255))

# <--== CLASSES ==-->
def get_resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return Path(base_path) / relative_path

LOCAL_APP_DIR = Path(os.path.expandvars(r"%localappdata%\WHSSchoolScheduleManager"))

class Config:
    CONFIG_PATH = LOCAL_APP_DIR / "config.json"
    FALLBACK_CONFIG_PATH = LOCAL_APP_DIR / "default.config.json"
    
    def __init__(self):
        with open(Config.FALLBACK_CONFIG_PATH, "r") as file:
            self.fallback_config = json.load(file)
        
        # schema test 1
        if "scroll_speed" not in self.fallback_config["ui_config"]:
            self.fallback_config["ui_config"]["scroll_speed"] = "0.7"
            json.dump(self.fallback_config, open(Config.FALLBACK_CONFIG_PATH, "w"), indent=4)
        
        self.config_open = False
        
        self.config_buttons = []
        self.config_scroll = 0
        
        self.config = self.read_from_file()

        self.save()
    
    def read_from_file(self):
        try:
            with open(Config.CONFIG_PATH, "r") as file:
                c = json.load(file)

                for key, item in self.fallback_config["ui_config"].items():
                    if key not in c["ui_config"]:
                        c["ui_config"][key] = item
        except Exception as e:
            traceback_lines = traceback.format_exception(e)
            traceback_string = "".join(traceback_lines)

            root = tk.Tk()
            root.title("Error Validating Configuration File")
            root.geometry("600x300")
            
            root.attributes('-topmost', True)
            
            text_widget = tk.Text(root, wrap="word", padx=10, pady=10, height=15)
            text_widget.insert("1.0", "There was an error reading your configuration file. It is likely corrupted, or a mistake was made while editing the file directly. Reverting to default values.\n\nSomething unexpected happened. Paste the below into a bug report form.\n\n" + traceback_string)
            text_widget.config(state="disabled") 
            text_widget.pack(expand=False, fill="both")
            
            button_frame = tk.Frame(root)
            button_frame.pack(pady=5)
            
            close_btn = tk.Button(button_frame, text="Ok.", command=root.destroy, width=10)
            close_btn.pack(side="left", padx=5)
            
            try:
                root.mainloop()
            except KeyboardInterrupt:
                root.destroy()
            
            return self.fallback_config
        
        return c
    
    def show_config_warning(self, e, text):
        traceback_lines = traceback.format_exception(e)
        traceback_string = "".join(traceback_lines)
        
        root = tk.Tk()
        root.title("An Exception has occured!")
        root.geometry("400x300")
        
        root.attributes('-topmost', True)
        
        text_widget = tk.Text(root, wrap="word", padx=10, pady=10, height=15)
        text_widget.insert("1.0", text + "\n\nSomething unexpected happened. Either edit the configuration file directly or click Edit Style in the config to change it back.\n\n" + traceback_string)
        text_widget.config(state="disabled") 
        text_widget.pack(expand=False, fill="both")
        
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)
        
        close_btn = tk.Button(button_frame, text="Ok.", command=root.destroy, width=10)
        close_btn.pack(side="left", padx=5)
        
        try:
            root.mainloop()
        except KeyboardInterrupt:
            root.destroy()
    
    def save(self):
        try:
            WindowHandler.DEFAULT_ALPHA_VALUE = int(self.config["ui_config"]["default_transparency"])
        except:
            pass
        try:
            float(self.config["ui_config"]["scroll_speed"])
        except Exception as e:
            self.show_config_warning(e, "You have set the scroll speed multiplier to a non-float / non-decimal value. Reverting to default scroll speed 1.3.")
            self.config["ui_config"]["scroll_speed"] = 1.3
        try:
            int(self.config["ui_config"]["width"])
        except Exception as e:
            self.show_config_warning(e, "You have set the window width to a non-integer value. Reverting to default window width 376")
            self.config["ui_config"]["width"] = 376
        try:
            int(self.config["ui_config"]["height"])
        except Exception as e:
            self.show_config_warning(e, "You have set the window height to a non-integer value. Reverting to default window height 94.")
            self.config["ui_config"]["height"] = 94
        with open(Config.CONFIG_PATH, "w") as file:
            json.dump(self.config, file, indent=4)

config = Config()

# - ui styling -
class Layout:
    EXPANSION_FACTOR = 4
    DEFAULT_WIDTH = int(config.fallback_config["ui_config"]["width"])
    DEFAULT_HEIGHT = int(config.fallback_config["ui_config"]["height"])
    
    def __init__(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self.width = int(config.config["ui_config"]["width"])
        self.collapsed_height = int(config.config["ui_config"]["height"])
        self.expanded_height = self.collapsed_height * Layout.EXPANSION_FACTOR
        self.current_height = self.collapsed_height
        self.height_target = self.collapsed_height
        
        # - window hover info -
        self.mouse_hovered = False
        self.hovered_since = None
        self.hovered_percent = 0
        
        self._calculate_dependent_properties()

    def _calculate_dependent_properties(self):
        self.class_circle_radius = round(self.collapsed_height * 31 / 94)
        self.class_icon_radius = self.class_circle_radius // 2 + 1
        self.class_progress_bar_height = self.class_circle_radius
        self.class_progress_bar_offset = (self.collapsed_height // 2 - self.class_progress_bar_height // 2) * 0.7
        self.class_progress_bar_radius = 5
        
        self.border_radius = round(self.collapsed_height * 13 / 94)
        self.border_width = round(self.collapsed_height * 3 / 94)
        
        self.top_button_padding = round(self.expanded_height * 8 / 470)
        self.top_button_height = round(self.expanded_height * 42 / 470)
        self.top_button_border = round(self.expanded_height * 2 / 470)
        self.top_button_icon_radius = round(self.expanded_height * 13 / 470)
        
        self.font_factor = (1 / 94 * self.collapsed_height)
        
        try:
            resources.reload_all()
        except NameError:
            pass

    def update(self, width=None, height=None):
        width = int(config.config["ui_config"]["width"]) if width is None else width
        height = (int(config.config["ui_config"]["height"]) * Layout.EXPANSION_FACTOR) if height is None else height
        self.height_target = self.height_target == self.collapsed_height
        self.width = width
        self.collapsed_height = height // Layout.EXPANSION_FACTOR
        self.expanded_height = height
        self.height_target = self.collapsed_height if self.height_target else self.expanded_height

        self._calculate_dependent_properties()
    
    def update_hover(self):
        if prev_mouse_hovered:
            if self.hovered_percent < 1:
                if not self.mouse_hovered:
                    if self.hovered_since is not None and time.time() - self.hovered_since < 1:
                        self.hovered_since = 2 * time.time() - self.hovered_since - 1
                    else:
                        self.hovered_since = time.time()
                    self.mouse_hovered = True
                self.hovered_percent = min(1.0, time.time() - self.hovered_since)
                if self.hovered_percent >= 1.0:
                    layout.height_target = layout.expanded_height
        else:
            if self.hovered_since is not None and self.mouse_hovered:
                if time.time() - self.hovered_since < 1:
                    self.hovered_since = 2 * time.time() - self.hovered_since - 1
                else:
                    self.hovered_since = time.time()
            self.mouse_hovered = False
            if self.hovered_percent > 0:
                self.hovered_percent = 1 - min(1.0, time.time() - self.hovered_since)
                if self.hovered_percent <= 0:
                    layout.height_target = layout.collapsed_height
                    self.hovered_since = 0
                    return True
        return False

layout = Layout()

# - window handler -
class WindowHandler:
    WINDOW_NAME = "School Schedule Manager"
    COLOR_KEY = win32api.RGB(255, 0, 255)
    try:
        DEFAULT_ALPHA_VALUE = int(config.config["ui_config"]["default_transparency"])
    except Exception as e:
        traceback_lines = traceback.format_exception(e)
        traceback_string = "".join(traceback_lines)
        
        root = tk.Tk()
        root.title("An Exception has occured!")
        root.geometry("400x300")
        
        root.attributes('-topmost', True)
        
        text_widget = tk.Text(root, wrap="word", padx=10, pady=10, height=15)
        text_widget.insert("1.0", "You have set the default transparency to a non-integer value. Reverting to default alpha 200.\n\nSomething unexpected happened. Either edit the configuration file directly or click Edit Style in the config to change it back.\n\n" + traceback_string)
        text_widget.config(state="disabled") 
        text_widget.pack(expand=False, fill="both")
        
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)
        
        close_btn = tk.Button(button_frame, text="Ok.", command=root.destroy, width=10)
        close_btn.pack(side="left", padx=5)
        
        try:
            root.mainloop()
        except KeyboardInterrupt:
            root.destroy()
        DEFAULT_ALPHA_VALUE = 200
    
    def __init__(self):
        self.monitor_width, self.monitor_height = pygame.display.get_desktop_sizes()[0]
        self.screen = pygame.Window(WindowHandler.WINDOW_NAME, size=(layout.width, layout.current_height), position=(6, self.monitor_height - 54 - layout.current_height), borderless=True, always_on_top=True)
        self.hwnd = self.screen.handle
        
        self.app_state = {
                "window_shown": True,
                "window_state": "default", # default, temp_show, temp_hide,
                "clickthrough": True,
                "window_alpha": WindowHandler.DEFAULT_ALPHA_VALUE
            }
        
        win_layout = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, win_layout | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | 0x00000080)
        self.set_window_alpha()
        
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED)
        
        os.environ["SDL_MOUSE_FOCUS_CLICKTHROUGH"] = "1"
        
        # - system tray initialization -
    
        show_window_menuitem = pystray.MenuItem("Show Window", self.show_window, enabled=lambda item: not self.app_state["window_shown"])
        hide_window_menuitem = pystray.MenuItem("Hide Window", self.hide_window, enabled=lambda item: self.app_state["window_shown"])

        menu = pystray.Menu(
            show_window_menuitem,
            hide_window_menuitem,
            pystray.MenuItem("Quit Application", self.quit_pressed)
        )

        self.icon = self.tray_icon(menu)
        self.icon.run_detached()
    
    def get_surface(self):
        return self.screen.get_surface()
    
    # - system tray icon -
    
    def tray_icon(self, menu):
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))

        svg_code = lucide.lucide_icon("clock", stroke="white", stroke_width=3, width=54, height=54)
        png_data = cairosvg.svg2png(bytestring=svg_code.encode("utf-8"))
        icon_image = Image.open(io.BytesIO(png_data)).convert("RGBA")
        
        image.paste(icon_image, (5, 5), icon_image)

        return pystray.Icon("school_schedule_manager", image, "School Schedule Manager", menu)

    # - window resize -
    
    def trigger_resize(self):
        _, _, (cur_x, cur_y) = win32gui.GetCursorInfo()
        win_x, win_y = self.screen.position
        
        bottom_y = win_y + round(layout.current_height)
        
        new_w = min(max(126, cur_x - win_x), self.monitor_width)
        new_h = min(max(94, bottom_y - cur_y), self.monitor_height)
        
        layout.update(new_w, new_h)

    # - window properties -

    def show_window(self, icon=None, item=None):
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
        self.app_state["window_shown"] = True

    def hide_window(self, icon=None, item=None):
        win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)
        self.app_state["window_shown"] = False
        config.config_open = False
    
    def reset_state(self):
        self.show_window()
        self.app_state["window_state"] = "default"
        self.set_window_alpha()
        self.set_window_clickthrough(True)
        config.config_open = False
    
    def set_window_clickthrough(self, enabled=None):
        current_layout = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        enabled = (not self.app_state["clickthrough"]) if enabled is None else enabled
        if enabled:
            new_layout = current_layout | win32con.WS_EX_TRANSPARENT
        else:
            new_layout = current_layout & ~win32con.WS_EX_TRANSPARENT
            
        self.app_state["clickthrough"] = enabled
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, new_layout)
    
    def set_window_alpha(self, alpha_value=None):
        alpha_value = WindowHandler.DEFAULT_ALPHA_VALUE if alpha_value is None else alpha_value
        self.app_state["window_alpha"] = alpha_value
        win32gui.SetLayeredWindowAttributes(self.hwnd, WindowHandler.COLOR_KEY, alpha_value, win32con.LWA_COLORKEY | win32con.LWA_ALPHA)

    # - quit handlers -

    def quit_all(self):
        pygame.quit()
        self.icon.stop()
        sys.exit()
        
    def quit_pressed(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))

window = WindowHandler()
ds = window.get_surface()

clock = pygame.time.Clock()

# - school schedule manager -
schedule = school_schedule.ScheduleManager()
schedule.reload("custom", config.config)

# - resource manager -
class ResourceManager:
    def __init__(self):
        self.top_icon_surfaces = {}
        self.top_text_surfaces = {}
        self.top_buttons = []
        
        self.special_surfaces = {}
        
    def reload_all(self):
        self.reload_fonts()
        self.reload_icons()
        self.reload_texts()
        
        self.reload_top_buttons()
        self.reload_config_icons()
        self.reload_special_surfaces()
    
    # - special surfaces -
    def reload_special_surfaces(self):
        fls = self.font_15.get_linesize()
        surf = pygame.Surface((fls, fls), pygame.SRCALPHA)
        for i in range(fls):
            draw.rect(surf, config.config["ui_config"]["bg_color"] + [min(round(255*i/fls), 255),], (i, 0, i+1, fls))
        self.special_surfaces["text_gradient"] = transform.smoothscale(surf, (fls*2, fls))
        self.special_surfaces["top_gradient"] = transform.smoothscale(transform.rotate(surf, 90), (layout.width, fls*1.5))
        self.special_surfaces["bottom_gradient"] = transform.rotate(self.special_surfaces["top_gradient"], 180)
        
    # - config icons -
    def reload_config_icons(self):
        for icon in config.config_buttons:
            icon.reload()
        
    # - top buttons -
    def reload_top_buttons(self):
        for top_button in self.top_buttons:
            top_button.reload()
    
    # - text Surfaces & fonts -
    def reload_fonts(self):
        font_path = get_resource_path("JetBrainsMono-Medium.ttf")
        
        self.font_15 = pygame.font.Font(font_path, round(15 * layout.font_factor))
        self.font_17 = pygame.font.Font(font_path, round(17 * layout.font_factor))
        self.font_20 = pygame.font.Font(font_path, round(20 * layout.font_factor))
    
    def reload_texts(self):
        self.top_text_surfaces["show"] = resources.font_15.render("Focus", True, config.config["ui_config"]["text_color"])
        self.top_text_surfaces["hide"] = resources.font_15.render("Hide (10s)", True, config.config["ui_config"]["text_color"])
        self.top_text_surfaces["settings"] = resources.font_15.render("Settings", True, config.config["ui_config"]["text_color"])
        self.top_text_surfaces["exit_settings"] = resources.font_15.render("Exit Settings", True, config.config["ui_config"]["text_color"])

    # - Lucide icons -
    def reload_icons(self):
        # - course icons -
        for course in schedule.schedule.courses:
            course.load_icon(self.load_icon(course.icon, layout.class_icon_radius), self.load_icon(course.icon, round(layout.class_icon_radius / 2)))
        
        # - top icon surfaces -
        self.top_icon_surfaces["show"] = self.load_icon("mouse-pointer-click", layout.top_button_icon_radius)
        self.top_icon_surfaces["hide"] = self.load_icon("panel-bottom-close", layout.top_button_icon_radius)
        self.top_icon_surfaces["settings"] = self.load_icon("settings", layout.top_button_icon_radius)
        self.top_icon_surfaces["exit_settings"] = self.load_icon("log-out", layout.top_button_icon_radius)

    def load_icon(self, icon_name, radius, color=(255, 255, 255)):
        r, g, b = color
        svg_string = lucide.lucide_icon(icon_name, stroke=f"#{r:02x}{g:02x}{b:02x}", width=radius * 2, height=radius * 2)
        svg_bytes = io.BytesIO(svg_string.encode("utf-8"))
        return pygame.image.load(svg_bytes, "svg").convert_alpha()

resources = ResourceManager()

# <--== UI HANDLERS & RENDERERS ==-->

# - render handler -
class RenderHandler:
    def render_basic_texts():
        # - draw primary texts -
        next_class_text = resources.font_15.render("Next Class: ", True, config.config["ui_config"]["text_color"], config.config["ui_config"]["bg_color"])
        ds.blit(next_class_text, (layout.collapsed_height * 0.9, layout.collapsed_height * 0.92 - next_class_text.height + base_y))
        
        next_class_name_text = resources.font_15.render(current.next_class.course.name, True, current.next_class.course.accent_color, config.config["ui_config"]["bg_color"])
        ds.blit(next_class_name_text, (layout.collapsed_height * 0.9 + next_class_text.width, layout.collapsed_height * 0.92 - next_class_name_text.height + base_y))
        
        # - draw progress bar -
        bar_width = layout.width - layout.collapsed_height // 2 - layout.class_circle_radius * 0.93 - layout.class_progress_bar_offset
        
        draw.rect(ds, config.config["ui_config"]["progress_bar_bg_color"], (layout.collapsed_height // 2 + layout.class_circle_radius * 0.93, layout.collapsed_height // 2 - layout.class_progress_bar_height // 2 + base_y, bar_width, layout.class_progress_bar_height), border_bottom_right_radius=layout.class_progress_bar_radius, border_top_right_radius=layout.class_progress_bar_radius)
        draw.rect(ds, accent_color, (layout.collapsed_height // 2 + layout.class_circle_radius * 0.93, layout.collapsed_height // 2 - layout.class_progress_bar_height // 2 + base_y, bar_width * current_class.class_percent, layout.class_progress_bar_height), border_bottom_right_radius=layout.class_progress_bar_radius, border_top_right_radius=layout.class_progress_bar_radius)
        
        # - draw hover expansion bar -
        bar_surface = pygame.Surface((layout.width, layout.collapsed_height * 0.08), pygame.SRCALPHA)

        pygame.draw.rect(bar_surface, temp_accent_color, (0, 0, layout.width * layout.hovered_percent, layout.collapsed_height * 0.08))
        mask = pygame.Surface((layout.width, layout.collapsed_height * 0.08), pygame.SRCALPHA)
        
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, layout.collapsed_height * 0.08 - layout.current_height, layout.width, layout.current_height), border_radius=layout.border_radius)
        bar_surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        ds.blit(bar_surface, (0, layout.current_height - layout.collapsed_height * 0.08))

        # - draw secondary texts -
        percent_text = resources.font_20.render(str(round(current_class.class_percent * 100, 2)) + "%", True, config.config["ui_config"]["text_color"])
        ds.blit(percent_text, ((layout.collapsed_height * 1.1) // 2 + layout.class_circle_radius, layout.collapsed_height // 2 - percent_text.height // 2 + base_y))
        
        time_remaining_text = resources.font_20.render(current_class.time_remaining, True, config.config["ui_config"]["text_color"])
        ds.blit(time_remaining_text, (layout.collapsed_height // 2 + layout.class_circle_radius * 0.6 + bar_width - time_remaining_text.width, layout.collapsed_height // 2 - percent_text.height // 2 + base_y))
            
        day_text = resources.font_15.render(current.timeinfo_text, True, config.config["ui_config"]["text_color"], config.config["ui_config"]["bg_color"])
        day_text_pos = (layout.collapsed_height // 2 + layout.class_circle_radius * 0.6 + bar_width - day_text.width, layout.collapsed_height * 0.085 + base_y) 
        
        class_name_text = resources.font_15.render(current_course.name, True, config.config["ui_config"]["text_color"], config.config["ui_config"]["bg_color"])
        class_name_pos = (layout.collapsed_height * 0.9, layout.collapsed_height * 0.085 + base_y)
        if day_text_pos[0] < class_name_text.width + class_name_pos[0]:
            gradient = resources.special_surfaces["text_gradient"]
            if class_name_pos[0] < mx < day_text_pos[0] + day_text.width and class_name_pos[1] < my < class_name_pos[1] + class_name_text.height:
                ds.blit(class_name_text, class_name_pos, (0, 0, min(class_name_text.width, ds.width - class_name_pos[0] - layout.border_width), class_name_text.height))
                ds.blit(gradient, (ds.width - layout.border_width - class_name_text.height * 3, class_name_pos[1]))
            else:
                ds.blit(class_name_text, class_name_pos, (0, 0, min(class_name_text.width, day_text_pos[0] - class_name_pos[0]), class_name_text.height))
                ds.blit(gradient, (day_text_pos[0] - class_name_text.height * 2.3, class_name_pos[1]))
                draw.rect(ds, config.config["ui_config"]["bg_color"], (day_text_pos[0] - class_name_text.height * 2.3 + gradient.width, class_name_pos[1], gradient.width / 2, gradient.height))
                ds.blit(day_text, day_text_pos)
        else:
            ds.blit(class_name_text, class_name_pos, (0, 0, min(class_name_text.width, day_text_pos[0] - class_name_pos[0]), class_name_text.height))
            ds.blit(day_text, day_text_pos)
        
        # - draw icon circle -
        gfxdraw.filled_circle(ds, layout.collapsed_height // 2, layout.collapsed_height // 2 + base_y, layout.class_circle_radius, accent_color)
        gfxdraw.aacircle(ds, layout.collapsed_height // 2, layout.collapsed_height // 2 + base_y, layout.class_circle_radius, accent_color)
        
        # - draw icon -
        ds.blit(current_course.icon_surf, (layout.collapsed_height // 2 - layout.class_icon_radius, layout.collapsed_height // 2 - layout.class_icon_radius + base_y))

    def render_top_buttons():
        draw.rect(ds, config.config["ui_config"]["button_bg_color"], hide_button.button_rect, border_top_left_radius=round(layout.border_radius * 0.6))
        draw.rect(ds, config.config["ui_config"]["button_bg_color"], show_button.button_rect, border_top_right_radius=round(layout.border_radius * 0.6))
        
        smooth_percent = 2 * ((show_button.hover_percent) ** 0.5) - show_button.hover_percent
        center_pos = (layout.width * 3 // 4 + layout.top_button_padding * 0.35 - round(layout.top_button_padding * 0.675), layout.top_button_padding + layout.top_button_height // 2)
        
        if window.app_state["window_state"] == "temp_show":
            if config.config_open:
                text_surface = resources.top_text_surfaces["exit_settings"].copy()
                text_surface.set_alpha(round(smooth_percent * 255))
                ds.blit(text_surface, (center_pos[0] - 0.35 * text_surface.width * smooth_percent, center_pos[1] - text_surface.height // 2))
                ds.blit(resources.top_icon_surfaces["exit_settings"], (center_pos[0] - layout.top_button_icon_radius - 0.6 * text_surface.width * smooth_percent, center_pos[1] - layout.top_button_icon_radius))
            else:
                text_surface = resources.top_text_surfaces["settings"].copy()
                text_surface.set_alpha(round(smooth_percent * 255))
                ds.blit(text_surface, (center_pos[0] - 0.25 * text_surface.width * smooth_percent, center_pos[1] - text_surface.height // 2))
                ds.blit(resources.top_icon_surfaces["settings"], (center_pos[0] - layout.top_button_icon_radius - 0.55 * text_surface.width * smooth_percent, center_pos[1] - layout.top_button_icon_radius))
        else:
            text_surface = resources.top_text_surfaces["show"].copy()
            text_surface.set_alpha(round(smooth_percent * 255))
            ds.blit(text_surface, (center_pos[0] - 0.2 * text_surface.width * smooth_percent, center_pos[1] - text_surface.height // 2))
            ds.blit(resources.top_icon_surfaces["show"], (center_pos[0] - layout.top_button_icon_radius - 0.8 * text_surface.width * smooth_percent, center_pos[1] - layout.top_button_icon_radius))
        
        smooth_percent = 2 * ((hide_button.hover_percent) ** 0.5) - hide_button.hover_percent
        center_pos = (round(layout.top_button_padding * 0.325) + layout.width // 4, layout.top_button_padding + layout.top_button_height // 2)
        
        text_surface = resources.top_text_surfaces["hide"].copy()
        text_surface.set_alpha(round(smooth_percent * 255))
        ds.blit(text_surface, (center_pos[0] - 0.3 * text_surface.width * smooth_percent, center_pos[1] - text_surface.height // 2))
        ds.blit(resources.top_icon_surfaces["hide"], (center_pos[0] - layout.top_button_icon_radius - 0.6 * text_surface.width * smooth_percent, center_pos[1] - layout.top_button_icon_radius))
        
        draw.rect(ds, config.config["ui_config"]["button_accent_color"], (hide_button.button_rect.x, hide_button.button_rect.y + hide_button.button_rect.height * 0.9, hide_button.button_percent * hide_button.button_rect.width, hide_button.button_rect.height * 0.1))
        if window.app_state["window_state"] != "temp_show":
            draw.rect(ds, config.config["ui_config"]["button_accent_color"], (show_button.button_rect.x, show_button.button_rect.y + show_button.button_rect.height * 0.9, show_button.button_percent * show_button.button_rect.width, show_button.button_rect.height * 0.1))

    def render_schedule_preview(starting, height):
        # - calculate schedule display -
        stripped_schedule = []
        for _class in current.schedule:
            if _class.course.name != "Transition":
                stripped_schedule.append(_class)
        
        current_course = current.current_class.course
        _class = current.current_class
        if _class.course.name == "Transition":
            prev_class = None
            for iclass in current.schedule:
                if iclass.course.name != "Transition":
                    prev_class = iclass
                elif iclass == _class:
                    break
            _class = prev_class
        shift = stripped_schedule.index(_class)
        
        # - draw timeline -
        for k in range(6):
            i = k
            count = i - 2 + shift + math.floor(timeline_scroll)
            if current_course.name == "Transition":
                i -= 0.5
            i -= timeline_scroll % 1
            if count < 0 or count >= len(stripped_schedule):
                continue
            rendering_class = stripped_schedule[count]
            rendering_course = rendering_class.course
            color = rendering_course.accent_color
            if len(stripped_schedule) > count + 1:
                next_color = stripped_schedule[count + 1].course.accent_color
                if i < 5 * (config.config["ui_config"]["timeline_gradient"]):
                    section_height = round(height * (0.9 - 0.2 * i)) if i == 4 else round(height / 5)
                    for j in range(section_height):
                        c = lerp_color(color, next_color, min(1, j / (height / 5)))
                        draw.rect(ds, c, (layout.width * 0.08, starting + height / 5 * (i + 0.5) + j, layout.width * 0.015, 1))
                else:
                    draw.rect(ds, color, (layout.width * 0.08, starting + height / 5 * (i + 0.5), layout.width * 0.015, height / 5 * (4.5 - i)))
            draw.circle(ds, color, (layout.width * 0.0875, starting + height / 5 * (i + 0.5)), layout.width / 50)
            
            ds.blit(rendering_course.small_icon_surf, (layout.width * 0.195, starting + height / 5 * (i + 0.125)))
            
            primary_text = resources.font_17.render(rendering_course.name, True, config.config["ui_config"]["text_color"])
            ds.blit(primary_text, (layout.width * 0.26, starting + height / 5 * (i + 0.05)))
            
            subtext = rendering_class.start_time.strftime(config.config["ui_config"]["time_format"]) + " - " + rendering_class.end_time.strftime(config.config["ui_config"]["time_format"])
            small_text = resources.font_15.render(subtext, True, config.config["ui_config"]["muted_text_color"])
            ds.blit(small_text, (layout.width * 0.195, starting + height / 5 * (i + 0.46)))
        
        # - draw arrow - 
        arrow_surf = resources.font_17.render("<", True, config.config["ui_config"]["text_color"])
        ds.blit(arrow_surf, (layout.width * 0.14, starting + height / 2 - arrow_surf.height / 2 + height / 5 * (-timeline_scroll)))

    def render_settings(starting, height):
        buttons = config.config_buttons
        for k in range(6):
            i = k
            count = i + math.floor(config.config_scroll)
            i -= config.config_scroll % 1
            if count < 0 or count >= len(buttons):
                continue
            button = buttons[count]
            
            rect = pygame.Rect((0, starting + height / 5 * (i + 0.4), layout.width, height / 6))
            hovered = rect.collidepoint(mx, my)
            if hovered and window.app_state["window_state"] == "temp_show":
                button.hover_state = min(1, button.hover_state + 0.1)
            else:
                button.hover_state = max(0, button.hover_state - 0.1)
            hover_anim = 1 - ((1 - button.hover_state) ** 1.6)
            bg_color = lerp_color(config.config["ui_config"]["config_bg_color"], button.color, hover_anim * 0.15)
            draw.rect(ds, bg_color, rect)
            
            ds.blit(button.surf, (layout.width * 0.06, starting + height / 5 * (i + 0.62)))
            text = "This is a pointless button." if button.text == "This is a button." and hovered else button.text
            button_text = resources.font_17.render(text, True, button.color)
            ds.blit(button_text, (layout.width * 0.15, starting + height / 5 * (i + 0.6)))

            if button.arrow is not None:
                ds.blit(button.arrow_surf, (layout.width * (0.82 + hover_anim * 0.05), starting + height / 5 * (i + 0.62)))

# - config buttons onclick -
class ConfigOnClickFunctions:
    def reload_all(config_json=None):
        if config_json is not None:
            config.config = config_json
        config.save()
        schedule.reload("custom", config.config)
        resources.reload_all()
    
    def cocf_exit_config():
        # - closes the config -`
        config.config_open = False
    
    def cocf_edit_classes():
        try:
            all_courses = config.config["class_data"]["yearly_data"]["student_data"]["courses"]
        except (KeyError, AttributeError):
            messagebox.showerror("Error", "Could not find course data at config.config['class_data']['yearly_data']['student_data']['courses']!")
            return
    
        class_courses = [c for c in all_courses if c.get("class_type") == "class"]
        other_courses = [c for c in all_courses if c.get("class_type") != "class"]
    
        root = tk.Tk()
        root.title("Class Manager")
        root.geometry("750x520")
    
        main_frame = tk.Frame(root, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
    
        tk.Label(main_frame, text="Manage Classes").pack(anchor="w", pady=(0, 10))
    
        container = tk.Frame(main_frame)
        container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
    
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
    
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
    
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
        row_widgets = []
    
        def populate_rows():
            for widget in scrollable_frame.winfo_children():
                widget.destroy()
            row_widgets.clear()
    
            header_frame = tk.Frame(scrollable_frame)
            header_frame.pack(fill=tk.X, padx=5, pady=2)
            tk.Label(header_frame, text="Period", width=8, anchor="w").pack(side=tk.LEFT, padx=2)
            tk.Label(header_frame, text="Class Name", width=22, anchor="w").pack(side=tk.LEFT, padx=2)
            tk.Label(header_frame, text="Icon", width=16, anchor="w").pack(side=tk.LEFT, padx=2)
            tk.Label(header_frame, text="Accent Color", width=14, anchor="w").pack(side=tk.LEFT, padx=2)
    
            for course in class_courses:
                add_course_row(course)
    
        def add_course_row(course_data=None):
            if course_data is None:
                course_data = {"period": "", "class_name": "", "icon": "", "accent_color": "#D99B26"}
    
            row_frame = tk.Frame(scrollable_frame, pady=4)
            row_frame.pack(fill=tk.X, padx=5)
    
            period_var = tk.StringVar(value=str(course_data.get("period", "")))
            name_var = tk.StringVar(value=course_data.get("class_name", ""))
            icon_var = tk.StringVar(value=course_data.get("icon", ""))
            color_var = tk.StringVar(value=course_data.get("accent_color", "#D99B26"))
    
            tk.Entry(row_frame, textvariable=period_var, width=8).pack(side=tk.LEFT, padx=2)
            tk.Entry(row_frame, textvariable=name_var, width=22).pack(side=tk.LEFT, padx=2)
            tk.Entry(row_frame, textvariable=icon_var, width=16).pack(side=tk.LEFT, padx=2)
            tk.Entry(row_frame, textvariable=color_var, width=12).pack(side=tk.LEFT, padx=2)
    
            def pick_color():
                chosen = colorchooser.askcolor(color=color_var.get())
                if chosen[1]:
                    color_var.set(chosen[1])
                    color_btn.config(bg=chosen[1])
    
            color_btn = tk.Button(row_frame, text="🎨", bg=color_var.get(), width=7, command=pick_color)
            color_btn.pack(side=tk.LEFT, padx=2)
    
            def delete_row():
                row_frame.destroy()
                if row_info in row_widgets:
                    row_widgets.remove(row_info)
    
            tk.Button(row_frame, text="Delete", command=delete_row, fg="red").pack(side=tk.LEFT, padx=6)
    
            row_info = {
                "period_var": period_var,
                "name_var": name_var,
                "icon_var": icon_var,
                "color_var": color_var
            }
            row_widgets.append(row_info)
    
        def on_add_click():
            add_course_row()
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
    
        def on_save_click():
            updated_classes = []
            for rw in row_widgets:
                updated_classes.append({
                    "period": rw["period_var"].get().strip(),
                    "class_type": "class",
                    "accent_color": rw["color_var"].get().strip(),
                    "icon": rw["icon_var"].get().strip(),
                    "class_name": rw["name_var"].get().strip()
                })
            
            config.config["class_data"]["yearly_data"]["student_data"]["courses"] = updated_classes + other_courses
            ConfigOnClickFunctions.reload_all()
            
            root.destroy()
    
        def on_cancel_click():
            root.destroy()
    
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
    
        def open_link():
            webbrowser.open_new_tab("https://lucide.dev/icons/")
    
        tk.Button(btn_frame, text="+ Add Class", command=on_add_click, bg="#4CAF50", fg="black", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Icon Help", command=open_link, bg="#EF4444", fg="black", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=on_cancel_click, width=15).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Save", command=on_save_click, bg="#2196F3", fg="black", width=15).pack(side=tk.RIGHT, padx=5)
    
        populate_rows()
        root.mainloop()

    def cocf_edit_style():
        root = tk.Tk()
        root.title("Edit Style")
        root.geometry(f"450x350+{10+layout.width}+{layout.new_y + layout.expanded_height - 385}")
        
        fields = [
            ("Timeline Gradient", "timeline_gradient", "checkbox", "The timeline gradient determines whether the timeline will have a gradient."),
            ("Use Custom Accent Color", "use_main_accent_color", "checkbox", "This determines whether the set accent color or the accent color of the current class will be used"),
            ("Main Accent Color", "main_accent_color", "color", "The main accent color determines the color of the border and class progress bar."),
            ("Background Color", "bg_color", "color", "The background color determines the color of the background."),
            ("Progress Bar Background Color", "progress_bar_bg_color", "color", "The progress bar background color determines the color of the progress bar's background."),
            ("Config Button Background Color", "config_bg_color", "color", "The configuration button background color determines the background color of the configuration buttons."),
            ("Button Background Color", "button_bg_color", "color", "The button background color determines the color of the button's background."),
            ("Button Accent Color", "button_accent_color", "color", "The button accent color determines the accent color of the buttons."),
            ("Text Color", "text_color", "color", "The text color determines the color of the text."),
            ("Muted Text Color", "muted_text_color", "color", "The muted text color determines the 'disabled' color of the text."),
        ]
        
        entries = {}
        
        def set_widget_value(field_id, value):
            widget_info = entries[field_id]
            w_type = widget_info["type"]
            
            if w_type in ("text", "color"):
                widget_info["widget"].delete(0, tk.END)
                widget_info["widget"].insert(0, str(value))
            elif w_type == "checkbox":
                if str(value).lower() in ("true", "1", "yes"):
                    widget_info["variable"].set(True)
                else:
                    widget_info["variable"].set(False)
        
        def get_widget_value(field_id):
            widget_info = entries[field_id]
            w_type = widget_info["type"]
            
            if w_type == "text":
                return widget_info["widget"].get()
            elif w_type == "color":
                return list(school_schedule.hex_to_rgb(widget_info["widget"].get()))
            elif w_type == "checkbox":
                return widget_info["variable"].get()
        
        def reset_to_default(field_id, default_value):
            set_widget_value(field_id, default_value)
            
        def rgb_to_hex(c):
            if c is None: return None
            if isinstance(c, str): return c
            if isinstance(c, int): return c
            r, g, b = c
            return f"#{r:02x}{g:02x}{b:02x}"
            
        def pick_color(entry_widget):
            current_color = entry_widget.get()
            color_code = colorchooser.askcolor(initialcolor=rgb_to_hex(current_color) if current_color else None)[1]
            if color_code:
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, color_code)
        
        title_label = tk.Label(root, text="Edit Style Options")
        title_label.pack(pady=10)
    
        outer_container = tk.Frame(root)
        outer_container.pack(fill="both", expand=True, padx=10)
        
        canvas = tk.Canvas(outer_container, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(outer_container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        form_frame = tk.Frame(canvas)
        
        canvas_window = canvas.create_window((0, 0), window=form_frame, anchor="nw")
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        form_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        
        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        root.bind_all("<MouseWheel>", on_mouse_wheel)
        
        for i, (field_name, field_id, option_type, field_desc) in enumerate(fields):
            label = tk.Label(form_frame, text=field_name, anchor="w")
            label.grid(row=i * 2, column=0, padx=5, pady=(5, 2), sticky="w")
        
            if option_type == "text":
                entry = tk.Entry(form_frame)
                entry.grid(row=i * 2, column=1, padx=5, pady=(5, 2), sticky="ew")
                entries[field_id] = {"type": "text", "widget": entry}
                
            elif option_type == "color":
                color_frame = tk.Frame(form_frame)
                color_frame.grid(row=i * 2, column=1, padx=5, pady=(5, 2), sticky="ew")
                color_frame.columnconfigure(0, weight=1)
                
                entry = tk.Entry(color_frame)
                entry.grid(row=0, column=0, sticky="ew")
                
                color_btn = tk.Button(color_frame, text=">", width=3, command=lambda e=entry: pick_color(e))
                color_btn.grid(row=0, column=1, padx=(2, 0))
                
                entries[field_id] = {"type": "color", "widget": entry}
                
            elif option_type == "checkbox":
                var = tk.BooleanVar()
                chk = tk.Checkbutton(form_frame, variable=var, anchor="w")
                chk.grid(row=i * 2, column=1, padx=5, pady=(5, 2), sticky="w")
                entries[field_id] = {"type": "checkbox", "widget": chk, "variable": var}
        
            initial_val = config.config["ui_config"].get(field_id, "")
            initial_val = rgb_to_hex(initial_val) if option_type == "color" else initial_val
            initial_val = str(initial_val) if option_type == "text" else initial_val
            set_widget_value(field_id, initial_val)
            
            fallback_val = rgb_to_hex(config.fallback_config["ui_config"].get(field_id, ""))
            reset_btn = tk.Button(
                form_frame, 
                text="Reset", 
                command=lambda fid=field_id, fval=fallback_val: reset_to_default(fid, fval), 
                width=8
            )
            reset_btn.grid(row=i * 2, column=2, padx=5, pady=(5, 2), sticky="e")
        
            description = tk.Label(form_frame, text=field_desc, justify="left", anchor="w", wraplength=410)
            description.grid(row=i * 2 + 1, column=0, columnspan=3, padx=5, pady=(0, 5), sticky="w")
        
        form_frame.columnconfigure(1, weight=1)
        
        def save_config():
            for field_name, field_id, option_type, field_desc in fields:
                config.config["ui_config"][field_id] = get_widget_value(field_id)
            config.save()
            ConfigOnClickFunctions.reload_all(config.config)
            try:
                root.destroy()
            except tk.TclError:
                pass
        
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        
        dont_save_btn = tk.Button(button_frame, text="Cancel", command=root.destroy, width=15)
        dont_save_btn.pack(side="left", padx=5, fill="x")
        
        save_btn = tk.Button(button_frame, text="Save and Close", command=save_config, width=15)
        save_btn.pack(side="left", padx=5, fill="x")
        
        root.mainloop()

    def cocf_edit_format():
        root = tk.Tk()
        root.title("Edit User Experience Variables")
        root.geometry(f"450x350+{10+layout.width}+{layout.new_y + layout.expanded_height - 385}")

        fields = [
            ("Default Transparency", "default_transparency", "text", "The default transparency determines the default transparency."),
            ("Time Format", "time_format", "text", "The time format determines how the time is shown on the timeline. For example, '%#I:%M %p' changes the time format to standard 12 hour time, while '%H:%M' is for 24 hour time."),
            ("Scroll Speed", "scroll_speed", "text", "The scroll speed determines the multiplier of the speed of scrolling in the timeline and the configuration menu."),
            ("Window Width", "width", "text", "The window width determines the width of the window when the menu is NOT OPEN."),
            ("Window Height", "height", "text", "The window height determines the height of the window when the menu is NOT OPEN.")
        ]
        
        entries = {}
        
        def set_widget_value(field_id, value):
            widget_info = entries[field_id]
            w_type = widget_info["type"]
            
            if w_type in ("text", "color"):
                widget_info["widget"].delete(0, tk.END)
                widget_info["widget"].insert(0, str(value))
            elif w_type == "checkbox":
                if str(value).lower() in ("true", "1", "yes"):
                    widget_info["variable"].set(True)
                else:
                    widget_info["variable"].set(False)
        
        def get_widget_value(field_id):
            widget_info = entries[field_id]
            w_type = widget_info["type"]
            
            if w_type == "text":
                return widget_info["widget"].get()
            elif w_type == "color":
                return list(school_schedule.hex_to_rgb(widget_info["widget"].get()))
            elif w_type == "checkbox":
                return widget_info["variable"].get()
        
        def reset_to_default(field_id, default_value):
            set_widget_value(field_id, default_value)
            
        def rgb_to_hex(c):
            if c is None: return None
            if isinstance(c, str): return c
            if isinstance(c, int): return c
            r, g, b = c
            return f"#{r:02x}{g:02x}{b:02x}"
            
        def pick_color(entry_widget):
            current_color = entry_widget.get()
            color_code = colorchooser.askcolor(initialcolor=rgb_to_hex(current_color) if current_color else None)[1]
            if color_code:
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, color_code)
        
        title_label = tk.Label(root, text="Edit User Experience Variables")
        title_label.pack(pady=10)
    
        outer_container = tk.Frame(root)
        outer_container.pack(fill="both", expand=True, padx=10)
        
        canvas = tk.Canvas(outer_container, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(outer_container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        form_frame = tk.Frame(canvas)
        
        canvas_window = canvas.create_window((0, 0), window=form_frame, anchor="nw")
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        form_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        
        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        root.bind_all("<MouseWheel>", on_mouse_wheel)
        
        for i, (field_name, field_id, option_type, field_desc) in enumerate(fields):
            label = tk.Label(form_frame, text=field_name, anchor="w")
            label.grid(row=i * 2, column=0, padx=5, pady=(5, 2), sticky="w")
        
            if option_type == "text":
                entry = tk.Entry(form_frame)
                entry.grid(row=i * 2, column=1, padx=5, pady=(5, 2), sticky="ew")
                entries[field_id] = {"type": "text", "widget": entry}
                
            elif option_type == "color":
                color_frame = tk.Frame(form_frame)
                color_frame.grid(row=i * 2, column=1, padx=5, pady=(5, 2), sticky="ew")
                color_frame.columnconfigure(0, weight=1)
                
                entry = tk.Entry(color_frame)
                entry.grid(row=0, column=0, sticky="ew")
                
                color_btn = tk.Button(color_frame, text="🎨", width=3, command=lambda e=entry: pick_color(e))
                color_btn.grid(row=0, column=1, padx=(2, 0))
                
                entries[field_id] = {"type": "color", "widget": entry}
                
            elif option_type == "checkbox":
                var = tk.BooleanVar()
                chk = tk.Checkbutton(form_frame, variable=var, anchor="w")
                chk.grid(row=i * 2, column=1, padx=5, pady=(5, 2), sticky="w")
                entries[field_id] = {"type": "checkbox", "widget": chk, "variable": var}
        
            initial_val = config.config["ui_config"].get(field_id, "")
            initial_val = rgb_to_hex(initial_val) if option_type == "color" else initial_val
            initial_val = str(initial_val) if option_type == "text" else initial_val
            set_widget_value(field_id, initial_val)
            
            fallback_val = rgb_to_hex(config.fallback_config["ui_config"].get(field_id, ""))
            reset_btn = tk.Button(
                form_frame, 
                text="Reset", 
                command=lambda fid=field_id, fval=fallback_val: reset_to_default(fid, fval), 
                width=8
            )
            reset_btn.grid(row=i * 2, column=2, padx=5, pady=(5, 2), sticky="e")
        
            description = tk.Label(form_frame, text=field_desc, justify="left", anchor="w", wraplength=410)
            description.grid(row=i * 2 + 1, column=0, columnspan=3, padx=5, pady=(0, 5), sticky="w")
        
        form_frame.columnconfigure(1, weight=1)
        
        def save_config():
            for field_name, field_id, option_type, field_desc in fields:
                config.config["ui_config"][field_id] = get_widget_value(field_id)
            config.save()
            ConfigOnClickFunctions.reload_all(config.config)
            try:
                root.destroy()
            except tk.TclError:
                pass

        def open_link():
            webbrowser.open_new_tab("https://docs.python.org/3/library/datetime.html#format-codes")

        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        
        tf_docs_btn = tk.Button(button_frame, text="Time Format Docs", command=open_link, width=15)
        tf_docs_btn.pack(side="left", padx=5, fill="x")
        
        dont_save_btn = tk.Button(button_frame, text="Cancel", command=root.destroy, width=15)
        dont_save_btn.pack(side="left", padx=5, fill="x")

        save_btn = tk.Button(button_frame, text="Save and Close", command=save_config, width=15)
        save_btn.pack(side="left", padx=5, fill="x")

        root.mainloop()

    def cocf_edit_special_dates():
        root = tk.Tk()
        root.title("Edit Special Dates")
        root.geometry(f"450x350+{10+layout.width}+{layout.new_y + layout.expanded_height - 385}")
        
        encoding = "0123456789ABCDEFGHIJ"

        def decode_dates(d_str):
            dates = []
            for i in range(0, len(d_str) // 2):
                base_int = encoding.index(d_str[2 * i]) * 20 + encoding.index(d_str[2 * i + 1]) + 30
                dates.append(str(base_int // 31) + "," + str(base_int % 31 + 1))
            return dates

        def decode(d_str):
            rawdata = d_str.split(";")
            data = {}
            for item in rawdata:
                s = item.split(":")
                if s[0] == "Year":
                    data["year"] = int(s[1])
                elif s[0] == "Adv":
                    data["advisory"] = s[1]
                elif s[0] == "Limit":
                    data["school_bounds"] = decode_dates(s[1])
                elif s[0] == "NoS":
                    data["no_school"] = decode_dates(s[1])
                elif s[0] == "Short":
                    data["short_days"] = decode_dates(s[1])
            return data
        
        def save_config():
            if str(import_text.get("1.0", "end-1c")) != "":
                decoded = decode(str(import_text.get("1.0", "end-1c")))
                config.config["class_data"]["yearly_data"]["special_dates"] = decoded
                ConfigOnClickFunctions.reload_all()
                try:
                    root.destroy()
                except tk.TclError:
                    pass
        
        main_container = tk.Frame(root)
        main_container.pack(expand=True, fill="both", padx=20, pady=10)
        
        instruction_label = tk.Label(main_container, text="Paste import code here:")
        instruction_label.pack(anchor="w", pady=(0, 5))
        
        import_text = tk.Text(main_container, height=10, width=40)
        import_text.pack(expand=True, fill="both", pady=(0, 10))
        
        button_frame = tk.Frame(main_container)
        button_frame.pack(side="bottom", pady=10)
        
        dont_save_btn = tk.Button(button_frame, text="Cancel", command=root.destroy, width=15)
        dont_save_btn.pack(side="left", padx=5)
        
        save_btn = tk.Button(button_frame, text="Save and Close", command=save_config, width=15)
        save_btn.pack(side="left", padx=5)
        
        root.mainloop()
        
    def cocf_edit_config_file():
        # - open Tk window for JSON editing -
        root = tk.Tk()
        root.title("Edit Raw JSON Configuration")
        root.geometry(f"800x500+{10+layout.width}+{layout.new_y + layout.expanded_height - 535}")

        initial_json_str = json.dumps(config.config, indent=4)
        
        header_frame = tk.Frame(root)
        header_frame.pack(fill="x", padx=15, pady=(12, 5))
        
        title_label = tk.Label(
            header_frame,
            text="Edit JSON Configuration File. Use at your own risk. Invalid values may silently trigger crashes.",
            anchor="w"
        )
        title_label.pack(fill="x")

        text_area = tk.Text(root, wrap="word", width=50, height=20)
        text_area.insert("1.0", initial_json_str)
        text_area.pack(padx=10, pady=10, fill="both", expand=True)

        def save_and_close():
            raw_content = text_area.get("1.0", "end-1c")

            try:
                parsed_json = json.loads(raw_content)
                if not isinstance(parsed_json, dict):
                    raise ValueError("JSON root must be a dictionary/object.")

                try:
                    root.destroy()
                except tk.TclError:
                    pass
                
                ConfigOnClickFunctions.reload_all(parsed_json)
                layout.update()
            except (json.JSONDecodeError, ValueError) as e:
                tk.messagebox.showerror(
                    "Invalid JSON", f"Please fix JSON syntax errors:\n{e}"
                )

        def open_link():
            webbrowser.open_new_tab("https://stackoverflow.blog/2022/06/02/a-beginners-guide-to-json-the-data-format-for-the-internet/")

        button_frame = tk.Frame(root)
        button_frame.pack(pady=(0, 10))

        json_button = tk.Button(button_frame, text="JSON Help", command=open_link, width=20)
        json_button.pack(side="left", padx=5)

        dont_save_button = tk.Button(button_frame, text="Cancel", command=root.destroy, width=20)
        dont_save_button.pack(side="left", padx=5)

        save_button = tk.Button(button_frame, text="Save and Close", command=save_and_close, width=20)
        save_button.pack(side="left", padx=5)

        try:
            root.mainloop()
        except KeyboardInterrupt:
            root.destroy()
    
    def cocf_resize():
        root = tk.Tk()
        root.title("Resize Window")
        root.geometry(f"400x180+{10+layout.width}+{layout.new_y + layout.expanded_height - 275}")
        
        def validate_int(P):
            if P == "" or P.isdigit():
                return True
            return False
        
        vcmd = (root.register(validate_int), '%P')
        
        input_frame = tk.Frame(root)
        input_frame.pack(pady=15, fill="x", padx=15)
        
        title_label = tk.Label(
            input_frame, 
            text="The size is measured in pixels. The size is when the menu is CLOSED, so the height will seem way larger.",
            wraplength=370, 
            justify="left"
        )
        title_label.pack(pady=5, anchor="w")
        
        width_frame = tk.Frame(input_frame)
        width_frame.pack(side="left", padx=20)
        
        width_entry = tk.Entry(width_frame, width=10, validate="key", validatecommand=vcmd)
        width_entry.pack(anchor="w")
        width_entry.insert(0, str(config.config["ui_config"]["width"]))
        
        width_label = tk.Label(width_frame, text="Width")
        width_label.pack(pady=2, anchor="w")
        
        height_frame = tk.Frame(input_frame)
        height_frame.pack(side="left", padx=20)
        
        height_entry = tk.Entry(height_frame, width=10, validate="key", validatecommand=vcmd)
        height_entry.pack(anchor="w")
        height_entry.insert(0, str(config.config["ui_config"]["height"]))
        
        height_label = tk.Label(height_frame, text="Height")
        height_label.pack(pady=2, anchor="w")
        
        def save_config():
            w_val = width_entry.get()
            h_val = height_entry.get()
            
            if not w_val or not h_val:
                messagebox.showerror("Error", "Width and Height cannot be empty.")
                return
                
            config.config["ui_config"]["width"] = str(w_val)
            config.config["ui_config"]["height"] = str(h_val)
            layout.update()
            ConfigOnClickFunctions.reload_all()
            
            try:
                root.destroy()
            except tk.TclError:
                pass
        
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        
        dont_save_button = tk.Button(button_frame, text="Cancel", command=root.destroy, width=15)
        dont_save_button.pack(side="left", padx=5)
        
        save_button = tk.Button(button_frame, text="Save", command=save_config, width=15)
        save_button.pack(side="left", padx=5)
        
        try:
            root.mainloop()
        except KeyboardInterrupt:
            root.destroy()


    def cocf_app_info():
        # - app info window -
        pinfo = platform.uname()
        
        APP_INFO_TEXT = f"""App & System Information
        
OS Name: {pinfo.system} ("{pinfo.node}")
Full Info: {pinfo.system} {pinfo.release}, {pinfo.machine}, {pinfo.version}

Here's your Python versions:
    Python {sys.version}
    Pygame {pygame.version.ver}

And, the app version is {APP_VERSION}
The configuration filepath is
    Default R/W: {Config.CONFIG_PATH}
    Fallback: {Config.FALLBACK_CONFIG_PATH}"""
     
        def open_url():
            webbrowser.open("https://github.com/un-undefined/school-schedule-manager")
        
        root = tk.Tk()
        root.title("App Info")
        root.geometry(f"500x400+{10+layout.width}+{layout.new_y + layout.expanded_height - 485}")
        
        text_widget = tk.Text(root, wrap="word", padx=10, pady=10, height=1)
        text_widget.insert("1.0", APP_INFO_TEXT)
        text_widget.config(state="disabled") 
        text_widget.pack(expand=True, fill="both")
        
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        
        link_button = tk.Button(button_frame, text="Open GitHub Page", command=open_url, width=20)
        link_button.pack(side="left", padx=5)
        
        close_btn = tk.Button(button_frame, text="Close", command=root.destroy, width=15)
        close_btn.pack(side="left", padx=5)
        
        try:
            root.mainloop()
        except KeyboardInterrupt:
            root.destroy()
    
    def cocf_github():
        # - open github page -
        webbrowser.open_new_tab("https://github.com/un-undefined/school-schedule-manager")
    
    def cocf_form():
        # - open feedback / bug report form -
        webbrowser.open_new_tab("https://forms.gle/oKoyiL4BcA96MvTv6")
    
    def cocf_copyright():
        # - copyright info window -
        MIT_LICENSE_TEXT = """
    This is the MIT License. For additional information, credit, and notes, view the GitHub page, accessed through the button below or this link: https://github.com/un-undefined/school-schedule-manager/blob/main/LICENSE
        
Copyright 2026 un-undefined
    
    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."""
        
        def open_url():
            webbrowser.open("https://github.com/un-undefined/school-schedule-manager/blob/main/LICENSE")
        
        root = tk.Tk()
        root.title("Copyright Info")
        root.geometry(f"800x450+{10+layout.width}+{layout.new_y + layout.expanded_height - 485}")
        
        text_widget = tk.Text(root, wrap="word", padx=10, pady=10)
        text_widget.insert("1.0", MIT_LICENSE_TEXT)
        text_widget.config(state="disabled") 
        text_widget.pack(expand=True, fill="both")
        
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        
        link_button = tk.Button(button_frame, text="Open GitHub License", command=open_url, width=20)
        link_button.pack(side="left", padx=5)
        
        close_btn = tk.Button(button_frame, text="Close", command=root.destroy, width=15)
        close_btn.pack(side="left", padx=5)
        
        try:
            root.mainloop()
        except:
            root.destroy()
        
    def cocf_close_app():
        # - closes the app -

        def close_cas():
            ConfigOnClickFunctions.reload_all(config.fallback_config)
            root.destroy()
            window.quit_pressed()
        
        root = tk.Tk()
        root.title("Confirm Program Close")
        root.geometry(f"400x130+{10+layout.width}+{layout.new_y + layout.expanded_height - 275}")
        
        text_widget = tk.Label(root, text="Are you sure that you want to close the application? If you placed the app as a desktop shortcut, you can reopen it by double-clicking the icon.", padx=10, pady=10, height=3, wraplength=300, justify="left")
        text_widget.pack(expand=True, fill="both")
        
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        
        return_button = tk.Button(button_frame, text="No, go back!", command=root.destroy, width=20)
        return_button.pack(side="left", padx=5)
        
        reset_btn = tk.Button(button_frame, text="Yes, save and close the app.", command=close_cas, width=20)
        reset_btn.pack(side="left", padx=5)
        
        try:
            root.mainloop()
        except KeyboardInterrupt:
            root.destroy()
    
    def cocf_reset_config():
        # - reset config to fallback -
        
        def reset_config():
            c = config.fallback_config
            ConfigOnClickFunctions.reload_all(c)
            layout.update()
            root.destroy()
        
        root = tk.Tk()
        root.title("Confirm Configuration Reset")
        root.geometry(f"400x130+{10+layout.width}+{layout.new_y + layout.expanded_height - 275}")
        
        text_widget = tk.Label(root, text="Are you sure that you want to reset all your information? The configuration file will be reset, meaning your color styles, classes, and year-based information will be removed. The program will revert to Owen's courses.", padx=10, pady=10, height=3, wraplength=300, justify="left")
        text_widget.pack(expand=True, fill="both")
        
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        
        return_button = tk.Button(button_frame, text="No, go back!", command=root.destroy, width=20)
        return_button.pack(side="left", padx=5)
        
        reset_btn = tk.Button(button_frame, text="Yes, reset all my data.", command=reset_config, width=20)
        reset_btn.pack(side="left", padx=5)
        
        try:
            root.mainloop()
        except KeyboardInterrupt:
            root.destroy()

    def clicked():
        root = tk.Tk()
        root.title("I guessed you clicked it, huh?")
        root.geometry("400x70")
        
        text_widget = tk.Text(root, wrap="word", padx=10, pady=10, height=1)
        text_widget.insert("1.0", "Well, technically, it did something...")
        text_widget.config(state="disabled") 
        text_widget.pack(expand=False, fill="both")
        
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)

        close_btn = tk.Button(button_frame, text="Close", command=root.destroy, width=10)
        close_btn.pack(side="left", padx=5)
        
        try:
            root.mainloop()
        except KeyboardInterrupt:
            root.destroy()

# - config buttons -
class ConfigButton:
    def __init__(self, text, icon, color=(255, 255, 255), onclick=None, arrow=None):
        config.config_buttons.append(self)
        
        self.text = text
        self.icon = icon
        self.color = color
        self.arrow = arrow
        
        self.onclick = onclick
        self.hover_state = 0
        
        self.reload()
    
    def reload(self):
        self.surf = resources.load_icon(self.icon, layout.top_button_icon_radius, color=self.color)
        if self.arrow is not None:
            self.arrow_surf = resources.load_icon(self.arrow, layout.top_button_icon_radius, color=self.color)

    def clicked(self):
        if self.onclick is not None:
            self.onclick()

exit_config = ConfigButton("Exit Configuration", "log-out", (255, 170, 170), ConfigOnClickFunctions.cocf_exit_config, arrow="square-arrow-right-exit")
edit_classes = ConfigButton("Edit Classes", "school", (170, 220, 255), ConfigOnClickFunctions.cocf_edit_classes, arrow="chevron-right")
edit_style = ConfigButton("Edit Style", "paint-roller", (255, 255, 255), ConfigOnClickFunctions.cocf_edit_style, arrow="chevron-right")
edit_format = ConfigButton("Edit UX Variables", "monitor-cog", (200, 170, 255), ConfigOnClickFunctions.cocf_edit_format, arrow="chevron-right")
resize = ConfigButton("Resize Window", "scaling", (170, 220, 255), ConfigOnClickFunctions.cocf_resize, arrow="chevron-right")
edit_special_dates = ConfigButton("Edit Yearly Info", "calendar-days", (255, 220, 170), ConfigOnClickFunctions.cocf_edit_special_dates, arrow="chevron-right")
edit_config_file = ConfigButton("Edit Raw Config File", "code", (170, 255, 170), ConfigOnClickFunctions.cocf_edit_config_file, arrow="chevron-right")
app_info = ConfigButton("App Info", "book-text", (255, 255, 255), ConfigOnClickFunctions.cocf_app_info, arrow="square-text")
github = ConfigButton("Open GitHub", "folder-git-2", (170, 255, 170), ConfigOnClickFunctions.cocf_github, arrow="external-link")
bug_reports = ConfigButton("Bug Reports", "bug", (255, 170, 170), ConfigOnClickFunctions.cocf_form, arrow="external-link")
feedback = ConfigButton("Feedback", "message-square-reply", (200, 170, 255), ConfigOnClickFunctions.cocf_form, arrow="external-link")
copyright = ConfigButton("Copyright", "copyright", (170, 220, 255), ConfigOnClickFunctions.cocf_copyright, arrow="chevron-right")
source_code = ConfigButton("View Source Code", "file-code-corner", (170, 255, 170), ConfigOnClickFunctions.cocf_github, arrow="external-link")
close_app = ConfigButton("Close Application", "circle-x", (255, 170, 170), ConfigOnClickFunctions.cocf_close_app, arrow="circle-arrow-right")
reset_config = ConfigButton("Reset Configuration", "list-restart", (255, 170, 170), ConfigOnClickFunctions.cocf_reset_config, arrow="rotate-ccw")
a_button = ConfigButton("This is a button.", "mouse-pointer-click", (255, 255, 255), ConfigOnClickFunctions.clicked)

# - show / hide buttons -
class TopButton:
    def __init__(self, mode):
        resources.top_buttons.append(self)
        
        self.button_time = None
        self.button_hovered = False
        self.button_percent = 0
        self.hover_percent = 0
        
        self.mode = mode
        self.reload()
        
    def reload(self):
        if self.mode == "hide":
            self.button_rect = pygame.Rect(layout.top_button_padding, layout.top_button_padding, layout.width // 2 - layout.top_button_padding * 1.35, layout.top_button_height)
        elif self.mode == "show":
            self.button_rect = pygame.Rect(layout.width // 2 + layout.top_button_padding * 0.35, layout.top_button_padding, layout.width // 2 - layout.top_button_padding * 1.35, layout.top_button_height)
        
    def update(self):
        if self.button_rect.collidepoint((mx, my)):
            self.hover_percent = min(1, self.hover_percent + 0.06)
            if not self.button_hovered:
                self.button_hovered = True
                if self.button_time is not None and time.time() - self.button_time < 1:
                    self.button_time = 2 * time.time() - self.button_time - 1
                else:
                    self.button_time = time.time()
            else:
                self.button_percent = min(1, time.time() - self.button_time)
                if self.button_percent == 1:
                    return True
        else:
            self.hover_percent = max(0, self.hover_percent - 0.06)
            if self.button_hovered:
                self.button_hovered = False
                if self.button_time is not None and time.time() - self.button_time < 1:
                    self.button_time = 2 * time.time() - self.button_time - 1
                else:
                    self.button_time = time.time()
            else:
                if self.button_time is not None:
                    self.button_percent = max(0, 1 - time.time() + self.button_time)
        return False

show_button = TopButton("show")
hide_button = TopButton("hide")

hide_time_start = None
hide_time_remaining = 0

# - important variables -

running = True

timeline_scroll = 0

layout._calculate_dependent_properties()

# <--== MAIN EXECUTION LOOP ==-->

try:
    while running:
        # - cursor & window info -
        try:
            _, _, (global_x, global_y) = win32gui.GetCursorInfo()
        except:
            continue
        win_x, win_y = window.screen.position
        window_rect = pygame.Rect(win_x, win_y, layout.width, round(layout.current_height))
        prev_mouse_hovered = window_rect.collidepoint(global_x, global_y)
        mx, my = (global_x - win_x, global_y - win_y)
        
        # - expand bar & expansion logic -
        if layout.update_hover() and hide_time_start is None:    
            # - reset app state -
            window.reset_state()
                    
        # - expansion window updates -
        if round(layout.height_target) != round(layout.current_height) or window.screen.size != (layout.width, round(layout.current_height)):
            bottom_y = win_y + round(layout.current_height)
            layout.current_height = layout.height_target
            rounded_h = round(layout.current_height)
    
            window.screen.size = (layout.width, rounded_h)
            
            layout.new_y = bottom_y - rounded_h
            win32gui.SetWindowPos(
                window.hwnd, win32con.HWND_TOPMOST, 
                win_x, layout.new_y, layout.width, rounded_h,
                win32con.SWP_NOACTIVATE | win32con.SWP_NOCOPYBITS | win32con.SWP_FRAMECHANGED
            )
            
            ds = window.screen.get_surface()
            timeline_scroll = 0
            config.config_scroll = 0
        base_y = round(layout.current_height) - layout.collapsed_height
        
        # - get current schedule -
        current = schedule.current()
        current_class = current.current_class
        current_course = current_class.course
        accent_color = current_course.accent_color
        
        temp_accent_color = accent_color if not config.config["ui_config"]["use_main_accent_color"] else config.config["ui_config"]["main_accent_color"]
        
        # - draw background -
        ds.fill((255, 0, 255))
        draw.rect(ds, config.config["ui_config"]["bg_color"], (0, 0, layout.width, layout.current_height), border_radius=18)
        
        # - draw expanded screen -
        if layout.current_height == layout.expanded_height:
            starting = layout.top_button_height * 1.3 + layout.top_button_padding
            height = base_y - layout.top_button_height * 1.2 - layout.top_button_padding
            if config.config_open:
                RenderHandler.render_settings(starting, height)
            else:
                RenderHandler.render_schedule_preview(starting, height)
            
            # - draw overlays -
            draw.rect(ds, config.config["ui_config"]["bg_color"], (0, 0, layout.width, starting))
            draw.rect(ds, config.config["ui_config"]["bg_color"], (0, starting + height, layout.width, layout.expanded_height - starting - height))
            
            ds.blit(resources.special_surfaces["top_gradient"], (0, starting))
            ds.blit(resources.special_surfaces["bottom_gradient"], (0, starting + height - resources.special_surfaces["bottom_gradient"].height))
    
            # - draw visibility buttons -
            if show_button.update():
                if window.app_state["window_state"] == "default":
                    # - enable window interaction -
                    window.app_state["window_state"] = "temp_show"
                    window.set_window_alpha(255)
                    window.set_window_clickthrough(False)
                    show_button.hover_percent = 0
                 
            if hide_button.update():
                # - hide window temporarily -
                hide_time_start = time.time()
                window.hide_window()
            
            RenderHandler.render_top_buttons()
    
        if hide_time_start is not None and time.time() - hide_time_start >= 10:
            hide_time_start = None
            window.reset_state()
        
        # - render texts -
        RenderHandler.render_basic_texts()
            
        # - draw window border -
        draw.rect(ds, temp_accent_color, (0, 0, layout.width, layout.current_height), layout.border_width, border_radius=layout.border_radius)
        
        # - main event handler -
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button < 4:
                    if show_button.button_rect.collidepoint((mx, my)):
                        config.config_open = not config.config_open
                        show_button.hover_percent = 0
                        config.config_scroll = 0
                    elif config.config_open:
                        for k in range(5):
                            i = k
                            count = i + math.floor(config.config_scroll)
                            i -= config.config_scroll % 1
                            if pygame.Rect((0, starting + height / 5 * (i + 0.4), layout.width, height / 6)).collidepoint(mx, my):
                                config.config_buttons[count].clicked()
    
            elif event.type == pygame.MOUSEWHEEL:
                if layout.current_height == layout.expanded_height and pygame.Rect(0, layout.top_button_height * 1.3 + layout.top_button_padding, layout.width, base_y - layout.top_button_height * 1.2 - layout.top_button_padding).collidepoint((mx, my)):
                    if config.config_open:
                        config.config_scroll = min(max(0, config.config_scroll - event.precise_y * float(config.config["ui_config"]["scroll_speed"])), len(config.config_buttons) - 4.4)
                    else:
                        stripped_schedule = []
                        for _class in current.schedule:
                            if _class.course.name != "Transition":
                                stripped_schedule.append(_class)
                        
                        current_course = current.current_class.course
                        _class = current.current_class
                        if _class.course.name == "Transition":
                            prev_class = None
                            for iclass in current.schedule:
                                if iclass.course.name != "Transition":
                                    prev_class = iclass
                                elif iclass == _class:
                                    break
                            _class = prev_class
                        shift = stripped_schedule.index(_class)

                        timeline_scroll = max(-shift, min(len(stripped_schedule)-shift-1, timeline_scroll - event.precise_y * float(config.config["ui_config"]["scroll_speed"])))
        
            elif event.type == pygame.WINDOWMINIMIZED or event.type == pygame.WINDOWHIDDEN:
                pygame.time.wait(500)
        
        window.screen.flip()
        clock.tick(60)
except Exception as e:
    traceback_lines = traceback.format_exception(e)
    traceback_string = "".join(traceback_lines)
    
    root = tk.Tk()
    root.title("An Exception has occured!")
    root.geometry("400x300")
    
    root.attributes('-topmost', True)
    
    text_widget = tk.Text(root, wrap="word", padx=10, pady=10, height=15)
    text_widget.insert("1.0", "Something really, really, really bad probably happened if it wasn't caught by automated debugging. Or you typed something in a configuration menu that wasn't right. Likely, it is caused by invalid modification or corruption of the main configuration file.\n\nSomething unexpected happened. Paste the below into a bug report form.\n\n" + traceback_string)
    text_widget.config(state="disabled") 
    text_widget.pack(expand=False, fill="both")
    
    button_frame = tk.Frame(root)
    button_frame.pack(pady=5)
    
    close_btn = tk.Button(button_frame, text="Ok.", command=root.destroy, width=10)
    close_btn.pack(side="left", padx=5)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.destroy()
    
window.quit_all()