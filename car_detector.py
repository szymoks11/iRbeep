#!/usr/bin/env python3
"""
iRacing Car Detection Module
Quick car detection that exits immediately with result

Author: Szymon Flis
"""

import irsdk
import json
import time
import sys

def get_current_car():
    """Get current car and exit immediately"""
    ir = irsdk.IRSDK()
    
    try:
        # Quick connection
        if not ir.startup():
            return {"error": "Failed to connect to iRacing SDK", "success": False}
        
        if not ir.is_connected:
            return {"error": "iRacing not running or no session active", "success": False}
        
        # Get car data quickly
        ir.freeze_var_buffer_latest()
        
        try:
            # Get basic data with proper error handling
            try:
                player_idx = ir['PlayerCarIdx']
            except:
                player_idx = None
            
            try:
                session_id = ir['SessionUniqueID']
            except:
                session_id = None
            
            result = {
                "timestamp": time.time(),
                "player_idx": player_idx,
                "session_id": session_id,
                "direct_car_name": None,
                "direct_car_path": None,
                "driver_car_name": None,
                "driver_car_path": None,
                "success": True
            }
            
            # Try direct car data first
            try:
                result["direct_car_name"] = ir['CarScreenName']
            except:
                result["direct_car_name"] = None
            
            try:
                result["direct_car_path"] = ir['CarPath']
            except:
                result["direct_car_path"] = None
            
            # Try driver info as backup
            try:
                driver_info = ir['DriverInfo']
                if driver_info and 'Drivers' in driver_info and player_idx is not None:
                    if player_idx < len(driver_info['Drivers']):
                        player_data = driver_info['Drivers'][player_idx]
                        result["driver_car_name"] = player_data.get('CarScreenName')
                        result["driver_car_path"] = player_data.get('CarPath')
            except:
                result["driver_car_name"] = None
                result["driver_car_path"] = None
            
            # Determine best car name (prefer direct, fallback to driver)
            best_car = (result["direct_car_name"] or 
                       result["driver_car_name"] or 
                       "No Car Data")
            
            result["best_car_name"] = best_car
            
            # Add some debug info
            result["detection_method"] = "direct" if result["direct_car_name"] else "driver" if result["driver_car_name"] else "none"
            
            return result
            
        finally:
            ir.unfreeze_var_buffer_latest()
            
    except Exception as e:
        return {"error": str(e), "success": False, "timestamp": time.time()}
    finally:
        try:
            ir.shutdown()
        except:
            pass

def main():
    """Main function for testing"""
    result = get_current_car()
    
    if result.get("success"):
        print(f"✅ Car Detection Success:")
        print(f"   Best Car: {result['best_car_name']}")
        print(f"   Direct Car: {result['direct_car_name']}")
        print(f"   Driver Car: {result['driver_car_name']}")
        print(f"   Session ID: {result['session_id']}")
        print(f"   Player Index: {result['player_idx']}")
        print(f"   Detection Method: {result['detection_method']}")
    else:
        print(f"❌ Car Detection Failed: {result['error']}")

if __name__ == "__main__":
    # If run directly, show human-readable output
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        # JSON output for app.py
        result = get_current_car()
        print(json.dumps(result))
    else:
        # Human-readable output for testing
        main()