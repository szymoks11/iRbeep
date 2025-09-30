# iRacing RPM Alert

A professional real-time RPM monitoring and shift point alert system for iRacing simulators. This desktop application provides intelligent audio alerts based on car-specific optimal shift points extracted from official iRacing PDF manuals.

## 🏁 Features

- **Real-Time Telemetry**: Live RPM and gear monitoring via iRacing SDK
- **35+ Car Database**: Optimal shift points from official iRacing manuals
- **Intelligent Alerts**: Single beep per upshift with automatic reset
- **Safety Integration**: Automatic alert suspension during caution periods
- **Professional GUI**: Modern dark-themed interface with live data display
- **Hot-Reload Config**: Modify shift points without restarting the application
- **Gear-Specific RPMs**: Advanced cars support different RPMs per gear

## 🚗 Supported Cars

The application includes optimal shift points for 35+ cars across all major categories:

- **Formula Cars**: F1, IndyCar, Super Formula, Formula Vee, F4
- **GT3/GT4**: BMW M4, Ferrari 488, Mercedes-AMG, Porsche 911, McLaren
- **Prototypes**: Dallara iR-01, Ligier JS P320  
- **NASCAR**: NextGen Cup Series (all manufacturers)
- **Sports Cars**: Mazda MX-5, Toyota GR86, Porsche Cayman

## 🛠️ Technical Stack

- **Python 3.8+** with type hints and professional error handling
- **iRacing SDK** for real-time telemetry integration
- **Tkinter** for modern desktop GUI
- **JSON Configuration** for easy customization
- **Comprehensive Logging** system

## 📖 Installation & Usage

```bash
# Clone the repository
git clone https://github.com/szymoks11/irbeep.git
cd irbeep

# Install dependencies
pip install pyirsdk

# Run the application
python app.py
