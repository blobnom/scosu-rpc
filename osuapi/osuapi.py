from typing import Literal
import requests

from .classes.User import SearchedUser
from .classes.User import UserFull

class OsuApi:
	base_url: str = "https://api.scosu.oritsu.net/v1"
	
	def api(self, endpoint: str) -> dict:
		req = requests.get(self.base_url + endpoint)
		return req.json()

	def search_user(self, name: str) -> SearchedUser:
		data = self.api(f"/search_players?q={name}")
		if data["status"] != "success":
			return None
		
		return SearchedUser(data["result"][0])
	
	def get_user(self, id: int, mode: int) -> UserFull:
		data = self.api(f"/get_player_info?id={id}&scope=all")
		if data["status"] != "success":
			return None
		
		tmp = {
			"info": data["player"]["info"],
			"stats": data["player"]["stats"][str(mode)]
		}

		return UserFull(tmp)