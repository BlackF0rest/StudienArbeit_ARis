# IMPORTS
# weather data
import requests, json
API_KEY = 'ab04d8ae1dafd3623b42adeabf9c08be'
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather?'
from geopy.geocoders import Nominatim

# GENERAL FUNCTIONS 

def debug_print(text:str):
    print("\033[92m" + text + "\033[0m")


# FUNCTIONS

class DataHandler():

    def __init__(self):
        pass

    def get_weather_data(self):
        current_city = 'Stuttgart'
        geolocator = Nominatim(user_agent="MyApp")
        location = geolocator.geocode(current_city)
        debug_print(f"Location: {location}")
        complete_url = BASE_URL + "lat=" + str(location.latitude) + "&lon=" + str(location.longitude) + "&appid=" + API_KEY 
        debug_print(f"Complete URL: {complete_url}")
        response = requests.get(complete_url)
        x = response.json()
        debug_print(f"Response: {x}")
        if x["cod"] != "404":
            y = x["main"]
            current_temperature = y["temp"]
            current_pressure = y["pressure"]
            current_humidity = y["humidity"]
            z = x["weather"]
            weather_description = z[0]["description"]
            debug_print(f"Temperature: {current_temperature}")
            debug_print(f"Pressure: {current_pressure}")
            debug_print(f"Humidity: {current_humidity}")
            debug_print(f"Weather description: {weather_description}")
        else:
            debug_print("City Not Found")

        weather_data = {
            "city": current_city,
            "temperature": current_temperature,
            "pressure": current_pressure,
            "humidity": current_humidity,
            "description": weather_description
        }

        return weather_data


    


DataHandler = DataHandler()
DataHandler.get_weather_data()
# END OF FILE