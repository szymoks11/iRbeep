#!/usr/bin/env python3
"""
iRacing RPM Alert - Version 1.0
A real-time RPM monitoring and shift point alert system for iRacing

Author: Szymon Flis
Version: 1.0.3
License: MIT
Repository: https://github.com/szymoks11/irbeep
"""

import irsdk
import tkinter as tk
from tkinter import ttk, messagebox
import winsound
import time
import json
import re
import logging
from pathlib import Path
from typing import Dict, Union, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('iracing_rpm_alert.log'),
        logging.StreamHandler()
    ]
)

class ModernButton(tk.Button):
    """Modern styled button with hover effects"""
    def __init__(self, parent, **kwargs):
        # Extract custom properties
        self.bg_normal = kwargs.pop('bg_normal', '#2d3142')
        self.bg_hover = kwargs.pop('bg_hover', '#4f5d75')
        self.fg_color = kwargs.pop('fg_color', 'white')
        
        # Set default button properties
        kwargs.setdefault('relief', 'flat')
        kwargs.setdefault('bd', 0)
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('bg', self.bg_normal)
        kwargs.setdefault('fg', self.fg_color)
        kwargs.setdefault('font', ('Segoe UI', 10, 'bold'))
        kwargs.setdefault('cursor', 'hand2')
        kwargs.setdefault('padx', 20)
        kwargs.setdefault('pady', 10)
        
        super().__init__(parent, **kwargs)
        
        # Bind hover events
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
    
    def _on_enter(self, event):
        self.config(bg=self.bg_hover)
    
    def _on_leave(self, event):
        self.config(bg=self.bg_normal)

class StatusIndicator(tk.Frame):
    """Optimized status indicator with reduced animation"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#0f0f23', **kwargs)
        
        self.dot = tk.Label(
            self,
            text="●",
            font=('Segoe UI', 14),
            bg='#0f0f23',
            fg='#ff6b35'
        )
        self.dot.pack(side=tk.LEFT, padx=(0, 8))
        
        self.text = tk.Label(
            self,
            text="Initializing...",
            font=('Segoe UI', 11),
            bg='#0f0f23',
            fg='#e0e1dd'
        )
        self.text.pack(side=tk.LEFT)
        
        # Reduce animation frequency for better performance
        self._animation_counter = 0
        self.animate_connection()
    
    def animate_connection(self):
        """Reduced animation frequency"""
        self._animation_counter += 1
        
        # Only animate every 3rd call (every 3 seconds instead of every second)
        if self._animation_counter % 3 == 0:
            current_color = self.dot.cget('fg')
            if current_color == '#ff6b35':
                self.dot.config(fg='#415a77')
            else:
                self.dot.config(fg='#ff6b35')
        
        self.after(1000, self.animate_connection)
    
    def set_status(self, status: str, color: str):
        """Set status text and color"""
        self.text.config(text=status)
        self.dot.config(fg=color)

class IRacingRPMAlert:
    """
    Real-time RPM monitoring and shift point alert system for iRacing.
    
    Features:
    - Car-specific upshift RPM points with gear support
    - Real-time telemetry monitoring
    - Modern, responsive GUI design
    - Customizable alert sounds
    """
    
    VERSION = "1.0.2"
    
    # Modern color scheme
    COLORS = {
        'bg_primary': '#0f0f23',      # Dark navy background
        'bg_secondary': '#1b263b',     # Slightly lighter navy
        'bg_card': '#2d3142',          # Card background
        'accent_primary': '#ff6b35',   # Orange accent
        'accent_secondary': '#ffecd1', # Light cream
        'text_primary': '#e0e1dd',     # Light text
        'text_secondary': '#778da9',   # Muted text
        'success': '#06ffa5',          # Bright green
        'warning': '#ffb700',          # Amber
        'error': '#ff006e',            # Bright pink
        'info': '#8338ec'              # Purple
    }
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.setup_window()
        self.initialize_variables()
        self.load_car_database()
        self.create_modern_gui()
        self.setup_iracing_connection()
        self.start_monitoring()
        
        logging.info(f"iRacing RPM Alert v{self.VERSION} started")
    
    def setup_window(self) -> None:
        """Configure main window with performance optimizations"""
        self.root.title(f"iRacing RPM Alert v{self.VERSION}")
        self.root.geometry("600x700")
        self.root.configure(bg=self.COLORS['bg_primary'])
        self.root.resizable(True, True)
        self.root.minsize(500, 600)
        
        # Disable animation for better performance
        self.root.tk.call("tk", "scaling", 1.0)
        
        # Configure window icon
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # Configure modern ttk style
        self.setup_modern_styles()
    
    def setup_modern_styles(self):
        """Setup modern ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure modern treeview
        style.configure('Modern.Treeview',
                       background=self.COLORS['bg_card'],
                       foreground=self.COLORS['text_primary'],
                       fieldbackground=self.COLORS['bg_card'],
                       borderwidth=0,
                       relief='flat')
        
        style.configure('Modern.Treeview.Heading',
                       background=self.COLORS['bg_secondary'],
                       foreground=self.COLORS['text_primary'],
                       borderwidth=0,
                       relief='flat')
        
        # Configure modern scrollbar
        style.configure('Modern.Vertical.TScrollbar',
                       background=self.COLORS['bg_secondary'],
                       troughcolor=self.COLORS['bg_primary'],
                       borderwidth=0,
                       arrowcolor=self.COLORS['text_secondary'])
    
    def initialize_variables(self) -> None:
        """Initialize all class variables with optimized settings"""
        self.is_monitoring: bool = True
        self.current_rpm: int = 0
        self.current_gear: int = 0
        self.current_car: str = "Unknown"
        self.last_beep_time: float = 0
        self.beep_cooldown: float = 0.2
        self.last_upshift_beep_time: float = 0
        self.has_beeped_for_current_upshift: bool = False
        self.last_upshift_rpm: int = 0
        
        # Optimized settings for better performance
        self.settings = {
            "beep_frequency": 880,
            "beep_duration": 100,
            "update_interval": 50,  # Reduced back to 50ms for better accuracy
            "rpm_reset_threshold": 200,
            "rpm_tolerance": 50  # Add tolerance for shift point accuracy
        }
    
    def load_car_database(self) -> None:
        """Load car-specific RPM data from external file if available"""
        config_file = Path("car_config.json")
        
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    raw_data = json.load(f)
                
                # Convert string gear keys to integers
                self.car_upshift_rpm = {}
                for car_name, rpm_data in raw_data.items():
                    if isinstance(rpm_data, dict):
                        # Convert string keys to integers for gear-specific data
                        converted_data = {}
                        for gear_key, rpm_value in rpm_data.items():
                            try:
                                gear_int = int(gear_key)
                                converted_data[gear_int] = rpm_value
                            except ValueError:
                                logging.warning(f"Invalid gear key '{gear_key}' for car '{car_name}'")
                        self.car_upshift_rpm[car_name] = converted_data
                    else:
                        # Single RPM value, keep as is
                        self.car_upshift_rpm[car_name] = rpm_data
                
                logging.info("Loaded car configuration from file")
                
            else:
                self.car_upshift_rpm = {}
                logging.warning("No config file found. Car database is empty.")
                
        except Exception as e:
            logging.warning(f"Failed to load car config: {e}. Using empty database.")
            self.car_upshift_rpm = {}
    
    def save_car_database(self) -> None:
        """Save car database to JSON file"""
        try:
            config_file = Path("car_config.json")
            with open(config_file, 'w') as f:
                json.dump(self.car_upshift_rpm, f, indent=2)
            logging.info("Car database saved to file")
        except Exception as e:
            logging.error(f"Failed to save car config: {e}")
    
    def _clean_car_name(self, car_name: str) -> str:
        """Clean car name by removing safety car indicators and fixing incorrect names"""
        if not car_name:
            return car_name
        
        original_name = car_name
        clean_name = car_name.lower()
        
        # Remove safety car prefixes
        safety_prefixes = ["safety ", "pace ", "caution ", "yellow ", "fcv ", "sc "]
        
        for prefix in safety_prefixes:
            if clean_name.startswith(prefix):
                clean_name = clean_name[len(prefix):].strip()
                break
        
        # During safety car periods, iRacing sometimes shows wrong car names
        # If we see porsche but you're actually in Formula Vee, we need to ignore the wrong data
        # For now, just remove safety prefix and let the user manually identify their car
        
        # If the result looks like gibberish after removing safety prefix, 
        # return a generic name so user knows something is wrong
        if len(clean_name) < 3 or not any(c.isalpha() for c in clean_name):
            clean_name = "Unknown Car (Safety Period)"
        else:
            clean_name = clean_name.title()
        
        # Log the change
        if clean_name != original_name:
            #logging.info(f"Safety car period detected: '{original_name}' -> '{clean_name}'")
            pass
        
        return clean_name
    
    def create_modern_gui(self):
        """Create modern, responsive GUI"""
        # Main container with padding
        main_container = tk.Frame(self.root, bg=self.COLORS['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header section
        self.create_header(main_container)
        
        # Status section
        self.create_status_section(main_container)
        
        # Telemetry display section
        self.create_telemetry_section(main_container)
        
        # Controls section
        self.create_controls_section(main_container)
        
        # Info section
        self.create_info_section(main_container)
    
    def create_header(self, parent):
        """Create modern header with branding"""
        header_frame = tk.Frame(parent, bg=self.COLORS['bg_primary'])
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        # App title with gradient effect
        title = tk.Label(
            header_frame,
            text="🏎️ iRacing RPM Alert",
            font=('Segoe UI', 28, 'bold'),
            bg=self.COLORS['bg_primary'],
            fg=self.COLORS['accent_primary']
        )
        title.pack()
        
        # Version subtitle
        version = tk.Label(
            header_frame,
            text=f"Version {self.VERSION}",
            font=('Segoe UI', 11),
            bg=self.COLORS['bg_primary'],
            fg=self.COLORS['text_secondary']
        )
        version.pack(pady=(5, 0))
    
    def create_status_section(self, parent):
        """Create modern status indicator section"""
        status_card = tk.Frame(
            parent,
            bg=self.COLORS['bg_card'],
            relief='flat',
            bd=0
        )
        status_card.pack(fill=tk.X, pady=(0, 20))
        
        # Add subtle border effect
        border_frame = tk.Frame(status_card, bg=self.COLORS['accent_primary'], height=2)
        border_frame.pack(fill=tk.X)
        
        content_frame = tk.Frame(status_card, bg=self.COLORS['bg_card'])
        content_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # Status indicator
        self.status_indicator = StatusIndicator(content_frame)
        self.status_indicator.pack(side=tk.LEFT)
        
        # Car name on the right
        self.car_label = tk.Label(
            content_frame,
            text="No Car Detected",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['accent_secondary']
        )
        self.car_label.pack(side=tk.RIGHT)
    
    def create_telemetry_section(self, parent):
        """Create modern telemetry display section"""
        telemetry_frame = tk.Frame(parent, bg=self.COLORS['bg_primary'])
        telemetry_frame.pack(fill=tk.X, pady=(0, 20))
        
        # RPM Display Card
        rpm_card = tk.Frame(
            telemetry_frame,
            bg=self.COLORS['bg_card'],
            relief='flat',
            bd=0
        )
        rpm_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # RPM accent border
        rpm_border = tk.Frame(rpm_card, bg=self.COLORS['success'], height=3)
        rpm_border.pack(fill=tk.X)
        
        rpm_content = tk.Frame(rpm_card, bg=self.COLORS['bg_card'])
        rpm_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            rpm_content,
            text="Current RPM",
            font=('Segoe UI', 10),
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_secondary']
        ).pack()
        
        self.rpm_label = tk.Label(
            rpm_content,
            text="0",
            font=('Segoe UI', 42, 'bold'),
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['success']
        )
        self.rpm_label.pack(pady=(5, 0))
        
        # Gear Display Card
        gear_card = tk.Frame(
            telemetry_frame,
            bg=self.COLORS['bg_card'],
            relief='flat',
            bd=0
        )
        gear_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Gear accent border
        gear_border = tk.Frame(gear_card, bg=self.COLORS['info'], height=3)
        gear_border.pack(fill=tk.X)
        
        gear_content = tk.Frame(gear_card, bg=self.COLORS['bg_card'])
        gear_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            gear_content,
            text="Current Gear",
            font=('Segoe UI', 10),
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_secondary']
        ).pack()
        
        self.gear_label = tk.Label(
            gear_content,
            text="N",
            font=('Segoe UI', 32, 'bold'),
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['info']
        )
        self.gear_label.pack(pady=(5, 0))
    
    def create_controls_section(self, parent):
        """Create modern controls section"""
        controls_frame = tk.Frame(parent, bg=self.COLORS['bg_primary'])
        controls_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Primary action button
        self.start_button = ModernButton(
            controls_frame,
            text="🟢 MONITORING ACTIVE",
            command=self.toggle_monitoring,
            bg_normal=self.COLORS['success'],
            bg_hover='#04d98b',
            font=('Segoe UI', 14, 'bold'),
            pady=15
        )
        self.start_button.pack(fill=tk.X, pady=(0, 15))
        
        # Secondary buttons grid
        button_grid = tk.Frame(controls_frame, bg=self.COLORS['bg_primary'])
        button_grid.pack(fill=tk.X)
        
        # Configure grid weights
        button_grid.columnconfigure(0, weight=1)
        button_grid.columnconfigure(1, weight=1)
        button_grid.columnconfigure(2, weight=1)
        
        # Settings button
        settings_btn = ModernButton(
            button_grid,
            text="⚙️ Settings",
            command=self.open_settings_window,
            bg_normal=self.COLORS['accent_primary'],
            bg_hover='#ff8559',
            font=('Segoe UI', 11, 'bold')
        )
        settings_btn.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        
        # Reload button
        reload_btn = ModernButton(
            button_grid,
            text="🔄 Reload",
            command=self.reload_config,
            bg_normal=self.COLORS['info'],
            bg_hover='#9d4edd',
            font=('Segoe UI', 11, 'bold')
        )
        reload_btn.grid(row=0, column=1, sticky='ew', padx=5)
        
        # Help button
        help_btn = ModernButton(
            button_grid,
            text="❓ Help",
            command=self.show_help,
            bg_normal=self.COLORS['text_secondary'],
            bg_hover='#8d99ae',
            font=('Segoe UI', 11, 'bold')
        )
        help_btn.grid(row=0, column=2, sticky='ew', padx=(5, 0))
    
    def create_info_section(self, parent):
        """Create modern info section"""
        info_card = tk.Frame(
            parent,
            bg=self.COLORS['bg_card'],
            relief='flat',
            bd=0
        )
        info_card.pack(fill=tk.X)
        
        # Info accent border
        info_border = tk.Frame(info_card, bg=self.COLORS['warning'], height=2)
        info_border.pack(fill=tk.X)
        
        info_content = tk.Frame(info_card, bg=self.COLORS['bg_card'])
        info_content.pack(fill=tk.X, padx=20, pady=15)
        
        # Cars configured counter
        self.cars_label = tk.Label(
            info_content,
            text=f"Cars Configured: {len(self.car_upshift_rpm)}",
            font=('Segoe UI', 10),
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_secondary']
        )
        self.cars_label.pack(side=tk.LEFT)
        
        # Update interval indicator
        update_label = tk.Label(
            info_content,
            text=f"Update: {self.settings['update_interval']}ms",
            font=('Segoe UI', 10),
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_secondary']
        )
        update_label.pack(side=tk.RIGHT)
    
    def show_help(self):
        """Show modern help dialog"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Help & Information")
        help_window.geometry("500x400")
        help_window.configure(bg=self.COLORS['bg_primary'])
        help_window.transient(self.root)
        help_window.grab_set()
        
        # Help content
        help_text = """
🏎️ iRacing RPM Alert Help

FEATURES:
• Real-time RPM monitoring
• Car-specific upshift points
• Per-gear RPM configuration
• Audio alerts for optimal shifts

USAGE:
1. Start iRacing and join a session
2. The app will automatically detect your car
3. Configure upshift RPM in Settings
4. Listen for audio alerts at shift points

KEYBOARD SHORTCUTS:
• Space: Toggle monitoring
• F1: Open settings
• F5: Reload configuration

TROUBLESHOOTING:
• Ensure iRacing is running
• Check car_config.json for settings
• Verify audio system is working

VERSION: """ + self.VERSION + """
AUTHOR: Szymon Flis
        """
        
        text_widget = tk.Text(
            help_window,
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_primary'],
            font=('Segoe UI', 10),
            wrap=tk.WORD,
            padx=20,
            pady=20,
            relief='flat',
            bd=0
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        close_btn = ModernButton(
            help_window,
            text="Close",
            command=help_window.destroy,
            bg_normal=self.COLORS['text_secondary']
        )
        close_btn.pack(pady=20)
    
    def open_settings_window(self) -> None:
        """Open optimized settings window with proper sizing"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("RPM Configuration")
        settings_window.geometry("650x700")  # Increased height further
        settings_window.configure(bg=self.COLORS['bg_primary'])
        settings_window.resizable(True, True)  # Allow resize so user can adjust if needed
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Header
        header = tk.Frame(settings_window, bg=self.COLORS['bg_primary'])
        header.pack(fill=tk.X, padx=20, pady=(20, 0))
        
        title = tk.Label(
            header,
            text="⚙️ RPM Configuration",
            font=('Segoe UI', 18, 'bold'),
            bg=self.COLORS['bg_primary'],
            fg=self.COLORS['accent_primary']
        )
        title.pack()
        
        subtitle = tk.Label(
            header,
            text="Configure upshift RPM points for your cars",
            font=('Segoe UI', 10),
            bg=self.COLORS['bg_primary'],
            fg=self.COLORS['text_secondary']
        )
        subtitle.pack(pady=(5, 15))
        
        # Simplified main content without scrolling
        main_frame = tk.Frame(settings_window, bg=self.COLORS['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Add car section (simplified)
        self.create_simple_add_car_section(main_frame)
        
        # Existing cars section (simplified)
        self.create_simple_existing_cars_section(main_frame, settings_window)

    def create_simple_add_car_section(self, parent):
        """Create simplified add car section without complex styling"""
        add_frame = tk.LabelFrame(
            parent,
            text="Add New Car",
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_primary'],
            font=('Segoe UI', 11, 'bold'),
            relief='flat',
            bd=1
        )
        add_frame.pack(fill=tk.X, pady=(0, 15))
        
        content = tk.Frame(add_frame, bg=self.COLORS['bg_card'])
        content.pack(fill=tk.X, padx=15, pady=15)
        
        # Car name input
        tk.Label(
            content,
            text="Car Name:",
            font=('Segoe UI', 9),
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_secondary']
        ).grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        self.car_name_entry = tk.Entry(
            content,
            font=('Segoe UI', 10),
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['text_primary'],
            relief='flat',
            bd=1,
            width=30
        )
        self.car_name_entry.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        
        # RPM type selection (simplified)
        self.rpm_type_var = tk.StringVar(value="single")
        
        tk.Label(
            content,
            text="Configuration Type:",
            font=('Segoe UI', 9),
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_secondary']
        ).grid(row=2, column=0, sticky='w', pady=(0, 5))
        
        radio_frame = tk.Frame(content, bg=self.COLORS['bg_card'])
        radio_frame.grid(row=3, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
        tk.Radiobutton(
            radio_frame,
            text="Single RPM",
            variable=self.rpm_type_var,
            value="single",
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_primary'],
            font=('Segoe UI', 9),
            command=self.toggle_simple_rpm_inputs
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Radiobutton(
            radio_frame,
            text="Per-gear RPM",
            variable=self.rpm_type_var,
            value="gear",
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_primary'],
            font=('Segoe UI', 9),
            command=self.toggle_simple_rpm_inputs
        ).pack(side=tk.LEFT)
        
        # Single RPM input
        self.single_rpm_frame = tk.Frame(content, bg=self.COLORS['bg_card'])
        self.single_rpm_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        
        tk.Label(
            self.single_rpm_frame,
            text="Upshift RPM:",
            font=('Segoe UI', 9),
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_secondary']
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.single_rpm_entry = tk.Entry(
            self.single_rpm_frame,
            font=('Segoe UI', 10),
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['text_primary'],
            relief='flat',
            bd=1,
            width=10
        )
        self.single_rpm_entry.pack(side=tk.LEFT)
        
        # Gear RPM inputs (simplified grid)
        self.gear_rpm_frame = tk.Frame(content, bg=self.COLORS['bg_card'])
        
        gear_label = tk.Label(
            self.gear_rpm_frame,
            text="Gear RPM values:",
            font=('Segoe UI', 9),
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_secondary']
        )
        gear_label.grid(row=0, column=0, columnspan=6, sticky='w', pady=(0, 5))
        
        self.gear_entries = {}
        for i, gear in enumerate(range(1, 7)):
            tk.Label(
                self.gear_rpm_frame,
                text=f"G{gear}:",
                font=('Segoe UI', 8),
                bg=self.COLORS['bg_card'],
                fg=self.COLORS['text_secondary']
            ).grid(row=1, column=i*2, sticky='w', padx=(0, 2))
            
            entry = tk.Entry(
                self.gear_rpm_frame,
                font=('Segoe UI', 9),
                bg=self.COLORS['bg_secondary'],
                fg=self.COLORS['text_primary'],
                relief='flat',
                bd=1,
                width=6
            )
            entry.grid(row=2, column=i*2, padx=(0, 5), pady=(0, 5))
            self.gear_entries[gear] = entry
        
        # Initially hide gear inputs
        self.gear_rpm_frame.grid_remove()
        
        # Add button
        add_btn = tk.Button(
            content,
            text="Add Car",
            command=self.add_new_car,
            bg=self.COLORS['success'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            bd=0,
            padx=20,
            pady=5,
            cursor='hand2'
        )
        add_btn.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        content.columnconfigure(0, weight=1)

    def toggle_simple_rpm_inputs(self):
        """Toggle between single and gear RPM inputs (simplified)"""
        if self.rpm_type_var.get() == "single":
            self.gear_rpm_frame.grid_remove()
            self.single_rpm_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        else:
            self.single_rpm_frame.grid_remove()
            self.gear_rpm_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(0, 10))

    def create_simple_existing_cars_section(self, parent, settings_window):
        """Create simplified existing cars section"""
        existing_frame = tk.LabelFrame(
            parent,
            text=f"Configured Cars ({len(self.car_upshift_rpm)})",
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_primary'],
            font=('Segoe UI', 11, 'bold'),
            relief='flat',
            bd=1
        )
        existing_frame.pack(fill=tk.BOTH, expand=True)
        
        content = tk.Frame(existing_frame, bg=self.COLORS['bg_card'])
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Simple listbox instead of treeview for better performance
        list_frame = tk.Frame(content, bg=self.COLORS['bg_card'])
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))  # Added more bottom padding
        
        self.car_listbox = tk.Listbox(
            list_frame,
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['text_primary'],
            font=('Segoe UI', 9),
            relief='flat',
            bd=1,
            selectbackground=self.COLORS['accent_primary'],
            height=6  # Fixed smaller height
        )
        self.car_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.car_listbox.yview)
        self.car_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate listbox
        self.populate_simple_list()
        
        # Control buttons - use pack instead of fill=tk.X to prevent stretching
        button_frame = tk.Frame(content, bg=self.COLORS['bg_card'])
        button_frame.pack(anchor='s')  # Anchor to bottom, don't expand
        
        tk.Button(
            button_frame,
            text="Delete Selected",
            command=self.delete_selected_simple_car,
            bg=self.COLORS['error'],
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            relief='flat',
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            button_frame,
            text="Refresh",
            command=self.populate_simple_list,
            bg=self.COLORS['info'],
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            relief='flat',
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            button_frame,
            text="Close",
            command=settings_window.destroy,
            bg=self.COLORS['text_secondary'],
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            relief='flat',
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2'
        ).pack(side=tk.RIGHT)

    def populate_simple_list(self):
        """Populate simple listbox with existing cars"""
        self.car_listbox.delete(0, tk.END)
        for car_name, rpm_data in self.car_upshift_rpm.items():
            if isinstance(rpm_data, dict):
                rpm_text = f"{car_name} - Gears: {', '.join([f'{g}:{r}' for g, r in sorted(rpm_data.items())])}"
            else:
                rpm_text = f"{car_name} - All gears: {rpm_data} RPM"
            self.car_listbox.insert(tk.END, rpm_text)

    def delete_selected_simple_car(self):
        """Delete selected car from simple listbox"""
        selection = self.car_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select a car to delete")
            return
        
        selected_text = self.car_listbox.get(selection[0])
        car_name = selected_text.split(" - ")[0]  # Extract car name
        
        if messagebox.askyesno("Confirm Deletion", f"Delete configuration for '{car_name}'?"):
            del self.car_upshift_rpm[car_name]
            self.save_car_database()
            self.populate_simple_list()
            self.update_cars_count()
            logging.info(f"Deleted car configuration: {car_name}")

    def add_new_car(self):
        """Add new car with modern validation"""
        car_name = self.car_name_entry.get().strip()
        if not car_name:
            messagebox.showerror("Validation Error", "Please enter a car name")
            return
        
        if self.rpm_type_var.get() == "single":
            try:
                rpm = int(self.single_rpm_entry.get())
                if rpm < 1000:
                    raise ValueError("RPM too low")
                self.car_upshift_rpm[car_name] = rpm
            except ValueError:
                messagebox.showerror("Validation Error", "Please enter a valid RPM value (minimum 1000)")
                return
        else:
            gear_data = {}
            for gear, entry in self.gear_entries.items():
                rpm_text = entry.get().strip()
                if rpm_text:
                    try:
                        rpm = int(rpm_text)
                        if rpm < 1000:
                            raise ValueError(f"RPM too low for gear {gear}")
                        gear_data[gear] = rpm
                    except ValueError:
                        messagebox.showerror("Validation Error", f"Invalid RPM value for gear {gear}")
                        return
            
            if not gear_data:
                messagebox.showerror("Validation Error", "Please enter at least one gear RPM value")
                return
            
            self.car_upshift_rpm[car_name] = gear_data
        
        self.save_car_database()
        self.populate_simple_list()
        self.update_cars_count()
        
        # Clear form
        self.car_name_entry.delete(0, tk.END)
        self.single_rpm_entry.delete(0, tk.END)
        for entry in self.gear_entries.values():
            entry.delete(0, tk.END)
        
        messagebox.showinfo("Success", f"✅ Added car: {car_name}")
        logging.info(f"Added new car configuration: {car_name}")
    
    def update_cars_count(self):
        """Update cars count display"""
        self.cars_label.config(text=f"Cars Configured: {len(self.car_upshift_rpm)}")
    
    def reload_config(self) -> None:
        """Reload configuration from JSON file"""
        self.load_car_database()
        self.update_cars_count()
        logging.info("Configuration reloaded from file")
        
        # Update current car display if needed
        if self.current_car and self.current_car != "Unknown":
            # Use the clean car name for RPM lookup
            clean_car_name = self._clean_car_name(self.current_car)
            display_gear = self.current_gear if self.current_gear > 0 else 1
            upshift_rpm = self.get_upshift_rpm_for_car(clean_car_name, display_gear)
            self.car_label.config(text=f"{self.current_car} (↑{upshift_rpm})")
        
        messagebox.showinfo("Success", "✅ Configuration reloaded successfully!")
    
    def get_upshift_rpm_for_car(self, car_name: str, gear: int = 1) -> int:
        """Get the upshift RPM for a specific car and gear with improved matching"""
        effective_gear = max(1, gear)  # Use gear 1 for neutral/reverse
        
        # Clean the car name first
        clean_car_name = self._clean_car_name(car_name)
        
        # Only log if car or gear changed (reduce spam)
        cache_key = f"{clean_car_name}_{effective_gear}"
        if not hasattr(self, '_last_rpm_lookup') or self._last_rpm_lookup != cache_key:
            self._last_rpm_lookup = cache_key
            logging.debug(f"RPM lookup: '{clean_car_name}', gear: {effective_gear}")
        
        # Try exact match with cleaned name first
        if clean_car_name in self.car_upshift_rpm:
            rpm_data = self.car_upshift_rpm[clean_car_name]
            rpm = self._extract_rpm_from_data(rpm_data, effective_gear)
            return rpm
        
        # Try partial matching with cleaned name
        clean_car_lower = clean_car_name.lower()
        for known_car, rpm_data in self.car_upshift_rpm.items():
            if self._is_car_match(clean_car_lower, known_car.lower()):
                rpm = self._extract_rpm_from_data(rpm_data, effective_gear)
                # Only log the first time we find a match for this car
                if not hasattr(self, '_logged_matches'):
                    self._logged_matches = set()
                match_key = f"{clean_car_name}_{known_car}"
                if match_key not in self._logged_matches:
                    self._logged_matches.add(match_key)
                    logging.info(f"Matched '{clean_car_name}' with '{known_car}' -> {rpm} RPM")
                return rpm
        
        # Enhanced Porsche matching specifically
        if "porsche" in clean_car_lower and ("911" in clean_car_lower or "gt3" in clean_car_lower):
            for known_car, rpm_data in self.car_upshift_rpm.items():
                known_lower = known_car.lower()
                if ("porsche" in known_lower and "911" in known_lower) or \
                ("porsche" in known_lower and "gt3" in known_lower and "cup" in known_lower):
                    rpm = self._extract_rpm_from_data(rpm_data, effective_gear)
                    # Only log once per car match
                    if not hasattr(self, '_logged_porsche_matches'):
                        self._logged_porsche_matches = set()
                    match_key = f"{clean_car_name}_{known_car}"
                    if match_key not in self._logged_porsche_matches:
                        self._logged_porsche_matches.add(match_key)
                        logging.info(f"Porsche match: '{clean_car_name}' with '{known_car}' -> {rpm} RPM")
                    return rpm
        
        # Fallback to car type detection
        fallback_rpm = self._get_rpm_by_car_type(clean_car_lower)
        # Only log fallback once per car
        if not hasattr(self, '_logged_fallbacks'):
            self._logged_fallbacks = set()
        if clean_car_name not in self._logged_fallbacks:
            self._logged_fallbacks.add(clean_car_name)
            logging.warning(f"No match found for '{clean_car_name}', using fallback RPM: {fallback_rpm}")
        return fallback_rpm
    
    def _extract_rpm_from_data(self, rpm_data: Union[int, Dict[int, int]], gear: int) -> int:
        """Extract RPM value from car data"""
        if isinstance(rpm_data, dict):
            if gear in rpm_data:
                return rpm_data[gear]
            elif 1 in rpm_data:
                return rpm_data[1]
            else:
                return max(rpm_data.values())
        return rpm_data
    
    def _is_car_match(self, car_name: str, known_car: str) -> bool:
        """Check if car names match using improved fuzzy logic"""
        # Prevent SRX from matching with Porsche cars
        if "srx" in known_car.lower() and "porsche" in car_name.lower():
            return False
        if "porsche" in known_car.lower() and "srx" in car_name.lower():
            return False
        
        # Direct substring matching
        if known_car in car_name or car_name in known_car:
            return True
        
        # Enhanced specific pattern matching
        if self._check_enhanced_patterns(car_name, known_car):
            return True
        
        # Word-based matching for better accuracy
        car_words = set(car_name.replace('-', ' ').replace('_', ' ').split())
        known_words = set(known_car.replace('-', ' ').replace('_', ' ').split())
        
        # Require at least 2 matching words and no conflicting car types
        common_words = car_words & known_words
        if len(common_words) >= 2:
            # Check for conflicting car types
            car_types = {'srx', 'porsche', 'formula', 'gt3', 'cup'}
            car_car_types = car_words & car_types
            known_car_types = known_words & car_types
            
            # If both have car type indicators, they must match
            if car_car_types and known_car_types:
                return car_car_types == known_car_types
            
            return True
        
        return False
    
    def _check_enhanced_patterns(self, car_name: str, known_car: str) -> bool:
        """Enhanced pattern matching for specific cars"""
        # Porsche patterns
        porsche_patterns = [
            ("porsche", "911", "gt3", "cup"),
            ("porsche", "gt3", "cup"),
            ("911", "gt3", "cup"),
            ("porsche", "911"),
            ("porsche", "gt3")
        ]
        
        for pattern in porsche_patterns:
            if all(word in car_name for word in pattern) and all(word in known_car for word in pattern):
                return True
        
        # Formula patterns
        formula_patterns = [
            ("formula", "vee"),
            ("formula", "1"),
            ("formula", "2"),
            ("formula", "3")
        ]
        
        for pattern in formula_patterns:
            if all(word in car_name for word in pattern) and all(word in known_car for word in pattern):
                return True
        
        return False
    
    def _get_rpm_by_car_type(self, car_name: str) -> int:
        """Get RPM based on car type when exact match fails"""
        car_type_mapping = {
            ("formula", "vee"): 6400,
            ("porsche", "gt3"): 8200,
            ("gt3",): 7500,
            ("formula",): 7000
        }
        
        for keywords, rpm in car_type_mapping.items():
            if all(keyword in car_name for keyword in keywords):
                return rpm
        
        return 8200  # Default fallback
    
    def check_upshift_rpm_beep(self) -> None:
        """Check and handle upshift RPM alerts with improved accuracy"""
        current_time = time.time()
        upshift_rpm = self.get_upshift_rpm_for_car(self.current_car, self.current_gear)
        
        # Add tolerance to catch shift points more accurately
        tolerance = self.settings.get("rpm_tolerance", 50)
        
        if self._should_trigger_beep(upshift_rpm, current_time, tolerance):
            self._trigger_upshift_alert(upshift_rpm, current_time)
        elif self._should_reset_beep_flag(upshift_rpm):
            self.has_beeped_for_current_upshift = False

    def _should_trigger_beep(self, upshift_rpm: int, current_time: float, tolerance: int = 50) -> bool:
        """Determine if beep should be triggered with tolerance"""
        # Trigger when RPM is within tolerance of target (not just above)
        rpm_in_range = (upshift_rpm - tolerance) <= self.current_rpm <= (upshift_rpm + tolerance)
        
        return (rpm_in_range and
                not self.has_beeped_for_current_upshift and
                current_time - self.last_upshift_beep_time > self.beep_cooldown)

    def _should_reset_beep_flag(self, upshift_rpm: int) -> bool:
        """Determine if beep flag should be reset"""
        return (self.has_beeped_for_current_upshift and
                self.current_rpm < (upshift_rpm - self.settings["rpm_reset_threshold"]))

    def _trigger_upshift_alert(self, upshift_rpm: int, current_time: float) -> None:
        """Trigger the upshift alert with accuracy info"""
        try:
            winsound.Beep(self.settings["beep_frequency"], self.settings["beep_duration"])
            self.last_upshift_beep_time = current_time
            self.has_beeped_for_current_upshift = True
            self.last_upshift_rpm = upshift_rpm
            
            # Calculate how close we were to target
            difference = abs(self.current_rpm - upshift_rpm)
            logging.info(f"Upshift alert: {self.current_rpm} RPM (target: {upshift_rpm}, diff: ±{difference}, gear: {self.current_gear})")
        except Exception as e:
            logging.error(f"Failed to play alert sound: {e}")
    
    def setup_iracing_connection(self) -> None:
        """Initialize iRacing SDK connection"""
        try:
            self.ir = irsdk.IRSDK()
            logging.info("iRacing SDK initialized")
        except Exception as e:
            logging.error(f"Failed to initialize iRacing SDK: {e}")
            messagebox.showerror("Error", "Failed to initialize iRacing SDK")
    
    def start_monitoring(self) -> None:
        """Start the main monitoring loop"""
        self.update_loop()

    def update_loop(self):
        """Main update loop with session change detection"""
        try:
            if self.ir.startup():
                if self.ir.is_connected:
                    if self.status_indicator.text.cget('text') != "Connected":
                        self.status_indicator.set_status("Connected", self.COLORS['success'])
                    
                    # Check for session changes (this reliably detects car switches)
                    current_session_id = self.ir['SessionUniqueID']
                    if not hasattr(self, '_last_session_id'):
                        self._last_session_id = current_session_id
                        logging.info(f"Initial session ID: {current_session_id}")
                    elif current_session_id != self._last_session_id:
                        # Session changed - force car re-detection
                        logging.info(f"SESSION CHANGE: {self._last_session_id} -> {current_session_id}")
                        self._last_session_id = current_session_id
                        
                        # Force complete reset of car detection
                        self.current_car = "Unknown"
                        self.has_beeped_for_current_upshift = False
                        
                        # Clear all cached data
                        if hasattr(self, '_logged_safety_mappings'):
                            self._logged_safety_mappings.clear()
                        if hasattr(self, '_logged_cleanings'):
                            self._logged_cleanings.clear()
                        if hasattr(self, '_last_rpm_lookup'):
                            self._last_rpm_lookup = None
                        if hasattr(self, '_logged_matches'):
                            self._logged_matches.clear()
                        if hasattr(self, '_logged_porsche_matches'):
                            self._logged_porsche_matches.clear()
                        if hasattr(self, '_logged_fallbacks'):
                            self._logged_fallbacks.clear()
                        
                        # Show user feedback
                        self.car_label.config(text="Detecting car after session change...")
                        logging.info("Session change detected - re-detecting car")
                    
                    self.ir.freeze_var_buffer_latest()
                    
                    try:
                        rpm = self.ir['RPM']
                        gear = self.ir['Gear']
                        driver_info = self.ir['DriverInfo']
                        
                        # Get car data every update
                        raw_car_name = None
                        player_car_idx = self.ir['PlayerCarIdx']
                        
                        if driver_info and 'Drivers' in driver_info and player_car_idx is not None:
                            if player_car_idx < len(driver_info['Drivers']):
                                player_data = driver_info['Drivers'][player_car_idx]
                                raw_car_name = (player_data.get('CarScreenName') or 
                                            player_data.get('CarScreenNameShort') or 
                                            player_data.get('CarPath'))
                        
                        if not raw_car_name:
                            raw_car_name = "No Car Data"
                        
                        clean_car_name = self._clean_car_name(raw_car_name)
                        
                        # Update car if different OR if we're in "Unknown" state
                        if clean_car_name != self.current_car or self.current_car == "Unknown":
                            self.current_car = clean_car_name
                            display_gear = gear if gear and gear > 0 else 1
                            upshift_rpm = self.get_upshift_rpm_for_car(clean_car_name, display_gear)
                            self.car_label.config(text=f"{raw_car_name} (↑{upshift_rpm})")
                            self.has_beeped_for_current_upshift = False
                            logging.info(f"Car detected: '{clean_car_name}' [raw: '{raw_car_name}'] -> {upshift_rpm} RPM")
                        
                        # Rest of your existing RPM and gear code...
                        if rpm is not None:
                            new_rpm = int(rpm)
                            if abs(new_rpm - self.current_rpm) > 10:
                                self.current_rpm = new_rpm
                                self.rpm_label.config(text=f"{self.current_rpm:,}")
                                
                                current_color = self.rpm_label.cget('fg')
                                if self.current_rpm > 8000 and current_color != self.COLORS['error']:
                                    self.rpm_label.config(fg=self.COLORS['error'])
                                elif 6000 < self.current_rpm <= 8000 and current_color != self.COLORS['warning']:
                                    self.rpm_label.config(fg=self.COLORS['warning'])
                                elif self.current_rpm <= 6000 and current_color != self.COLORS['success']:
                                    self.rpm_label.config(fg=self.COLORS['success'])
                            
                            if self.is_monitoring:
                                self.check_upshift_rpm_beep()
                        
                        if gear is not None and gear != self.current_gear:
                            self.current_gear = gear
                            
                            if gear == -1:
                                self.gear_label.config(text="R")
                            elif gear == 0:
                                self.gear_label.config(text="N")
                            else:
                                self.gear_label.config(text=str(gear))
                            
                            if self.current_car and self.current_car != "Unknown":
                                display_gear = gear if gear > 0 else 1
                                upshift_rpm = self.get_upshift_rpm_for_car(self.current_car, display_gear)
                                current_display = self.car_label.cget('text')
                                if " (↑" in current_display:
                                    display_name = current_display.split(" (↑")[0]
                                    self.car_label.config(text=f"{display_name} (↑{upshift_rpm})")
                                self.has_beeped_for_current_upshift = False
                    
                    finally:
                        self.ir.unfreeze_var_buffer_latest()
                        
                else:
                    if self.status_indicator.text.cget('text') != "Waiting for session...":
                        self.status_indicator.set_status("Waiting for session...", self.COLORS['warning'])
                        self.current_rpm = 0
                        self.current_gear = 0
                        self.current_car = "No Session"
                        self.rpm_label.config(text="0", fg=self.COLORS['success'])
                        self.gear_label.config(text="N")
                        self.car_label.config(text="No Active Session")
                        
            else:
                if self.status_indicator.text.cget('text') != "Disconnected from iRacing":
                    self.status_indicator.set_status("Disconnected from iRacing", self.COLORS['error'])
                    self.current_rpm = 0
                    self.current_gear = 0
                    self.current_car = "Unknown"
                    self.rpm_label.config(text="0", fg=self.COLORS['success'])
                    self.gear_label.config(text="N")
                    self.car_label.config(text="iRacing Not Detected")
                
        except Exception as e:
            logging.error(f"Update loop error: {e}")
        
        self.root.after(self.settings["update_interval"], self.update_loop)

    def toggle_monitoring(self) -> None:
        """Toggle monitoring state with modern UI updates"""
        self.is_monitoring = not self.is_monitoring
        status = "ACTIVE" if self.is_monitoring else "PAUSED"
        logging.info(f"Monitoring {status}")
        
        if self.is_monitoring:
            self.start_button.config(text="🟢 MONITORING ACTIVE", bg=self.COLORS['success'])
            self.start_button.bg_normal = self.COLORS['success']
            self.start_button.bg_hover = '#04d98b'
        else:
            self.start_button.config(text="⏸️ MONITORING PAUSED", bg=self.COLORS['error'])
            self.start_button.bg_normal = self.COLORS['error']
            self.start_button.bg_hover = '#ff1a8c'

    def _on_slider_change(self, value):
        """Handle slider changes with debouncing"""
        if not hasattr(self, '_slider_update_job'):
            self._slider_update_job = None
        
        if self._slider_update_job:
            self.root.after_cancel(self._slider_update_job)
        
        self._slider_update_job = self.root.after(100, lambda: self._update_setting_from_slider(value))

    def _update_setting_from_slider(self, value):
        """Update setting after debounce delay"""
        pass
        
        # Schedule new update with 100ms delay
        self._slider_update_job = self.root.after(100, lambda: self._update_setting_from_slider(value))
        
    def create_settings_slider(self, parent, setting_name, min_val, max_val, current_val):
        """Create optimized slider with debouncing"""
        slider = tk.Scale(
            parent,
            from_=min_val,
            to=max_val,
            orient=tk.HORIZONTAL,
            command=lambda val: self._on_slider_change(val),
            resolution=1,
            length=200,
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_primary'],
            highlightthickness=0,
            troughcolor=self.COLORS['bg_secondary']
        )
        slider.set(current_val)
        return slider

    def on_closing(self) -> None:
        """Clean shutdown procedure"""
        try:
            logging.info("Shutting down iRacing RPM Alert")
            if hasattr(self, 'ir'):
                self.ir.shutdown()
            self.root.destroy()
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")

def main():
    """Main application entry point with performance optimizations"""
    try:
        root = tk.Tk()
        
        # Performance optimizations
        root.tk.call('tk', 'scaling', 1.0)  # Disable DPI scaling
        
        app = IRacingRPMAlert(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # Bind keyboard shortcuts
        root.bind('<KeyPress-space>', lambda e: app.toggle_monitoring())
        root.bind('<F1>', lambda e: app.open_settings_window())
        root.bind('<F5>', lambda e: app.reload_config())
        
        # Focus the window so keyboard shortcuts work
        root.focus_set()
        
        root.mainloop()
    except Exception as e:
        logging.critical(f"Critical error: {e}")
        messagebox.showerror("Critical Error", f"Application failed to start: {e}")

if __name__ == "__main__":
    main()