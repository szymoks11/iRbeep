#!/usr/bin/env python3
"""
iRacing RPM Alert - Version 1.0
A real-time RPM monitoring and shift point alert system for iRacing

Author: Szymon Flis
Version: 1.0.0
License: MIT
Repository: https://github.com/szymoks11/irbeep
"""

import irsdk
import tkinter as tk
from tkinter import ttk, messagebox
import winsound
import time
import json
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

class IRacingRPMAlert:
    """
    Real-time RPM monitoring and shift point alert system for iRacing.
    
    Features:
    - Car-specific upshift RPM points with gear support
    - Real-time telemetry monitoring
    - Safety car period detection
    - Customizable alert sounds
    - Professional GUI with status indicators
    """
    
    VERSION = "1.0.0"
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.setup_window()
        self.initialize_variables()
        self.load_car_database()
        self.create_widgets()
        self.setup_iracing_connection()
        self.start_monitoring()
        
        logging.info(f"iRacing RPM Alert v{self.VERSION} started")
    
    def setup_window(self) -> None:
        """Configure main window properties"""
        self.root.title(f"iRacing RPM Alert v{self.VERSION}")
        self.root.geometry("500x400")
        self.root.configure(bg='#1e1e1e')
        self.root.resizable(True, True)
        
        # Set window icon (if you have one)
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
    
    def initialize_variables(self) -> None:
        """Initialize all class variables with type hints"""
        self.is_monitoring: bool = True
        self.current_rpm: int = 0
        self.current_gear: int = 0
        self.current_car: str = "Unknown"
        self.last_beep_time: float = 0
        self.beep_cooldown: float = 0.2
        self.last_upshift_beep_time: float = 0
        self.has_beeped_for_current_upshift: bool = False
        self.last_upshift_rpm: int = 0
        
        # Settings
        self.settings = {
            "beep_frequency": 880,
            "beep_duration": 100,
            "update_interval": 50,
            "rpm_reset_threshold": 200
        }
    
    def load_car_database(self) -> None:
        """Load car-specific RPM data from external file if available"""
        config_file = Path("car_config.json")
        
        print(f"Looking for config file at: {config_file.absolute()}")
        print(f"Config file exists: {config_file.exists()}")
        
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
                                print(f"Warning: Invalid gear key '{gear_key}' for car '{car_name}'")
                        self.car_upshift_rpm[car_name] = converted_data
                    else:
                        # Single RPM value, keep as is
                        self.car_upshift_rpm[car_name] = rpm_data
                
                print(f"Loaded {len(self.car_upshift_rpm)} cars from config file")
                print(f"Porsche gear 1 RPM: {self.car_upshift_rpm.get('Porsche 911 GT3 Cup (992)', {}).get(1, 'Not found')}")
                logging.info("Loaded car configuration from file")
                
                # IMPORTANT: Return early to prevent any default database calls
                return
                
            else:
                print("Config file not found, creating default database")
                self.car_upshift_rpm = self.get_default_car_database()
                self.save_car_database()
                print(f"Created config file with {len(self.car_upshift_rpm)} cars")
        except Exception as e:
            print(f"Error loading config: {e}")
            logging.warning(f"Failed to load car config: {e}. Using defaults.")
            self.car_upshift_rpm = self.get_default_car_database()
    
    def save_car_database(self) -> None:
        """Save car database to JSON file - only called when creating new file"""
        try:
            config_file = Path("car_config.json")
            with open(config_file, 'w') as f:
                json.dump(self.car_upshift_rpm, f, indent=2)
            print(f"Saved config to: {config_file.absolute()}")
            print(f"File size: {config_file.stat().st_size} bytes")
            logging.info("Car database saved to file")
        except Exception as e:
            print(f"Error saving config: {e}")
            logging.error(f"Failed to save car config: {e}")
    
    def get_default_car_database(self) -> Dict[str, Union[int, Dict[int, int]]]:
        """Return default car RPM database"""
        print("WARNING: get_default_car_database() was called!")
        import traceback
        traceback.print_stack()  # This will show us WHERE it was called from
        
        return {
            "Porsche 911 GT3 Cup (992)": {
                1: 7800, 2: 8000, 3: 8100, 4: 8200, 5: 8200, 6: 8200
            },
            "BMW M4 GT3": 7200,
            "Ferrari 488 GT3 Evo 2020": 7800,
            "McLaren MP4-12C GT3": 7500,
            "Audi R8 LMS EVO": 7300,
            "Mercedes-AMG GT3 2020": 7000,
            "Lamborghini Huracán GT3 EVO": 8500,
            "Lexus RC F GT3": 7400,
            "Acura NSX GT3": 7600,
            "Ford Mustang FR500S": 6800,
            "Mazda MX-5 Cup": 7000,
            "Skip Barber Formula 2000": 6500,
            "Formula Vee": 6400,
            "Legends Ford '34 Coupe": 6000,
            "Street Stock": 6200,
            "Late Model Stock Car": 6800,
            "Super Late Model": 7200,
            "ARCA Menards Chevrolet Impala": 6500,
            "NASCAR Cup Series Chevrolet Camaro ZL1": {
                1: 8500, 2: 8600, 3: 8700, 4: 8800
            },
            "NASCAR Cup Series Ford Mustang": {
                1: 8500, 2: 8600, 3: 8700, 4: 8800
            },
            "NASCAR Cup Series Toyota Camry": {
                1: 8500, 2: 8600, 3: 8700, 4: 8800
            },
            "NASCAR Xfinity Series Chevrolet Camaro": 8500,
            "NASCAR Xfinity Series Ford Mustang": 8500,
            "NASCAR Xfinity Series Toyota Supra": 8500,
            "NASCAR Truck Series Chevrolet Silverado": 8200,
            "NASCAR Truck Series Ford F-150": 8200,
            "NASCAR Truck Series Toyota Tundra": 8200,
            "Dallara IR18": {
                1: 11500, 2: 11700, 3: 11800, 4: 11900, 5: 12000, 6: 12000
            },
            "Super Formula SF23": 11500,
            "Formula 3.5": 8500,
            "Pro Mazda": 7200,
            "Indy Pro 2000": 6800,
            "USF 2000": 6500,
            "Dirt Late Model": 6800,
            "Dirt Modified": 7500,
            "Dirt Sprint Car": 8200,
            "Dirt Midget": 7800,
            "World of Outlaws Sprint Car": 8500,
        }
    
    def create_widgets(self):
        """Create the user interface"""
        # Title
        title = tk.Label(
            self.root,
            text=f"iRacing RPM Alert v{self.VERSION}",
            font=("Arial", 20, "bold"),
            bg='#1e1e1e',
            fg='white'
        )
        title.pack(pady=15)
        
        # Connection status
        self.status_label = tk.Label(
            self.root,
            text="● Waiting for iRacing...",
            font=("Arial", 12),
            bg='#1e1e1e',
            fg='orange'
        )
        self.status_label.pack()
        
        # Car name display
        self.car_label = tk.Label(
            self.root,
            text="Unknown Car",
            font=("Arial", 14, "bold"),
            bg='#1e1e1e',
            fg='#ffaa00'
        )
        self.car_label.pack(pady=5)
        
        # Current RPM display
        rpm_frame = tk.Frame(self.root, bg='#1e1e1e')
        rpm_frame.pack(pady=20)
        
        self.rpm_label = tk.Label(
            rpm_frame,
            text="0",
            font=("Arial", 48, "bold"),
            bg='#1e1e1e',
            fg='#00ff00'
        )
        self.rpm_label.pack()
        
        tk.Label(
            rpm_frame,
            text="Current RPM",
            font=("Arial", 12),
            bg='#1e1e1e',
            fg='gray'
        ).pack()
        
        # Current Gear display
        gear_frame = tk.Frame(self.root, bg='#1e1e1e')
        gear_frame.pack(pady=10)
        
        self.gear_label = tk.Label(
            gear_frame,
            text="N",
            font=("Arial", 24, "bold"),
            bg='#1e1e1e',
            fg='#00aaff'
        )
        self.gear_label.pack()
        
        tk.Label(
            gear_frame,
            text="Current Gear",
            font=("Arial", 10),
            bg='#1e1e1e',
            fg='gray'
        ).pack()
        
        # Control buttons
        button_frame = tk.Frame(self.root, bg='#1e1e1e')
        button_frame.pack(pady=20)
        
        self.start_button = tk.Button(
            button_frame,
            text="Monitoring Active",
            command=self.toggle_monitoring,
            font=("Arial", 12, "bold"),
            bg='#00aa00',
            fg='white',
            padx=20,
            pady=10,
            relief='raised',
            cursor='hand2'
        )
        self.start_button.pack()
        
        # Add config reload button for easy testing
        reload_button = tk.Button(
            button_frame,
            text="Reload Config",
            command=self.reload_config,
            font=("Arial", 10),
            bg='#0066cc',
            fg='white',
            padx=15,
            pady=5,
            relief='raised',
            cursor='hand2'
        )
        reload_button.pack(pady=(10, 0))
    
    def reload_config(self) -> None:
        """Reload configuration from JSON file"""
        print("Manually reloading configuration...")
        self.load_car_database()
        logging.info("Configuration reloaded from file")
        
        # Update current car display if needed
        if self.current_car and self.current_car != "Unknown":
            base_car_name = self.current_car.replace(" (Safety Car Period)", "")
            display_gear = self.current_gear if self.current_gear > 0 else 1
            upshift_rpm = self.get_upshift_rpm_for_car(base_car_name, display_gear)
            self.car_label.config(text=f"{self.current_car} (Upshift: {upshift_rpm} RPM)")
            print(f"Updated display: {upshift_rpm} RPM for gear {display_gear}")
    
    def get_upshift_rpm_for_car(self, car_name: str, gear: int = 1) -> int:
        """Get the upshift RPM for a specific car and gear"""
        effective_gear = max(1, gear)  # Use gear 1 for neutral/reverse
        
        # Try exact match first
        if car_name in self.car_upshift_rpm:
            rpm_data = self.car_upshift_rpm[car_name]
            return self._extract_rpm_from_data(rpm_data, effective_gear)
        
        # Try partial matching
        car_name_lower = car_name.lower()
        for known_car, rpm_data in self.car_upshift_rpm.items():
            if self._is_car_match(car_name_lower, known_car.lower()):
                return self._extract_rpm_from_data(rpm_data, effective_gear)
        
        # Fallback to car type detection
        return self._get_rpm_by_car_type(car_name_lower)
    
    def _extract_rpm_from_data(self, rpm_data: Union[int, Dict[int, int]], gear: int) -> int:
        """Extract RPM value from car data"""
        if isinstance(rpm_data, dict):
            return rpm_data.get(gear, rpm_data.get(1, max(rpm_data.values())))
        return rpm_data
    
    def _is_car_match(self, car_name: str, known_car: str) -> bool:
        """Check if car names match using fuzzy logic"""
        return (known_car in car_name or car_name in known_car or
                self._check_specific_patterns(car_name))
    
    def _check_specific_patterns(self, car_name: str) -> bool:
        """Check for specific car pattern matches"""
        porsche_gt3_cup = ("porsche" in car_name and "gt3" in car_name and "cup" in car_name)
        porsche_911_gt3 = ("911" in car_name and "gt3" in car_name)
        return porsche_gt3_cup or porsche_911_gt3
    
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
        """Check and handle upshift RPM alerts"""
        current_time = time.time()
        upshift_rpm = self.get_upshift_rpm_for_car(self.current_car, self.current_gear)
        
        if self._should_trigger_beep(upshift_rpm, current_time):
            self._trigger_upshift_alert(upshift_rpm, current_time)
        elif self._should_reset_beep_flag(upshift_rpm):
            self.has_beeped_for_current_upshift = False
    
    def _should_trigger_beep(self, upshift_rpm: int, current_time: float) -> bool:
        """Determine if beep should be triggered"""
        return (self.current_rpm >= upshift_rpm and
                not self.has_beeped_for_current_upshift and
                current_time - self.last_upshift_beep_time > self.beep_cooldown)
    
    def _should_reset_beep_flag(self, upshift_rpm: int) -> bool:
        """Determine if beep flag should be reset"""
        return (self.has_beeped_for_current_upshift and
                self.current_rpm < (upshift_rpm - self.settings["rpm_reset_threshold"]))
    
    def _trigger_upshift_alert(self, upshift_rpm: int, current_time: float) -> None:
        """Trigger the upshift alert"""
        try:
            winsound.Beep(self.settings["beep_frequency"], self.settings["beep_duration"])
            self.last_upshift_beep_time = current_time
            self.has_beeped_for_current_upshift = True
            self.last_upshift_rpm = upshift_rpm
            
            logging.info(f"Upshift alert: {self.current_rpm} RPM (target: {upshift_rpm}, gear: {self.current_gear})")
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
        """Main update loop - called every 50ms"""
        try:
            # Try to connect/read from iRacing
            if self.ir.startup():
                # Check if we're actually connected and have data
                if self.ir.is_connected:
                    # Connected and have valid data!
                    if self.status_label['fg'] != '#00ff00':
                        self.status_label.config(text="● Connected", fg='#00ff00')
                    
                    # Read data from iRacing
                    self.ir.freeze_var_buffer_latest()
                    
                    try:
                        rpm = self.ir['RPM']
                        gear = self.ir['Gear']
                        
                        # Check if we're in the pits or safety car period
                        session_flags = self.ir['SessionFlags']
                        
                        # Try to get car name from session info
                        driver_info = self.ir['DriverInfo']
                        car_name = None
                        
                        if driver_info:
                            # Try different car name fields
                            if 'DriverCarScreenName' in driver_info:
                                car_name = driver_info['DriverCarScreenName']
                            elif 'Drivers' in driver_info and len(driver_info['Drivers']) > 0:
                                driver = driver_info['Drivers'][0]
                                car_name = driver.get('CarScreenName') or driver.get('CarScreenNameShort') or driver.get('CarPath', 'Unknown Car')
                        
                        # Check if safety car is active
                        safety_car_active = False
                        if session_flags is not None:
                            # Check for caution/yellow flags (safety car periods)
                            safety_car_active = (session_flags & 0x0008) or (session_flags & 0x4000)  # Yellow or Caution flags
                        
                        if not car_name:
                            car_name = "No Car Data"
                        elif safety_car_active:
                            car_name = f"{car_name} (Safety Car Period)"
                        
                        # Only print debug info if car changed
                        if car_name != self.current_car:
                            logging.info(f"Car detected: '{car_name}'")
                        
                        # Update car name if it changed
                        if car_name and car_name != self.current_car:
                            self.current_car = car_name
                            # Get base car name without safety car suffix for RPM lookup
                            base_car_name = car_name.replace(" (Safety Car Period)", "")
                            # Use gear 1 as default for initial display
                            display_gear = self.current_gear if self.current_gear > 0 else 1
                            upshift_rpm = self.get_upshift_rpm_for_car(base_car_name, display_gear)
                            self.car_label.config(text=f"{car_name} (Upshift: {upshift_rpm} RPM)")
                            logging.info(f"Upshift RPM set to: {upshift_rpm} for gear {display_gear}")
                        
                        if rpm is not None:
                            self.current_rpm = int(rpm)
                            self.rpm_label.config(text=str(self.current_rpm))
                            
                            # Only check for upshift beep if not in safety car period and monitoring is active
                            if not safety_car_active and self.is_monitoring:
                                self.check_upshift_rpm_beep()
                        
                        # Update gear display and recalculate upshift RPM if gear changed
                        if gear is not None and gear != self.current_gear:
                            self.current_gear = gear
                            
                            if gear == -1:
                                self.gear_label.config(text="R")
                            elif gear == 0:
                                self.gear_label.config(text="N")
                            else:
                                self.gear_label.config(text=str(gear))
                            
                            # Update upshift RPM display when gear changes
                            if self.current_car and not safety_car_active:
                                base_car_name = self.current_car.replace(" (Safety Car Period)", "")
                                display_gear = gear if gear > 0 else 1
                                upshift_rpm = self.get_upshift_rpm_for_car(base_car_name, display_gear)
                                self.car_label.config(text=f"{self.current_car} (Upshift: {upshift_rpm} RPM)")
                                
                                # Reset beep flag when gear changes
                                self.has_beeped_for_current_upshift = False
                    
                    finally:
                        self.ir.unfreeze_var_buffer_latest()
                        
                else:
                    # Connected to iRacing but no session data
                    if self.status_label['fg'] != 'orange':
                        self.status_label.config(text="● Waiting for session...", fg='orange')
                        self.current_rpm = 0
                        self.current_gear = 0
                        self.current_car = "No Session"
                        self.rpm_label.config(text="0")
                        self.gear_label.config(text="N")
                        self.car_label.config(text="No Session")
                        
            else:
                # Not connected to iRacing at all
                if self.status_label['fg'] != 'red':
                    self.status_label.config(text="● Disconnected", fg='red')
                    self.current_rpm = 0
                    self.current_gear = 0
                    self.current_car = "Unknown"
                    self.rpm_label.config(text="0")
                    self.gear_label.config(text="N")
                    self.car_label.config(text="Unknown Car")
                
        except Exception as e:
            logging.error(f"Update loop error: {e}")
        
        # Schedule next update
        self.root.after(self.settings["update_interval"], self.update_loop)
    
    def toggle_monitoring(self) -> None:
        """Toggle monitoring state"""
        self.is_monitoring = not self.is_monitoring
        status = "ACTIVE" if self.is_monitoring else "PAUSED"
        logging.info(f"Monitoring {status}")
        
        # Update UI to reflect state
        if self.is_monitoring:
            self.start_button.config(text="Monitoring Active", bg='#00aa00')
        else:
            self.start_button.config(text="Monitoring Paused", bg='#aa0000')
    
    def on_closing(self) -> None:
        """Clean shutdown procedure - preserves manual config edits"""
        try:
            logging.info("Shutting down iRacing RPM Alert")
            if hasattr(self, 'ir'):
                self.ir.shutdown()
            # Don't auto-save on shutdown to preserve manual JSON edits
            self.root.destroy()
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")

def main():
    """Main application entry point"""
    try:
        root = tk.Tk()
        app = IRacingRPMAlert(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Critical error: {e}")
        messagebox.showerror("Critical Error", f"Application failed to start: {e}")

if __name__ == "__main__":
    main()